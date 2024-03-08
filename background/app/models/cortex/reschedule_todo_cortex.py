from datetime import datetime

from app import db, language_retriever, conversation_retriever
from mojodex_core.entities import *

from models.user_task_execution import UserTaskExecution
from models.knowledge.knowledge_collector import KnowledgeCollector

from background_logger import BackgroundLogger
from sqlalchemy import func, text

from models.todos.todos_rescheduler import TodosRescheduler

from app import send_admin_error_email


class RescheduleTodoCortex:
    logger_prefix = "RescheduleTodoCortex"

    def __init__(self, todo):
        try:
            self.logger = BackgroundLogger(
                f"{RescheduleTodoCortex.logger_prefix} - todo_pk {todo.todo_pk}")
            self.logger.debug(f"__init__")
            self.todo_pk = todo.todo_pk
            self.todo_description = todo.description
            self.n_scheduled = self.__get_n_scheduled(self.todo_pk)
            self.first_scheduled_date = self.__get_first_scheduled_date(self.todo_pk)

            self.session_id, self.user_task_execution_pk, self.user_task_pk, self.task_name_for_system, self.task_definition_for_system, self.task_input_values = self.__get_task_info(
                self.todo_pk)

            self.task_result = self.__get_task_result(self.user_task_execution_pk)
            self.user = db.session.query(MdUser).join(MdUserTask, MdUserTask.user_id == MdUser.user_id).filter(
                MdUserTask.user_task_pk == self.user_task_pk).first()
            self.company = db.session.query(MdCompany).join(MdUser, MdUser.company_fk == MdCompany.company_pk).filter(
                MdUser.user_id == self.user.user_id).first()
            self.language = language_retriever.get_language_from_session_or_user(self.session_id, self.user)
            self.knowledge_collector = KnowledgeCollector(self.user.name, self.user.timezone_offset, self.user.summary,
                                                          self.user.company_description, self.user.goal)
            self.user_task_execution = UserTaskExecution(self.session_id, self.user_task_execution_pk,
                                                         self.task_name_for_system,
                                                         self.task_definition_for_system, self.task_input_values,
                                                         self.task_result, self.user.user_id)

            self.todo_list = self.__get_todolist(self.user.user_id)


        except Exception as e:
            self.logger.error(f"__init__ :: {e}")
            send_admin_error_email(f"Error in {self.logger_prefix} - __init__ (todo_pk: {todo.todo_pk}): {e}")


    def reschedule_todo(self):
        try:
            todo_rescheduler = TodosRescheduler(
                self.todo_pk,
                self.user_task_execution,
                self.knowledge_collector,
                self.todo_description,
                self.n_scheduled,
                self.first_scheduled_date,
                self.todo_list)
            todo_rescheduler.reschedule_and_save()
        except Exception as e:
            self.logger.error(f"reschedule_todo: {e}")
            send_admin_error_email(f"Error in {self.logger_prefix} - todo_pk {self.todo_pk} - reschedule_todo: {e}")



    def __get_task_info(self, todo_pk):
        try:
            session_id, user_task_execution_pk, user_task_pk, task_name_for_system, task_definition_for_system, task_input_values = db.session.query(
                MdUserTaskExecution.session_id, MdUserTaskExecution.user_task_execution_pk, MdUserTask.user_task_pk, MdTask.name_for_system, MdTask.definition_for_system,
                MdUserTaskExecution.json_input_values) \
                .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                .join(MdUserTaskExecution, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .join(MdTodo, MdUserTaskExecution.user_task_execution_pk == MdTodo.user_task_execution_fk) \
                .filter(MdTodo.todo_pk == todo_pk) \
                .first()

            return session_id, user_task_execution_pk, user_task_pk, task_name_for_system, task_definition_for_system, task_input_values
        except Exception as e:
            raise Exception(f"_get_task_info: {e}")

    def __get_task_result(self, user_task_execution_pk):
        try:
            task_result = db.session.query(MdProducedTextVersion.production) \
                .join(MdProducedText, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .join(MdUserTaskExecution,
                      MdProducedText.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
                .order_by(MdProducedTextVersion.creation_date.desc()) \
                .first()[0]

            return task_result
        except Exception as e:
            raise Exception(f"_get_task_result: {e}")

    def __get_n_scheduled(self, todo_pk):
        try:
            n_scheduled = db.session.query(MdTodoScheduling).filter(MdTodoScheduling.todo_fk == todo_pk).count()
            return n_scheduled
        except Exception as e:
            raise Exception(f"_get_n_scheduled: {e}")

    def __get_first_scheduled_date(self, todo_pk):
        try:
            first_scheduled_date = db.session.query(MdTodoScheduling.scheduled_date) \
                .filter(MdTodoScheduling.todo_fk == todo_pk) \
                .order_by(MdTodoScheduling.scheduled_date) \
                .first()[0]
            return first_scheduled_date
        except Exception as e:
            raise Exception(f"_get_first_scheduled_date: {e}")


    def __get_todolist(self, user_id):
        try:
            # Subquery to get the latest todo_scheduling for each todo
            latest_todo_scheduling = db.session.query(
                MdTodoScheduling.todo_fk,
                func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date')) \
                .group_by(MdTodoScheduling.todo_fk) \
                .subquery()
            # Get the current date in UTC
            now_utc = datetime.utcnow().date()
            results = db.session.query(MdTodo.description, latest_todo_scheduling.c.latest_scheduled_date) \
                .join(MdUserTaskExecution, MdTodo.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdUser, MdUserTask.user_id == MdUser.user_id) \
                .filter(MdUser.user_id == user_id) \
                .filter(MdTodo.deleted_by_user.is_(None)) \
                .filter(MdTodo.completed.is_(None)) \
                .filter((latest_todo_scheduling.c.latest_scheduled_date - text(
                'md_user.timezone_offset * interval \'1 minute\'')) >= now_utc) \
                .order_by(latest_todo_scheduling.c.latest_scheduled_date.desc()) \
                .offset(0) \
                .limit(20) \
                .all()

            return [{'description': description, 'scheduled_date': scheduled_date} for description, scheduled_date in results]
        except Exception as e:
            raise Exception(f"_get_todolist: {e}")
