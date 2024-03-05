import os
from datetime import datetime
import requests
from mojodex_background_openai import MojodexBackgroundOpenAI
from jinja2 import Template

from background_logger import BackgroundLogger
from azure_openai_conf import AzureOpenAIConf

from app import send_admin_error_email


class UserTaskExecutionSummarizer:
    logger_prefix = "UserTaskExecutionSummarizer::"

    task_execution_summary_prompt = "/data/prompts/background/user_task_execution_end/user_task_execution_summarizer/task_execution_summary_prompt.txt"
    task_execution_summarizer = MojodexBackgroundOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf,"TASK_EXECUTION_SUMMARIZER")

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
            send_admin_error_email(f"{self.logger.name} : {e}")
            raise Exception(f"{UserTaskExecutionSummarizer.logger_prefix} __init__: {e}")

    def _task_execution_summary(self, retry=3):
        prompt, response = None, None
        try:
            self.logger.info("_task_execution_summary")
            response = None

            with open(UserTaskExecutionSummarizer.task_execution_summary_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(mojo_knowledge=self.knowledge_collector.mojo_knowledge,
                                         global_context=self.knowledge_collector.global_context,
                                         username=self.knowledge_collector.user_name,
                                         user_company_knowledge=self.knowledge_collector.user_company_knowledge,
                                         task_name=self.user_task_execution.task_name,
                                         task_definition=self.user_task_execution.task_definition,
                                         user_task_inputs=self.user_task_execution.json_input_values,
                                         user_messages_conversation=self.user_messages_conversation)

            messages = [{"role": "user", "content": prompt}]
            responses = UserTaskExecutionSummarizer.task_execution_summarizer.chat(messages,
                                                                                   self.user_task_execution.user_id,
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
                self.logger.warning(f"_task_execution_summary : {e}, retrying...")
                self._task_execution_summary(retry=retry - 1)
            else:
                # Save in file and we will open it only if the user gave access to their data
                file_path = f"/data/task_execution_summary_error_{self.user_task_execution.user_task_execution_pk}.txt"
                with open(file_path, "w") as f:
                    f.write(f"PROMPT:\n{prompt} \n\n\n RESPONSE:\n{response}")
                raise Exception(f"_task_execution_summary:: {e} - data available in {file_path}")

    def _save_to_db(self):
        try:
            # Save in db => send to mojodex-backend
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/user_task_execution_summary"
            pload = {'datetime': datetime.now().isoformat(), 'title': self.title, 'summary': self.summary,
                     'user_task_execution_pk': self.user_task_execution.user_task_execution_pk}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                # I can't write complete pload for privacy reasons so just checking keys
                raise Exception(
                    f"Payload keys: {list(pload.keys())} - Status code: {internal_request.status_code} - text: {internal_request.text}")
        except Exception as e:
            raise Exception(f"_save_to_db: {e}")
