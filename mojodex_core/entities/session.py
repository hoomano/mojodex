from sqlalchemy.orm import object_session
from models.assistant.models.message import Message
from mojodex_core.entities.db_base_entities import MdSession

class Session(MdSession):

    @property
    def messages(self):
        try:
            session = object_session(self)
            return session.query(Message).filter(Message.session_id == self.session_id).order_by(Message.message_date).all()
        except Exception as e:
            raise Exception("_db_messages: " + str(e))

    @property
    def last_user_message(self):
        try:
            from models.assistant.session import Session as SessionModel
            last_user_message = next((message for message in self.messages[::-1] if message.sender == SessionModel.user_message_key), None)
            return last_user_message
        except Exception as e:
            raise Exception(f"_last_user_message :: {e}")

    @property
    def conversation(self):
        try:
            user_key = "user"
            agent_key = "assistant"
            messages = self.messages
            conversation = []
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation.append({"role": user_key, "content": message.message['text']})
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message:
                            conversation.append({"role": agent_key, "content": message.message['text_with_tags']})
                        else:
                            conversation.append({"role": agent_key, "content": message.message['text']})
                elif message.sender == "system":
                    conversation.append({"role": "system", "content": message.message['text']})
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: messages: " + str(e))

    def get_conversation_as_string(self, agent_key="Agent", user_key="User", with_tags=True):
        try:
            messages = self.messages
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
