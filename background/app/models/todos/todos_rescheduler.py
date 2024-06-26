import os
from datetime import datetime

import requests
from mojodex_core.json_loader import json_decode_retry
from background_logger import BackgroundLogger
from mojodex_core.logging_handler import on_json_error


from mojodex_core.mail import send_technical_error_email

from mojodex_core.llm_engine.mpt import MPT


class TodosRescheduler:
    logger_prefix = "TodosRescheduler"
    todos_scheduling_url = "/todos_scheduling"

    todos_rescheduler_mpt_filename = "instructions/reschedule_todo.mpt"

    def __init__(self, todo_pk, user_task_execution, knowledge_collector, todo_description, n_scheduled,
                 first_scheduled_date, todo_list):
        self.todo_pk = todo_pk
        self.user_task_execution = user_task_execution
        self.knowledge_collector = knowledge_collector
        self.todo_description = todo_description
        self.n_scheduled = n_scheduled
        self.first_scheduled_date = first_scheduled_date
        self.todo_list = todo_list
        self.logger = BackgroundLogger(
            f"{TodosRescheduler.logger_prefix} - todo_pk {todo_pk}")

    def reschedule_and_save(self):
        try:
            json_result = self.__reschedule()
            # check reminder_date is a DateTime in format yyyy-mm-dd
            try:
                datetime.strptime(json_result['reschedule_date'], "%Y-%m-%d")
                save_to_db = True
            except ValueError:
                self.logger.error(
                    f"Error extracting todos : Invalid reschedule_date {json_result['reschedule_date']} - Not saving to db")
                send_technical_error_email(f"Error in {self.logger_prefix} - reschedule_and_save: Invalid reschedule_date {json_result['reschedule_date']} - Not saving to db."
                                       f"This is not blocking, only this todo {self.todo_pk} will not be rescheduled.")
                save_to_db = False
            if save_to_db:
                self.__save_to_db(
                    json_result['argument'], json_result['reschedule_date'])

        except Exception as e:
            raise Exception(f"{self.logger_prefix} : reschedule_and_save: {e}")

    @json_decode_retry(retries=3, required_keys=['reschedule_date', 'argument'], on_json_error=on_json_error)
    def __reschedule(self):
        self.logger.debug(f"_reschedule")
        try:
            todos_rescheduler = MPT(TodosRescheduler.todos_rescheduler_mpt_filename,
                                    mojo_knowledge=self.knowledge_collector.mojodex_knowledge,
                                    user_datetime_context=self.knowledge_collector.localized_context,
                                    username=self.knowledge_collector.user_name,
                                    user_business_goal=self.knowledge_collector.user_business_goal,
                                    user_company_knowledge=self.knowledge_collector.user_company_knowledge,
                                    task_name=self.user_task_execution.task_name,
                                    task_definition=self.user_task_execution.task_definition,
                                    task_result=self.user_task_execution.task_result,
                                    todo_definition=self.todo_description,
                                    todo_list=self.todo_list,
                                    n_scheduled=self.n_scheduled
                                    )
            results = todos_rescheduler.run(user_id=self.user_task_execution.user_id,
                                            temperature=0, max_tokens=500, json_format=True,
                                            user_task_execution_pk=self.user_task_execution.user_task_execution_pk,
                                            task_name_for_system=self.user_task_execution.task_name)

            result = results[0]
            return result

        except Exception as e:
            raise Exception(f"_extract :: {e}")

    def __save_to_db(self, argument, reschedule_date):
        try:
            self.logger.debug(f"_save_to_db: {reschedule_date}")
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/{TodosRescheduler.todos_scheduling_url}"
            # Save follow-ups in db => send to mojodex-backend
            pload = {'datetime': datetime.now().isoformat(), 'argument': argument, 'reschedule_date': reschedule_date,
                     'todo_fk': self.todo_pk}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(str(internal_request.json()))
            return
        except Exception as e:
            raise Exception(f"__save_to_db: {e}")
