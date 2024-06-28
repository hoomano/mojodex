from mojodex_core.tag_manager import TagManager
from app import server_socket, placeholder_generator
from models.workflows.workflow_process_controller import WorkflowProcessController
from mojodex_core.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from models.tasks.task_executor import TaskExecutor
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution


class WorkflowManager:

    def __init__(self, session_id, user_id):
        self.workflow_step_no_go_explanation_manager = TagManager("no_go_explanation")
        self.workflow_step_clarification_manager = TagManager("ask_for_clarification")
        self.workflow_step_instruction_manager = TagManager("user_instruction")
        self.execution_manager = TagManager("execution")
        self.task_executor = TaskExecutor(session_id, user_id)

    @property
    def step_instruction_placeholder(self):
        return self.workflow_step_instruction_manager.add_tags_to_text("Result of the step must be shorter.")

    @property
    def clarification_placeholder(self):
        return self.workflow_step_clarification_manager.add_tags_to_text("Can you clarify your instruction to relaunch this workflow step?")

    @property
    def no_go_explanation_placeholder(self):
        return self.workflow_step_no_go_explanation_manager.add_tags_to_text("I can't edit initial inputs or already achieved workflow steps.")

    @property
    def task_execution_placeholder(self):
        return self.execution_manager.add_tags_to_text(
               f"{TaskProducedTextManager.title_tag_manager.add_tags_to_text(placeholder_generator.mojo_draft_title)}"
               f"{TaskProducedTextManager.draft_tag_manager.add_tags_to_text(placeholder_generator.mojo_draft_body)}")
    def manage_response_task_tags(self, response: str, workflow_execution: UserWorkflowExecution):
        try:
            if self.workflow_step_no_go_explanation_manager.start_tag in response:
                text_without_tags = self.workflow_step_no_go_explanation_manager.extract_text(response)
                return {"text": text_without_tags, "text_with_tags": response}
            elif self.workflow_step_clarification_manager.start_tag in response:
                text_without_tags = self.workflow_step_clarification_manager.extract_text(response)
                return {"text": text_without_tags, "text_with_tags": response}
            elif self.workflow_step_instruction_manager.start_tag in response:
                instruction = self.workflow_step_instruction_manager.extract_text(response)
                workflow_process_controller = WorkflowProcessController(workflow_execution.user_task_execution_pk)
                workflow_process_controller.invalidate_current_step(instruction)
                server_socket.start_background_task(workflow_process_controller.run)
                return None

            return {"text": response}
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_response_task_tags :: {e}")

    def manage_task_stream(self, partial_text, mojo_message_token_stream_callback, draft_token_stream_callback):
        try:
            text = None
            if self.workflow_step_clarification_manager.start_tag in partial_text:
                text = self.workflow_step_clarification_manager.extract_text(partial_text)
            elif self.workflow_step_instruction_manager.start_tag in partial_text:
                text = self.workflow_step_instruction_manager.extract_text(partial_text)

            if text and mojo_message_token_stream_callback:
                mojo_message_token_stream_callback(text)

            elif self.execution_manager.start_tag in partial_text:
                text = self.execution_manager.extract_text(partial_text)
                draft_token_stream_callback(text)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: manage_task_stream :: {e}")
