from models.session.assistant_message_context.assistant_message_context import AssistantMessageContext


class ChatContext(AssistantMessageContext):
    logger_prefix = "ChatContext :: "

    def __init__(self, user, session_id, user_messages_are_audio, chat_state):
        try:
            self.state = chat_state
            self.user_messages_are_audio = user_messages_are_audio
            self.session_id = session_id
            super().__init__(user)
        except Exception as e:
            raise Exception(f"{ChatContext.logger_prefix} :: __init__ :: {e}")