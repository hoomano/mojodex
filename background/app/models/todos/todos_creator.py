import os
from datetime import datetime

import requests
from mojodex_core.json_loader import json_decode_retry
from background_logger import BackgroundLogger
from mojodex_core.logging_handler import on_json_error


from mojodex_core.mail import send_technical_error_email

from mojodex_core.llm_engine.mpt import MPT


class TodosCreator:
    logger_prefix = "TodosCreator"
    todos_url = "/todos"

    todos_extractor_mpt_filename = "instructions/extract_todos.mpt"

    def __init__(self, user_task_execution, knowledge_collector, language, conversation,
                 linked_user_task_executions_todos):
        self.user_task_execution = user_task_execution
        self.knowledge_collector = knowledge_collector
        self.language = language
        self.conversation = conversation
        self.linked_user_task_executions_todos = linked_user_task_executions_todos
        self.logger = BackgroundLogger(
            f"{TodosCreator.logger_prefix} - user_task_execution_pk {user_task_execution.user_task_execution_pk}")

    def extract_and_save(self):
        try:
            self.logger.debug("extract_and_save")
            json_todos = self.__extract()
            self.logger.debug(f"Extracted - {len(json_todos['todos'])} todos")
            for todo in json_todos['todos']:
                if todo['mentioned_as_todo'].strip().lower() != "yes":
                    self.logger.debug(
                        f"extract_and_save: {todo['todo_definition']} not mentioned as todo - Not saving to db")
                    if todo['mentioned_as_todo'].strip().lower() != 'no':
                        send_technical_error_email(
                            f"(Warning) Extracting todos for user_task_execution_pk {self.user_task_execution.user_task_execution_pk} : {todo['mentioned_as_todo']} is not a valid value for mentioned_as_todo")
                    continue
                # check reminder_date is a DateTime in format yyyy-mm-dd
                try:
                    datetime.strptime(todo['due_date'], "%Y-%m-%d")
                    save_to_db = True
                except ValueError:
                    self.logger.error(
                        f"Error extracting todos : Invalid reminder_date {todo['due_date']} - Not saving to db")
                    save_to_db = False
                if save_to_db:
                    self.__save_to_db(
                        todo['todo_definition'], todo['due_date'])
                    self.logger.debug(f"Saved to db")
        except Exception as e:
            raise Exception(f"{self.logger_prefix} : extract_and_save: {e}")

    @json_decode_retry(retries=3, required_keys=['todos'], on_json_error=on_json_error)
    def __extract(self):
        self.logger.debug(f"_extract")
        try:
            todos_extractor = MPT(TodosCreator.todos_extractor_mpt_filename,
                                  mojo_knowledge=self.knowledge_collector.mojodex_knowledge,
                                  user_datetime_context=self.knowledge_collector.localized_context,
                                  username=self.knowledge_collector.user_name,
                                  user_business_goal=self.knowledge_collector.user_business_goal,
                                  user_company_knowledge=self.knowledge_collector.user_company_knowledge,
                                  task_name=self.user_task_execution.task_name,
                                  task_definition=self.user_task_execution.task_definition,
                                  task_conversation=self.conversation,
                                  task_result=self.user_task_execution.task_result,
                                  linked_user_task_executions_todos=self.linked_user_task_executions_todos,
                                  language=self.language
                                  )

            results = todos_extractor.run(user_id=self.user_task_execution.user_id,
                                          temperature=0, max_tokens=500,
                                          json_format=True,
                                          user_task_execution_pk=self.user_task_execution.user_task_execution_pk,
                                          task_name_for_system=self.user_task_execution.task_name)

            result = results[0]
            return result

        except Exception as e:
            raise Exception(f"_extract :: {e}")

    def __save_to_db(self, description, due_date):
        try:
            self.logger.debug(f"_save_to_db: {description}")
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/{TodosCreator.todos_url}"
            # Save follow-ups in db => send to mojodex-backend
            pload = {'datetime': datetime.now().isoformat(), 'description': description, 'due_date': due_date,
                     'user_task_execution_fk': self.user_task_execution.user_task_execution_pk}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(str(internal_request.json()))
            return internal_request.json()["todo_pk"]
        except Exception as e:
            raise Exception(f"__save_to_db: {e}")
