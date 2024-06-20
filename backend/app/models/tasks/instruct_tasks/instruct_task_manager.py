from models.tasks.task_executor import TaskExecutor

from models.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from models.assistant.execution_manager import ExecutionManager
from app import placeholder_generator
from models.assistant.chat_assistant import ChatAssistant

from models.tasks.tag_manager import TagManager


class InstructTaskManager:

    def __init__(self, session_id, user_id):
        self.task_input_manager = TagManager("ask_user_primary_info")
        self.task_executor = TaskExecutor(session_id, user_id)

    @property
    def task_execution_placeholder(self):
        return f"{ExecutionManager.execution_start_tag}" \
               f"{TaskProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{TaskProducedTextManager.title_end_tag}" \
               f"{TaskProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{TaskProducedTextManager.draft_end_tag}" \
               f"{ExecutionManager.execution_end_tag}"

    @property
    def task_message_placeholder(self):
        return self.task_input_manager.add_tags_to_text("Can you please provide more information?")

    def manage_response_task_tags(self, response):
        try:
            if self.task_input_manager.start_tag in response:
                text_without_tags = self.task_input_manager.remove_tags_from_text(response)
                return {"text": text_without_tags, "text_with_tags": response}
            return {"text": response}
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_response_task_tags :: {e}")

    def manage_task_stream(self, partial_text, mojo_message_token_stream_callback, draft_token_stream_callback):
        try:
            text = None
            if self.task_input_manager.start_tag in partial_text:
                text = self.task_input_manager.remove_tags_from_text(partial_text)
            if text and mojo_message_token_stream_callback:
                mojo_message_token_stream_callback(text)

            elif self.task_executor.tag_manager.execution_start_tag in partial_text:
                # take the text between <execution> and </execution>
                text = self.task_executor.tag_manager.remove_tags_from_text(partial_text)
                draft_token_stream_callback(text)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_task_stream :: {e}")
