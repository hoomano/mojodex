from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from mojodex_backend_logger import MojodexBackendLogger


class TaskInputsManager:
    logger_prefix = "TaskInputsManager::"
    ask_user_input_start_tag = "<ask_user_primary_info>"
    ask_user_input_end_tag = "</ask_user_primary_info>"

    def __init__(self, session_id):
        self.logger = MojodexBackendLogger(f"{TaskInputsManager.logger_prefix} -- session_id {session_id}")

    def manage_ask_input_text(self, ask_input_text):
        try:
            mojo_text = AssistantMessageGenerator.remove_tags_from_text(ask_input_text, self.ask_user_input_start_tag, self.ask_user_input_end_tag)
            return {"text": mojo_text,
                    "text_with_tags": ask_input_text}
        except Exception as e:
            raise Exception(f"{TaskInputsManager.logger_prefix} :: manage_ask_input_text :: {e}")
