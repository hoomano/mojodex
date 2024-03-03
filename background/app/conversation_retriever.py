from app import db
from background_logger import BackgroundLogger
from mojodex_core.entities import MdMessage


class ConversationRetriever:
    logger_prefix = "ConversationRetriever::"

    def __init__(self):
        self.logger = BackgroundLogger(ConversationRetriever.logger_prefix)

    def _get_all_session_messages(self, session_id):
        return db.session.query(MdMessage) \
            .filter(MdMessage.session_id == session_id) \
            .order_by(MdMessage.message_date) \
            .all()

    def get_conversation_as_string(self, session_id, agent_key="Agent", user_key="User", with_tags=True):
        try:
            messages = self._get_all_session_messages(session_id)
            conversation = ""
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation += f"{user_key}: {message.message['text']}\n"
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message and with_tags:
                            conversation += f"{agent_key}: {message.message['text_with_tags']}\n"
                        else:
                            conversation += f"{agent_key}: {message.message['text']}\n"
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("_get_conversation_as_string: " + str(e))

    def _get_user_messages_as_conversation(self, session_id, user_key="User"):
        try:
            messages = self._get_all_session_messages(session_id)
            conversation = ""
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation += f"{user_key}: {message.message['text']}\n"
            return conversation
        except Exception as e:
            raise Exception("_get_conversation_as_string: " + str(e))


    def get_conversation_as_list(self, session_id, agent_key="assistant", user_key="user", with_tags=True):
        try:
            messages = self._get_all_session_messages(session_id)
            conversation = []
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation.append({"role": user_key, "content": message.message['text']})
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message and with_tags:
                            conversation.append({"role": agent_key, "content": message.message['text_with_tags']})
                        else:
                            conversation.append({"role": agent_key, "content": message.message['text']})
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("get_conversation_as_list: " + str(e))