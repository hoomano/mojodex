from models.tasks.task_inputs_manager import TaskInputsManager

from models.tasks.task_executor import TaskExecutor

from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager
from models.session.execution_manager import ExecutionManager
from app import placeholder_generator

from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator


class TaskManager:

    def __init__(self, session_id, user_id):
        self.task_input_manager = TaskInputsManager(session_id)
        self.task_executor = TaskExecutor(session_id, user_id)

    @property
    def task_execution_placeholder(self):
        return f"{ExecutionManager.execution_start_tag}" \
               f"{InstructTaskProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{InstructTaskProducedTextManager.title_end_tag}" \
               f"{InstructTaskProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{InstructTaskProducedTextManager.draft_end_tag}" \
               f"{ExecutionManager.execution_end_tag}"


    def manage_response_task_tags(self, response):
        try:
            if TaskInputsManager.ask_user_input_start_tag in response:
                return self.task_input_manager.manage_ask_input_text(response)
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
            if TaskInputsManager.ask_user_input_start_tag in partial_text:
                text = AssistantMessageGenerator.remove_tags_from_text(partial_text,
                                                                       TaskInputsManager.ask_user_input_start_tag,
                                                                       TaskInputsManager.ask_user_input_end_tag)
            # elif TaskToolManager.tool_usage_start_tag in partial_text:
            #     text = AssistantMessageGenerator.remove_tags_from_text(partial_text, TaskToolManager.tool_usage_start_tag,
            #                                                           TaskToolManager.tool_usage_end_tag)
            if text and mojo_message_token_stream_callback:
                mojo_message_token_stream_callback(text)

            elif ExecutionManager.execution_start_tag in partial_text:
                # take the text between <execution> and </execution>
                text = AssistantMessageGenerator.remove_tags_from_text(partial_text,
                                                                       ExecutionManager.execution_start_tag,
                                                                       ExecutionManager.execution_end_tag)
                draft_token_stream_callback(text)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_task_stream :: {e}")