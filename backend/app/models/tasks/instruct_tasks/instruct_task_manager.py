from models.tasks.task_executor import TaskExecutor

from models.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from models.assistant.execution_manager import ExecutionManager
from app import placeholder_generator
from models.assistant.chat_assistant import ChatAssistant

from models.tasks.tag_manager import TagManager


class InstructTaskManager:

    def __init__(self, session_id, user_id):
        self.task_input_manager = TagManager("ask_user_primary_info", "Hello world!")
        self.task_executor = TaskExecutor(session_id, user_id)

    @property
    def task_execution_placeholder(self):
        return f"{ExecutionManager.execution_start_tag}" \
               f"{TaskProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{TaskProducedTextManager.title_end_tag}" \
               f"{TaskProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{TaskProducedTextManager.draft_end_tag}" \
               f"{ExecutionManager.execution_end_tag}"

    @property
    def task_message_placeholder(self):
        return self.task_input_manager.placeholder

    def manage_response_task_tags(self, response):
        try:
            if self.task_input_manager.start_tag in response:
                return self.task_input_manager.manage_text(response)
            # if TaskToolManager.tool_usage_start_tag in response:
            #    return self.task_tool_manager.manage_tool_usage_text(response,
            #                                                         self.running_user_task_execution.user_task_execution_pk,
            #                                                         self._get_task_tools_json(self.running_task))
            return {"text": response}
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_response_task_tags :: {e}")

    def manage_task_stream(self, partial_text, mojo_message_token_stream_callback, draft_token_stream_callback):
        try:
            text = None
            if self.task_input_manager.start_tag in partial_text:
                text = ChatAssistant.remove_tags_from_text(partial_text,
                                                           self.task_input_manager.start_tag,
                                                           self.task_input_manager.end_tag)
            # elif TaskToolManager.tool_usage_start_tag in partial_text:
            #     text = AssistantMessageGenerator.remove_tags_from_text(partial_text, TaskToolManager.tool_usage_start_tag,
            #                                                           TaskToolManager.tool_usage_end_tag)
            if text and mojo_message_token_stream_callback:
                mojo_message_token_stream_callback(text)

            elif ExecutionManager.execution_start_tag in partial_text:
                # take the text between <execution> and </execution>
                text = ChatAssistant.remove_tags_from_text(partial_text,
                                                           ExecutionManager.execution_start_tag,
                                                           ExecutionManager.execution_end_tag)
                draft_token_stream_callback(text)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_task_stream :: {e}")
