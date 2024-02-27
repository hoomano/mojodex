import os
import requests
from app import db, log_error, server_socket, executor, time_manager, socketio_message_sender, main_logger
from mojodex_core.entities import *
from datetime import datetime
from models.voice_generator import VoiceGenerator
from models.task_classifier import TaskClassifier
from models.default_chit_chat import DefaultChitChat
from models.tasks.task_manager import TaskManager
from packaging import version

from models.home_chat.home_chat_manager import HomeChatManager


class Session:
    logger_prefix = "Session"
    sessions_storage = "/data/users"
    agent_message_key, user_message_key = "mojo", "user"

    def __init__(self, session_id):
        """
        A session is a full interaction between the user and Mojo
        :param user_id: id of the user
        :param session_id: id of the session
        :param input: input of the user to start the session
        """
        self.id = session_id
        user = self._get_user()
        self.user_id = user.user_id
        if 'SPEECH_KEY' in os.environ and 'SPEECH_REGION' in os.environ:
            try:
                self.voice_generator = VoiceGenerator() if self.__get_platform() == "mobile" else None
            except Exception as e:
                self.voice_generator = None
                main_logger.error(f"{Session.logger_prefix}:: Can't initialize voice generator")
        else:
            self.voice_generator = None



    def __get_mojo_messages_audio_storage(self):
        try:
            user_storage = os.path.join(Session.sessions_storage, self.user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage, exist_ok=True)
            session_storage = os.path.join(user_storage, self.id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage, exist_ok=True)
            mojo_messages_audio_storage = os.path.join(session_storage, "mojo_messages_audios")
            if not os.path.exists(mojo_messages_audio_storage):
                os.makedirs(mojo_messages_audio_storage, exist_ok=True)
            return mojo_messages_audio_storage
        except Exception as e:
            raise Exception(f"__get_mojo_messages_audio_storage :: {e}")


    def _get_user(self):
        return db.session.query(MdUser).join(MdSession, MdSession.user_id == MdUser.user_id).filter(
            MdSession.session_id == self.id).first()

    def _get_session_db(self):
        return db.session.query(MdSession).filter(MdSession.session_id == self.id).first()

    def _get_all_session_messages(self):
        # get all of session
        return db.session.query(MdMessage) \
            .filter(MdMessage.session_id == self.id) \
            .order_by(MdMessage.message_date) \
            .all()

    def _get_conversation(self, user_key="User", agent_key="Agent"):
        try:
            messages = self._get_all_session_messages()
            conversation = ""
            for message in messages:
                if message.sender == Session.user_message_key:
                    if "text" in message.message:
                        conversation += f"{user_key}: {message.message['text']}\n"
                elif message.sender == Session.agent_message_key:
                    if "text" in message.message:
                        conversation += f"{agent_key}: {message.message['text']}\n"
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("Error during _get_conversation: " + str(e))

    def _get_number_of_messages(self):
        return db.session.query(MdMessage).filter(MdMessage.session_id == self.id).count()

    def __get_last_user_message(self):
        try:
            last_user_message_pk = db.session.query(MdMessage.message_pk) \
                .filter(MdMessage.session_id == self.id) \
                .filter(MdMessage.sender == 'user') \
                .order_by(MdMessage.message_date.desc()).first()
            if last_user_message_pk is None:
                return None
            return last_user_message_pk[0] if last_user_message_pk else None
        except Exception as e:
            raise Exception(f"__get_last_user_message :: {e}")

    def __get_platform(self):
        return db.session.query(MdSession.platform) \
            .filter(MdSession.session_id == self.id) \
            .first()[0]

    def _get_language(self):
        session_language = db.session.query(MdSession.language) \
            .filter(MdSession.session_id == self.id) \
            .first()
        return session_language[0] if session_language else None

    def _mojo_token_callback(self, partial_text):
        try:
            server_socket.emit('mojo_token', {"text": partial_text, 'session_id': self.id}, to=self.id)
        except Exception as e:
            raise Exception(f"_mojo_token_callback :: {e}")


    def set_produced_text_version_read_by_user(self, produced_text_version_pk):
        produced_text_version = db.session.query(MdProducedTextVersion).filter(
            MdProducedTextVersion.produced_text_version_pk == produced_text_version_pk).first()
        produced_text_version.read_by_user = datetime.now()
        db.session.commit()

    def set_mojo_message_read_by_user(self, message_pk):
        try:
            mojo_message = db.session.query(MdMessage).filter(MdMessage.message_pk == message_pk).first()
            mojo_message.read_by_user = datetime.now()
            # check if there is a produced_text_version_pk in the message
            if "produced_text_version_pk" in mojo_message.message:
                produced_text_version_pk = mojo_message.message["produced_text_version_pk"]
                self.set_produced_text_version_read_by_user(produced_text_version_pk)
            db.session.commit()
        except Exception as e:
            log_error("Error during set_mojo_message_read_by_user: " + str(e))

    def _find_task_for_user_task_execution_pk(self, user_task_execution_pk):
        return db.session.query(MdTask, MdUserTaskExecution) \
            .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
            .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
            .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
            .first()

    def _generate_session_title(self, sender, message):
        # call background backend /end_user_task_execution to update generate session title and summary
        uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/first_session_message"
        pload = {'datetime': datetime.now().isoformat(),
                 'session_id': self.id,
                 'sender': sender,
                 'message': message["text"]}
        internal_request = requests.post(uri, json=pload)
        if internal_request.status_code != 200:
            log_error(
                f"Error while calling background first_session_message : {internal_request.json()}")

    def receive_human_message(self, event_name, message):
        try:
            app_version = version.parse(message["version"]) if "version" in message else version.parse("0.0.0")
            if self._get_number_of_messages() == 0 and self._get_session_db().starting_mode == 'chat':
                sender = "user"
                executor.submit(self._generate_session_title, sender, message)

            if event_name == "user_message":
                if "message_pk" not in message:
                    self._new_message(message, Session.user_message_key, event_name)

            # Home chat session here ??
            # with response_message = ...
            if "origin" in message and message["origin"] == "home_chat":
                response_event_name, response_message, response_language = self.__manage_home_chat_session(message, app_version)
            elif 'user_task_execution_pk' in message:
                # For now only task sessions
                response_event_name, response_message, response_language = self.__manage_task_session(message, app_version)
            else:
                raise Exception("Unknown message origin")

            if response_message:
                if "session_id" not in response_message:
                    response_message["session_id"] = self.id
                db_message = self._new_message(response_message, Session.agent_message_key, response_event_name)
                message_pk = db_message.message_pk
                response_message["message_pk"] = message_pk
                response_message["audio"] = "text" in response_message and self.__get_platform() == "mobile" and self.voice_generator is not None
                if response_event_name == 'mojo_message':
                    socketio_message_sender.send_mojo_message_with_ack(response_message, self.id)
                else:
                    server_socket.emit(response_event_name, response_message, to=self.id)
                if response_message["audio"]:
                    output_filename = os.path.join(self.__get_mojo_messages_audio_storage(), f"{message_pk}.mp3")
                    try:
                        self.voice_generator.text_to_speech(response_message["text"], response_language, self.user_id, output_filename)
                    except Exception as e:
                        db_message.in_error_state = datetime.now()
                        log_error(str(e), session_id=self.id)

            db.session.close()
        except Exception as e:
            db.session.rollback()
            message = socketio_message_sender.send_error("Error during session new_receive_human_message: " + str(e), self.id, user_message_pk=self.__get_last_user_message())
            self._new_message(message, Session.agent_message_key, 'error')
            db.session.close()

    def __manage_home_chat_session(self, message, app_version):
        try:
            home_chat_manager = HomeChatManager(session_id=self.id, user=self._get_user(), platform=self.__get_platform(), app_version=app_version,
                                                 voice_generator=self.voice_generator, mojo_messages_audio_storage=self.__get_mojo_messages_audio_storage(), mojo_token_callback=self._mojo_token_callback)
            response_event_name, response_message, response_language = home_chat_manager.response_to_user_message(user_message=message)
            return response_event_name, response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_home_chat_session :: {e}")

    def __manage_task_session(self, message, app_version):
        try:
            running_task, user_task_execution = self._find_task_for_user_task_execution_pk(
                    message["user_task_execution_pk"])
            task_manager = TaskManager(self._get_user(), self.id, self.__get_platform(), app_version, self.voice_generator, self.__get_mojo_messages_audio_storage(),  mojo_token_callback=self._mojo_token_callback)
            task_manager.set_task_and_execution(running_task, user_task_execution)
            tag_proper_nouns = self.__get_platform() == "mobile"
            response_event_name, response_message, response_language = task_manager.response_to_user_message(user_message=message, tag_proper_nouns=tag_proper_nouns)

            return response_event_name, response_message, response_language
        except Exception as e:
            raise Exception(f"__manage_task_session :: {e}")


    def _new_message(self, message, sender, event_name):
        """
        Save message in DB
        :param message: Message to save
        :param sender: Who sent the message
        :return:
        """
        try:
            if sender == Session.user_message_key:
                message_date = message["message_date"]
                timezone_offset = int(message["timezone_offset"])
                message_date = time_manager.device_date_to_backend_date(message_date, timezone_offset)
            else:
                message_date = datetime.now()
            message = MdMessage(session_id=self.id, sender=sender, event_name=event_name, message=message,
                                creation_date=datetime.now(), message_date=message_date)
            db.session.add(message)
            db.session.commit()
            return message
        except Exception as e:
            db.session.rollback()
            raise Exception(f"new_message : {e}")

