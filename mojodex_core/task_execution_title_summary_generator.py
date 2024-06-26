from mojodex_core.entities.abstract_entities.user_task_execution import UserTaskExecution
from mojodex_core.knowledge_manager import knowledge_manager
from mojodex_core.entities.db_base_entities import MdUserTaskExecution
from mojodex_core.entities.db_base_entities import MdTask, MdUserTask
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.db import with_db_session

class TaskExecutionTitleSummaryGenerator:

    
    @staticmethod
    @with_db_session
    def generate_title_and_summary(user_task_execution_pk, db_session):
        try:
            type = db_session.query(MdTask.type)\
                .join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk)\
                .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk)\
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk)\
                .first()[0]
            user_task_execution: UserTaskExecution = None
            if type == "workflow":
                from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
                user_task_execution = db_session.query(UserWorkflowExecution).get(user_task_execution_pk)
            else:
                from mojodex_core.entities.instruct_user_task_execution import InstructTaskExecution
                user_task_execution = db_session.query(InstructTaskExecution).get(user_task_execution_pk)
            task_execution_summary = MPT("mojodex_core/instructions/task_execution_summary.mpt",
                                        mojo_knowledge=knowledge_manager.mojodex_knowledge,
                                        global_context=user_task_execution.user.datetime_context,
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
