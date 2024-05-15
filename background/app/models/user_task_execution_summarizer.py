import os
from datetime import datetime
import requests

from background_logger import BackgroundLogger

from mojodex_core.mail import send_technical_error_email
from mojodex_core.llm_engine.mpt import MPT


class UserTaskExecutionSummarizer:
    logger_prefix = "UserTaskExecutionSummarizer::"

    def __init__(self, knowledge_collector, user_task_execution, user_messages_conversation):
        try:
            self.logger = BackgroundLogger(
                f"{UserTaskExecutionSummarizer.logger_prefix} - user_task_execution_pk {user_task_execution.user_task_execution_pk}")
            self.knowledge_collector = knowledge_collector
            self.user_task_execution = user_task_execution
            self.user_messages_conversation = user_messages_conversation
            self.title, self.summary = self._task_execution_summary()
            self._save_to_db()
        except Exception as e:
            send_technical_error_email(f"{self.logger.name} : {e}")
            raise Exception(
                f"{UserTaskExecutionSummarizer.logger_prefix} __init__: {e}")

    def _task_execution_summary(self, retry=3):
        prompt, response = None, None
        try:
            self.logger.info("_task_execution_summary")
            response = None

            task_execution_summary = MPT("instructions/task_execution_summary.mpt", 
                                         mojo_knowledge=self.knowledge_collector.mojodex_knowledge,
                                         global_context=self.knowledge_collector.localized_context,
                                         username=self.knowledge_collector.user_name,
                                         user_company_knowledge=self.knowledge_collector.user_company_knowledge,
                                         task_name=self.user_task_execution.task_name,
                                         task_definition=self.user_task_execution.task_definition,
                                         user_task_inputs=self.user_task_execution.json_input_values,
                                         user_messages_conversation=self.user_messages_conversation)

            responses = task_execution_summary.run(user_id=self.user_task_execution.user_id,
                                                   temperature=0, max_tokens=500,
                                                   user_task_execution_pk=self.user_task_execution.user_task_execution_pk,
                                                   task_name_for_system=self.user_task_execution.task_name,
                                                   )
            response = responses[0]
            title = response.split("<title>")[1].split("</title>")[0]
            summary = response.split("<summary>")[1].split("</summary>")[0]
            return title, summary
        except Exception as e:
            if retry > 0:
                self.logger.warning(
                    f"_task_execution_summary : {e}, retrying...")
                self._task_execution_summary(retry=retry - 1)
            else:
                # Save in file and we will open it only if the user gave access to their data
                file_path = f"/data/task_execution_summary_error_{self.user_task_execution.user_task_execution_pk}.txt"
                with open(file_path, "w") as f:
                    f.write(f"PROMPT:\n{prompt} \n\n\n RESPONSE:\n{response}")
                raise Exception(
                    f"_task_execution_summary:: {e} - data available in {file_path}")

    def _save_to_db(self):
        try:
            # Save in db => send to mojodex-backend
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/user_task_execution_summary"
            pload = {'datetime': datetime.now().isoformat(), 'title': self.title, 'summary': self.summary,
                     'user_task_execution_pk': self.user_task_execution.user_task_execution_pk}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                # I can't write complete pload for privacy reasons so just checking keys
                raise Exception(
                    f"Payload keys: {list(pload.keys())} - Status code: {internal_request.status_code} - text: {internal_request.text}")
        except Exception as e:
            raise Exception(f"_save_to_db: {e}")
