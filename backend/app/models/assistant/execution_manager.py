from models.tasks.tag_manager import TagManager

class ExecutionManager:

    tag_manager: TagManager = TagManager("execution")

    @staticmethod
    def manage_execution_text(execution_text):
        try:
            mojo_text = ExecutionManager.tag_manager.remove_tags_from_text(execution_text)
            return mojo_text
        except Exception as e:
            raise Exception(f"{ExecutionManager.__class__.__name__} :: manage_execution_text :: {e}")
