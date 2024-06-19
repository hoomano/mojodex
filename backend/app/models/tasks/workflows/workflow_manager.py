from models.assistant.chat_assistant import ChatAssistant
from models.tasks.tag_manager import TagManager
from app import server_socket, placeholder_generator
from models.workflows.workflow_process_controller import WorkflowProcessController

from models.assistant.execution_manager import ExecutionManager
from models.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from models.tasks.task_executor import TaskExecutor
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution


class WorkflowManager:

    def __init__(self, session_id, user_id):
        self.workflow_step_no_go_explanation_manager = TagManager("no_go_explanation",
                                                                  "I can't edit initial inputs or already achieved workflow steps.")
        self.workflow_step_clarification_manager = TagManager("ask_for_clarification",
                                                              "Can you clarify your instruction to relaunch this workflow step?")
        self.workflow_step_instruction_manager = TagManager("user_instruction",
                                                            "Result of the step must be shorter.")
        self.task_executor = TaskExecutor(session_id, user_id)

    @property
    def step_instruction_placeholder(self):
        return self.workflow_step_instruction_manager.placeholder

    @property
    def clarification_placeholder(self):
        return self.workflow_step_clarification_manager.placeholder

    @property
    def no_go_explanation_placeholder(self):
        return self.workflow_step_no_go_explanation_manager.placeholder

    @property
    def task_execution_placeholder(self):
        return f"{ExecutionManager.execution_start_tag}" \
               f"{TaskProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{TaskProducedTextManager.title_end_tag}" \
               f"{TaskProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{TaskProducedTextManager.draft_end_tag}" \
               f"{ExecutionManager.execution_end_tag}"

    def manage_response_task_tags(self, response: str, workflow_execution: UserWorkflowExecution):
        try:
            if self.workflow_step_no_go_explanation_manager.start_tag in response:
                return self.workflow_step_no_go_explanation_manager.manage_text(response)
            elif self.workflow_step_clarification_manager.start_tag in response:
                return self.workflow_step_clarification_manager.manage_text(response)
            elif self.workflow_step_instruction_manager.start_tag in response:
                instruction = self.workflow_step_instruction_manager.manage_text(response)
                workflow_process_controller = WorkflowProcessController(workflow_execution.user_task_execution_pk)
                workflow_process_controller.invalidate_current_step(instruction['text'])
                server_socket.start_background_task(workflow_process_controller.run)
                return instruction

            return {"text": response}
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_response_task_tags :: {e}")

    def manage_task_stream(self, partial_text, mojo_message_token_stream_callback, draft_token_stream_callback):
        try:
            text = None
            if self.workflow_step_clarification_manager.start_tag in partial_text:
                text = ChatAssistant.remove_tags_from_text(partial_text,
                                                           self.workflow_step_clarification_manager.start_tag,
                                                           self.workflow_step_clarification_manager.end_tag)
            elif self.workflow_step_instruction_manager.start_tag in partial_text:
                text = ChatAssistant.remove_tags_from_text(partial_text,
                                                           self.workflow_step_instruction_manager.start_tag,
                                                           self.workflow_step_instruction_manager.end_tag)

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
