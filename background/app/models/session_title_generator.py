import os
from datetime import datetime

import requests
from background_logger import BackgroundLogger
from jinja2 import Template
from llm_calls.mojodex_openai import MojodexOpenAI

from azure_openai_conf import AzureOpenAIConf


class SessionTitleGenerator:
    logger_prefix = "SessionTitleGenerator::"

    generate_title_prompt = "/data/prompts/background/session_started/generate_title_prompt.txt"
    title_generator = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "GENERATE_SESSION_TITLE")

    def __init__(self, session_id, user_id, knwoledge_collector):
        try:
            self.logger = BackgroundLogger(f"{SessionTitleGenerator.logger_prefix} -- session_id: {session_id}")
            self.session_id = session_id
            self.user_id = user_id
            self.knowledge_collector = knwoledge_collector
            self.logger.debug("__init__")
        except Exception as e:
            self.logger.error(f"__init__ :: {e}")

    def generate_session_title(self, sender, message, session_date, language):
        try:
            self.logger.debug("generate_session_title")
            with open(SessionTitleGenerator.generate_title_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(mojo_knowledge=self.knowledge_collector.mojo_knowledge,
                                         global_context=self.knowledge_collector.global_context,
                                         username=self.knowledge_collector.user_name,
                                         user_company_knowledge=self.knowledge_collector.user_company_knowledge,
                                         sender=sender, message=message, session_date=session_date, language=language)
                messages = [{"role": "system", "content": prompt}]
            responses = SessionTitleGenerator.title_generator.chat(messages, self.user_id, temperature=0.5,
                                                                   max_tokens=50)
            title = responses[0]
            self._save_to_db(title)
            self.logger.debug(f"generate_session_title :: {title}")
            return title
        except Exception as e:
            self.logger.error(f"generate_session_title :: {e}")

    def _save_to_db(self, title):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/session"
            pload = {'datetime': datetime.now().isoformat(),
                     'session_id': self.session_id,
                     'title': title}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(
                    f"_save_to_db : {internal_request.status_code} - {internal_request.text}")
        except Exception as e:
            self.logger.error(f"_save_to_db :: {e}")
