from mojodex_core.entities import MdMessage
from sqlalchemy.orm.attributes import flag_modified
class ChatSession:
    def __init__(self, session_id, db_session):
        self.session_id = session_id
        self.db_session = db_session

    @property
    def _db_messages(self):
        try:
            return self.db_session.query(MdMessage).filter(MdMessage.session_id == self.session_id).order_by(
                MdMessage.message_date).all()
        except Exception as e:
            raise Exception("_db_messages: " + str(e))

    @property
    def _last_user_message(self):
        try:
            from models.assistant.session import Session as SessionModel
            return next((message for message in self._db_messages[::-1] if message.sender == SessionModel.user_message_key), None)
        except Exception as e:
            raise Exception(f"_last_user_message :: {e}")

    def associate_last_user_message_with_user_task_execution_pk(self, user_task_execution_pk):
        try:
            last_user_message = self._last_user_message
            if last_user_message:
                new_message = last_user_message.message

                new_message['user_task_execution_pk'] = user_task_execution_pk
                last_user_message.message = new_message
                flag_modified(last_user_message, "message")
                self.db_session.commit()
        except Exception as e:
            raise Exception(f"__associate_previous_user_message :: {e}")

    @property
    def conversation(self):
        try:
            user_key = "user"
            agent_key = "assistant"
            messages = self._db_messages
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
            messages = self._db_messages
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
