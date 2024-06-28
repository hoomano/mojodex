from mojodex_core.entities.user_task_execution import UserTaskExecution
from mojodex_core.knowledge_manager import KnowledgeManager
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.db import with_db_session

class TaskExecutionTitleSummaryGenerator:

    
    @staticmethod
    @with_db_session
    def generate_title_and_summary(user_task_execution_pk, db_session):
        try:
            user_task_execution = db_session.query(UserTaskExecution).get(user_task_execution_pk)
            task_execution_summary = MPT("mojodex_core/instructions/task_execution_summary.mpt",
                                        mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                                        user_datetime_context=user_task_execution.user.datetime_context,
                                        username=user_task_execution.user.name,
                                        user_company_knowledge=user_task_execution.user,
                                        task=user_task_execution.task,
                                        user_task_inputs=user_task_execution.json_input_values,
                                        user_messages_conversation=user_task_execution.session.get_conversation_as_string())

            responses = task_execution_summary.run(user_id=user_task_execution.user.user_id,
                                                temperature=0, max_tokens=500,
                                                user_task_execution_pk=user_task_execution.user_task_execution_pk,
                                                task_name_for_system=user_task_execution.task.name_for_system,
                                                )
            response = responses[0]
            user_task_execution.title = response.split("<title>")[1].split("</title>")[0]
            user_task_execution.summary = response.split("<summary>")[1].split("</summary>")[0]
            db_session.commit()
        except Exception as e:
            raise Exception(f"generate_title_and_summary :: {e}")
