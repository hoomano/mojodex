from models.session.assistant_message_generators.assistant_message_generator import \
    AssistantMessageGenerator

from mojodex_backend_logger import MojodexBackendLogger


class ExecutionManager:
    execution_start_tag, execution_end_tag = "<execution>", "</execution>"

    def __init__(self):
        self.logger = MojodexBackendLogger(f"{self.__class__.__name__}")

    def manage_execution_text(self, execution_text):
        try:
            mojo_text = AssistantMessageGenerator.remove_tags_from_text(execution_text, self.execution_start_tag,
                                                                             self.execution_end_tag)
            return mojo_text
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_execution_text :: {e}")
