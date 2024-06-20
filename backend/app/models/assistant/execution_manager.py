from models.tasks.tag_manager import TagManager
from mojodex_backend_logger import MojodexBackendLogger

class ExecutionManager:

    def __init__(self):
        self.logger = MojodexBackendLogger(f"{self.__class__.__name__}")
        self.tag_manager = TagManager("execution")

    def manage_execution_text(self, execution_text):
        try:
            mojo_text = self.tag_manager.remove_tags_from_text(execution_text)
            return mojo_text
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_execution_text :: {e}")
