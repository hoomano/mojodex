import time

from app import db, main_logger, server_socket, executor
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *

class SocketioMessageSender:
    def __init__(self):
        self.mojo_messages_waiting_for_acknowledgment, self.produced_text_messages_waiting_for_acknowledgment = {}, {}

    def _mojo_message_received(self, data, *args):
        if "backend_event_manager" in data and data["backend_event_manager"]:
            # any backend event manager receiving a message should not prevent the message to be re-sent to the user while they have not acknowledged it
            return
        session_id = data["session_id"]

        session_db = db.session.query(MdSession).filter(MdSession.session_id == session_id).first()
        if session_db is None:
            main_logger.error(f"Session {session_id} not found in db", None)
            return

        from models.assistant.session import Session as SessionModel
        session = SessionModel(session_id)
        if "message_pk" in data and data["message_pk"]:
            message_pk = int(data["message_pk"])
            if message_pk in self.mojo_messages_waiting_for_acknowledgment:
                del self.mojo_messages_waiting_for_acknowledgment[message_pk]
                session.set_mojo_message_read_by_user(message_pk=message_pk)
        elif "produced_text_version_pk" in data and data["produced_text_version_pk"]:
            produced_text_version_pk = int(data["produced_text_version_pk"])
            if produced_text_version_pk in self.produced_text_messages_waiting_for_acknowledgment:
                del self.produced_text_messages_waiting_for_acknowledgment[produced_text_version_pk]
                session.set_produced_text_version_read_by_user(produced_text_version_pk=produced_text_version_pk)

        return session

    def send_mojo_message_with_ack(self, message, session_id, event_name='mojo_message', remaining_tries=120):
        # max_tries = every 5s for 10 minutes
        if "produced_text_version_pk" in message:
            self.produced_text_messages_waiting_for_acknowledgment[message["produced_text_version_pk"]] = message
        elif "message_pk" in message:
            self.mojo_messages_waiting_for_acknowledgment[message["message_pk"]] = message
        if "session_id" not in message:
            message["session_id"] = session_id
        server_socket.emit(event_name, message, to=session_id, callback=self._mojo_message_received)

        def waiting_for_acknowledgment():
            # sleep 5 seconds
            time.sleep(5)
            # if the message is still not None, resend it
            if "message_pk" in message and message["message_pk"] in self.mojo_messages_waiting_for_acknowledgment:
                self.send_mojo_message_with_ack(self.mojo_messages_waiting_for_acknowledgment[message["message_pk"]], session_id,
                                           event_name=event_name, remaining_tries=remaining_tries - 1)
            elif "produced_text_version_pk" in message and message[
                "produced_text_version_pk"] in self.produced_text_messages_waiting_for_acknowledgment:
                self.send_mojo_message_with_ack(
                    self.produced_text_messages_waiting_for_acknowledgment[message["produced_text_version_pk"]], session_id,
                    event_name=event_name, remaining_tries=remaining_tries - 1)

        # start a timer of 5 seconds, in 5 seconds if it has not been killed, it will resend the message. Use executor
        if remaining_tries > 0:
            executor.submit(waiting_for_acknowledgment)

    def send_error(self, error, session_id, **kwargs):
        """
        Send error to the user and log it in console + db
        :param error: Error to send and log
        :param session_id: Session id in which the error occurred
        :return:
        """
        try:
            message = {"error": error, "session_id": session_id, **kwargs}
            server_socket.emit('error', message, to=session_id)
            log_error(message, session_id=session_id)
            return message
        except Exception as e:
            main_logger.error(f"Error while sending error to user: {e}", None)