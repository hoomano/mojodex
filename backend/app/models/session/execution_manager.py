from models.session.assistant_message_generators.assistant_message_generator import \
    AssistantMessageGenerator

from mojodex_backend_logger import MojodexBackendLogger


class ExecutionManager:
    logger_prefix = "ExecutionManager :: "
    execution_start_tag, execution_end_tag = "<execution>", "</execution>"

    def __init__(self, session_id):
        self.logger = MojodexBackendLogger(f"{ExecutionManager.logger_prefix} -- session_id {session_id}")

    def manage_execution_text(self, execution_text, running_task, task_name_for_user,
                              user_task_execution_pk, task_executor, use_draft_placeholder=False):
        try:
            mojo_text = AssistantMessageGenerator.remove_tags_from_text(execution_text, self.execution_start_tag,
                                                                             self.execution_end_tag)

            if running_task:
                response = task_executor.manage_execution_text(execution_text=mojo_text, task=running_task,
                                                           task_name=task_name_for_user,
                                                           user_task_execution_pk=user_task_execution_pk,
                                                           use_draft_placeholder=use_draft_placeholder)
                response["text_with_tags"] = execution_text
                return response
            else:
                # TODO: create a dedicated method to save the execution text as a ProducedText using a ProducedTextManager
                return {"text": mojo_text, "text_with_tags": execution_text}
        except Exception as e:
            raise Exception(f"{ExecutionManager.logger_prefix} :: manage_execution_text :: {e}")
