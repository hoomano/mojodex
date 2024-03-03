import os
from datetime import datetime

import requests
from app import db, language_retriever, conversation_retriever
from mojodex_core.entities import *

from models.user_task_execution import UserTaskExecution
from models.knowledge.knowledge_collector import KnowledgeCollector

from background_logger import BackgroundLogger

from models.todos.todos_creator import TodosCreator
from sqlalchemy import func


class ExtractTodosCortex:
    logger_prefix = "ExtractTodosCortex"

    def __init__(self, user_task_execution):
        try:
            self.logger = BackgroundLogger(
                f"{ExtractTodosCortex.logger_prefix} - user_task_execution_pk {user_task_execution.user_task_execution_pk}")
            self.logger.debug(f"__init__")
            self.session_id = user_task_execution.session_id  # used to identify any call to openai

            self.user_task_execution_pk = user_task_execution.user_task_execution_pk

            self.user_task_pk, self.task_name_for_system, self.task_definition_for_system, self.task_input_values = self.__get_task_info(
                user_task_execution)

            self.task_result = self.__get_task_result(user_task_execution)
            self.user = db.session.query(MdUser).join(MdUserTask, MdUserTask.user_id == MdUser.user_id).filter(
                MdUserTask.user_task_pk == self.user_task_pk).first()
            self.user_task_execution = UserTaskExecution(self.session_id, self.user_task_execution_pk, self.task_name_for_system,
                                                         self.task_definition_for_system, self.task_input_values,
                                                         self.task_result, self.user.user_id)

            self.company = db.session.query(MdCompany).join(MdUser, MdUser.company_fk == MdCompany.company_pk).filter(
                MdUser.user_id == self.user.user_id).first()
            self.language = language_retriever.get_language_from_session_or_user(self.session_id, self.user)
            self.knowledge_collector = KnowledgeCollector(self.user.name, self.user.timezone_offset, self.user.summary, self.user.company_description, self.user.goal)

            self.conversation = conversation_retriever.get_conversation_as_string(self.session_id, agent_key='YOU', user_key='USER', with_tags=False)

            self.linked_user_task_executions_todos = self.__get_linked_tasks_todos(user_task_execution)


        except Exception as e:
            self.logger.error(f"__init__ :: {e}")

    def extract_todos(self):
        try:

            self.logger.debug(f"extract_todos")
            todos_creator = TodosCreator(
                self.user_task_execution,
                self.knowledge_collector,
                self.language,
                self.conversation,
                self.linked_user_task_executions_todos)
            todos_creator.extract_and_save()
            self.__mark_todo_extracted()
        except Exception as e:
            self.logger.error(f"extract_todos: {e}")

    def __get_task_info(self, user_task_execution):
        try:
            user_task_pk, task_name_for_system, task_definition_for_system, task_input_values = db.session.query(
                MdUserTask.user_task_pk, MdTask.name_for_system, MdTask.definition_for_system,
                MdUserTaskExecution.json_input_values) \
                .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
                .join(MdUserTaskExecution, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution.user_task_execution_pk) \
                .first()

            return user_task_pk, task_name_for_system, task_definition_for_system, task_input_values
        except Exception as e:
            raise Exception(f"_get_task_info: {e}")

    def __get_task_result(self, user_task_execution):
        try:
            task_result = db.session.query(MdProducedTextVersion.production) \
                .join(MdProducedText, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .join(MdUserTaskExecution,
                      MdProducedText.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk) \
                .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution.user_task_execution_pk) \
                .order_by(MdProducedTextVersion.creation_date.desc()) \
                .first()[0]

            return task_result
        except Exception as e:
            raise Exception(f"__get_task_result: {e}")


    def __get_linked_tasks_todos(self, user_task_execution):
        try:
            linked_user_task_executions_todos = []

            # Subquery to get the latest todo_scheduling for each todo
            latest_todo_scheduling = db.session.query(
                MdTodoScheduling.todo_fk,
                func.max(MdTodoScheduling.scheduled_date).label('latest_scheduled_date')) \
                .group_by(MdTodoScheduling.todo_fk) \
                .subquery()

            while user_task_execution and user_task_execution.predefined_action_from_user_task_execution_fk:
                user_task_execution = db.session.query(MdUserTaskExecution) \
                    .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution.predefined_action_from_user_task_execution_fk) \
                    .first()
                if user_task_execution:
                    todos = db.session.query(MdTodo.description, latest_todo_scheduling.c.latest_scheduled_date) \
                        .join(latest_todo_scheduling, MdTodo.todo_pk == latest_todo_scheduling.c.todo_fk) \
                        .filter(MdTodo.user_task_execution_fk == user_task_execution.user_task_execution_pk) \
                        .all()
                    linked_user_task_executions_todos += [{"scheduled_date": str(scheduled_date), "description": description} for description, scheduled_date in todos]

            return linked_user_task_executions_todos

        except Exception as e:
            raise Exception(f"__get_linked_tasks_todos: {e}")


    def __mark_todo_extracted(self):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/extract_todos"
            # Save follow-ups in db => send to mojodex-backend
            pload = {'datetime': datetime.now().isoformat(),
                     'user_task_execution_fk': self.user_task_execution.user_task_execution_pk}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(str(internal_request.json()))
            return internal_request.json()["user_task_execution_pk"]
        except Exception as e:
            raise Exception(f"__save_to_db: {e}")


