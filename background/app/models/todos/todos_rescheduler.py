
from mojodex_core.db import with_db_session
from mojodex_core.entities.db_base_entities import MdTodoScheduling
from mojodex_core.entities.todo import Todo
from mojodex_core.entities.user import User
from mojodex_core.entities.user_task import UserTask
from mojodex_core.entities.user_task_execution import UserTaskExecution
from mojodex_core.json_loader import json_decode_retry
from mojodex_core.logging_handler import on_json_error
from mojodex_core.email_sender.email_service import EmailService
from mojodex_core.knowledge_manager import KnowledgeManager
from mojodex_core.llm_engine.mpt import MPT
from datetime import datetime

class TodosRescheduler:

    todos_rescheduler_mpt_filename = "instructions/reschedule_todo.mpt"

    def __init__(self, todo_pk):
        self.todo_pk = todo_pk

    def reschedule_and_save(self):
        try:
            collected_data = self._collect_data()
            json_result = self._reschedule(*collected_data)
            try:
                # check reminder_date is a DateTime in format yyyy-mm-dd
                reschedule_date=datetime.strptime(json_result['reschedule_date'], "%Y-%m-%d")
            except ValueError:
                EmailService().send_technical_error_email(f"Error in {self.__class__.__name__} - reschedule_and_save: Invalid reschedule_date {json_result['reschedule_date']} - Not saving to db."
                                       f"This is not blocking, only this todo {self.todo_pk} will not be rescheduled.")
                return
            
            self._save_to_db(json_result['argument'], reschedule_date)
        except Exception as e:
            EmailService().send_technical_error_email(f"{self.__class__.__name__} : extract_and_save: {e}")
        

    @with_db_session
    def _collect_data(self, db_session):
        try:
            todo: Todo
            user_task_execution: UserTaskExecution
            user: User
            todo, user_task_execution, user = db_session.query(Todo, UserTaskExecution, User) \
                .join(UserTaskExecution, UserTaskExecution.user_task_execution_pk == Todo.user_task_execution_fk) \
                .join(UserTask, UserTask.user_task_pk == UserTaskExecution.user_task_fk) \
                .join(User, User.user_id == UserTask.user_id) \
                .filter(Todo.todo_pk == self.todo_pk) \
                .first()
            task_result = f"{user_task_execution.last_produced_text_version.title}\n{user_task_execution.last_produced_text_version.production}"
            
            return user.user_id, user_task_execution.user_task_execution_pk, user_task_execution.task.name_for_system, user.datetime_context, user.name, user.goal, user.company_description, user_task_execution.task.definition_for_system, task_result, todo.description, user.twenty_first_todo_list_items, todo.n_times_scheduled
            
        except Exception as e:
            raise Exception(f"_collect_data :: {e}")

    @json_decode_retry(retries=3, required_keys=['reschedule_date', 'argument'], on_json_error=on_json_error)
    def _reschedule(self, user_id, user_task_execution_pk, task_name_for_system, user_datetime_context, username, user_business_goal,
                    user_company_knowledge, task_definition_for_system, task_result, todo_definition, todo_list, n_scheduled):
        try:
            todos_rescheduler = MPT(TodosRescheduler.todos_rescheduler_mpt_filename,
                                    mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                                    user_datetime_context=user_datetime_context,
                                    username=username,
                                    user_business_goal=user_business_goal,
                                    user_company_knowledge=user_company_knowledge,
                                    task_name=task_name_for_system,
                                    task_definition=task_definition_for_system,
                                    task_result=task_result,
                                    todo_definition=todo_definition,
                                    todo_list=todo_list,
                                    n_scheduled=n_scheduled
                                    )

            results = todos_rescheduler.run(user_id=user_id,
                                            temperature=0, max_tokens=500, json_format=True,
                                            user_task_execution_pk=user_task_execution_pk,
                                            task_name_for_system=task_name_for_system)
        
            result = results[0]
            return result
        except Exception as e:
            raise Exception(f"_reschedule :: {e}")

    @with_db_session
    def _save_to_db(self, argument, reschedule_date, db_session):
        """
        Save new todo due-date in db by sending it to mojodex-backend through appropriated route because backend is the only responsible for writing in db
        """
        try:
            new_todo_scheduling = MdTodoScheduling(
                todo_fk=self.todo_pk,
                scheduled_date=reschedule_date,
                reschedule_justification=argument
            )

            db_session.add(new_todo_scheduling)
            db_session.commit()
        except Exception as e:
            raise Exception(f"_save_to_db: {e}")
