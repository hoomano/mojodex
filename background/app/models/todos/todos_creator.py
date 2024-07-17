from sqlalchemy import func
from mojodex_core.db import with_db_session
from mojodex_core.entities.db_base_entities import MdTodo, MdTodoScheduling
from mojodex_core.entities.user import User
from mojodex_core.entities.user_task import UserTask
from mojodex_core.entities.user_task_execution import UserTaskExecution
from mojodex_core.json_loader import json_decode_retry
from mojodex_core.logging_handler import on_json_error
from mojodex_core.knowledge_manager import KnowledgeManager
from mojodex_core.email_sender.email_service import EmailService
from mojodex_core.llm_engine.mpt import MPT
from datetime import datetime

class TodosCreator:

    todos_extractor_mpt_filename = "instructions/extract_todos.mpt"

    def __init__(self, user_task_execution_pk):
        self.user_task_execution_pk = user_task_execution_pk


    def extract_and_save(self):
        """
        Extracts todos from the user_task_execution and send them to mojodex-backend to save them in the db
        """
        try:
            collected_data = self._collect_data()
            json_todos = self._extract(*collected_data)
            for todo in json_todos['todos']:
                if todo['mentioned_as_todo'].strip().lower() != "yes":
                    if todo['mentioned_as_todo'].strip().lower() != 'no':
                        EmailService().send_technical_error_email(
                            f"{self.__class__.__name__} - (Warning) Extracting todos for user_task_execution_pk {self.user_task_execution.user_task_execution_pk} : {todo['mentioned_as_todo']} is not a valid value for mentioned_as_todo")
                    continue
                try:
                    # check reminder_date is a DateTime in format yyyy-mm-dd
                    due_date = datetime.strptime(todo['due_date'], "%Y-%m-%d")
                except ValueError:
                    # Invalid due date, not saving to db just skip it
                    continue
                self._save_to_db(todo['todo_definition'], due_date)
            self._mark_todo_extracted()
        except Exception as e:
            EmailService().send_technical_error_email(f"{self.__class__.__name__} : extract_and_save: {e}")

    @with_db_session
    def _collect_data(self, db_session):
        """
        Collects necessary data from DB to call the prompt extracting ToDos
        """
        try:
            user_task_execution: UserTaskExecution
            user: User
            user_task_execution, user = db_session.query(UserTaskExecution, User) \
                .join(UserTask, UserTask.user_task_pk == UserTaskExecution.user_task_fk) \
                .join(User, User.user_id == UserTask.user_id) \
                .filter(UserTaskExecution.user_task_execution_pk == self.user_task_execution_pk) \
                .first()
                        # Subquery to get the latest todo_scheduling for each todo
            latest_todo_scheduling = db_session.query(
                MdTodoScheduling.todo_fk,
                func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date')) \
                .group_by(MdTodoScheduling.todo_fk) \
                .subquery()
            
            todos = db_session.query(MdTodo.description, latest_todo_scheduling.c.latest_scheduled_date) \
                    .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                    .filter(MdTodo.user_task_execution_fk.in_([previous_related_user_task_execution.user_task_execution_pk for previous_related_user_task_execution in user_task_execution.previous_related_user_task_executions])) \
                    .all()
                
            related_previous_user_task_executions_todos = [{"scheduled_date": str(scheduled_date), "description": description} for description, scheduled_date in todos]

            task_result = f"{user_task_execution.last_produced_text_version.title}\n{user_task_execution.last_produced_text_version.production}"
            
            return user.user_id, user.datetime_context, user.name, user.goal, user.company_description, user_task_execution.task.name_for_system, user_task_execution.task.definition_for_system, user_task_execution.session.get_conversation_as_string(with_tags=False), task_result, related_previous_user_task_executions_todos, user.language_code
        except Exception as e:
            raise Exception(f"_collect_data: {e}")

    @json_decode_retry(retries=3, required_keys=['todos'], on_json_error=on_json_error)
    def _extract(self, user_id, user_datetime_context, user_name, user_business_goal, user_company_description, task_name_for_system, 
                  task_definition_for_system, task_execution_conversation, task_execution_result, related_previous_user_task_executions_todos, language):
        try:
            todos_extractor = MPT(TodosCreator.todos_extractor_mpt_filename,
                                  mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                                  user_datetime_context=user_datetime_context,
                                  username=user_name,
                                  user_business_goal=user_business_goal,
                                  user_company_knowledge=user_company_description,
                                  task_name=task_name_for_system,
                                  task_definition=task_definition_for_system,
                                  task_conversation=task_execution_conversation,
                                  task_result=task_execution_result,
                                  linked_user_task_executions_todos=related_previous_user_task_executions_todos,
                                  language=language
                                  )

            result = todos_extractor.run(user_id=user_id,
                                          temperature=0, max_tokens=500,
                                          json_format=True,
                                          user_task_execution_pk=self.user_task_execution_pk,
                                          task_name_for_system=task_name_for_system)

            return result
        except Exception as e:
            raise Exception(f"_extract :: {e}")


    @with_db_session
    def _save_to_db(self, description, due_date, db_session):
        """
        Save new todo in db
        """
        try:

            # create new todo
            new_todo = MdTodo(
                creation_date=datetime.now(),
                description=description,
                user_task_execution_fk=self.user_task_execution_pk
            )
            db_session.add(new_todo)
            db_session.flush()
            db_session.refresh(new_todo)

            # create todo_scheduling
            new_todo_scheduling = MdTodoScheduling(
                todo_fk=new_todo.todo_pk,
                scheduled_date=due_date
            )

            db_session.add(new_todo_scheduling)
            db_session.commit()

        except Exception as e:
            raise Exception(f"_save_to_db: {e}")

    @with_db_session
    def _mark_todo_extracted(self, db_session):
        """
        Mark the user_task_execution's todos has been extracted by sending it to mojodex-backend through appropriated route
        """
        try:
            user_task_execution: UserTaskExecution = db_session.query(UserTaskExecution).get(self.user_task_execution_pk)
            user_task_execution.todos_extracted = datetime.now()
            db_session.commit()
        except Exception as e:
            raise Exception(f"_mark_todo_extracted: {e}")