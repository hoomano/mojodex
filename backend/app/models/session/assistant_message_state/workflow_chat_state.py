from models.workflows.workflow_execution import WorkflowExecution
from models.session.assistant_message_state.task_enabled_chat_state import TaskEnabledChatState


class WorkflowChatState(TaskEnabledChatState):
    logger_prefix = "WorkflowChatState :: "

    def __init__(self, running_user_workflow_execution_pk):
        try:
            super().__init__(running_user_workflow_execution_pk)
            self.running_user_workflow_execution = WorkflowExecution(running_user_workflow_execution_pk)
        except Exception as e:
            raise Exception(f"{WorkflowChatState.logger_prefix} __init__ :: {e}")