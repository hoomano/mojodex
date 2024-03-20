from models.workflows.workflow import WorkflowExecution
from models.session.assistant_message_state.chat_state import ChatState
from app import db
from mojodex_core.entities import MdWorkflow, MdUserWorkflow, MdUserWorkflowExecution
from sqlalchemy import or_, func


class WorkflowChatState(ChatState):
    logger_prefix = "WorkflowChatState :: "

    def __init__(self, running_user_workflow_execution_pk):
        try:
            super().__init__()
            self.running_user_workflow_execution = WorkflowExecution(running_user_workflow_execution_pk)
        except Exception as e:
            raise Exception(f"{WorkflowChatState.logger_prefix} __init__ :: {e}")


        
    def __set_workflow_and_execution(self, user_workflow_execution_pk):
        try:
            self.running_workflow, self.running_user_workflow, self.running_user_workflow_execution = db.session.query(MdWorkflow, MdUserWorkflow, MdUserWorkflowExecution) \
                .join(MdUserWorkflow, MdUserWorkflow.workflow_fk == MdWorkflow.workflow_pk) \
                .join(MdUserWorkflowExecution, MdUserWorkflowExecution.user_workflow_fk == MdUserWorkflow.user_workflow_pk) \
                .filter(MdUserWorkflowExecution.user_workflow_execution_pk == user_workflow_execution_pk) \
                .first()
        except Exception as e:
            raise Exception(f"__set_workflow_and_execution :: {e}")

