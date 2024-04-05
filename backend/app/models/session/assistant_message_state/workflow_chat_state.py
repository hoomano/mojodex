from models.workflows.workflow_execution import WorkflowExecution
from models.session.assistant_message_state.chat_state import ChatState


class WorkflowChatState(ChatState):
    logger_prefix = "WorkflowChatState :: "

    def __init__(self, running_user_workflow_execution_pk):
        try:
            super().__init__()
            self.running_user_workflow_execution = WorkflowExecution(running_user_workflow_execution_pk)
        except Exception as e:
            raise Exception(f"{WorkflowChatState.logger_prefix} __init__ :: {e}")


    def get_conversation_as_list(self, session_id, without_last_message=False, agent_key="assistant", user_key="user"):
        try:
            messages = self._get_all_session_messages(session_id)
            if without_last_message:
                messages = messages[:-1]
            conversation = []
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation.append({"role": user_key, "content": message.message['text']})
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message:
                            conversation.append({"role": agent_key, "content": message.message['text_with_tags']})
                        else:
                            conversation.append({"role": agent_key, "content": message.message['text']})
                elif message.sender == "system": 
                    conversation.append({"role": "system", "content": message.message['text']})
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception(f"{ChatState.logger_prefix} get_conversation_as_list: " + str(e))