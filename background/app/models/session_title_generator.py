import os
from datetime import datetime

import requests
from background_logger import BackgroundLogger

from mojodex_core.llm_engine.mpt import MPT


class SessionTitleGenerator:
    logger_prefix = "SessionTitleGenerator::"

    generate_title_mpt_filename = "instructions/generate_title_prompt.mpt"

    def __init__(self, session_id, user_id, knwoledge_collector):
        try:
            self.logger = BackgroundLogger(
                f"{SessionTitleGenerator.logger_prefix} -- session_id: {session_id}")
            self.session_id = session_id
            self.user_id = user_id
            self.knowledge_collector = knwoledge_collector
            self.logger.debug("__init__")
        except Exception as e:
            self.logger.error(f"__init__ :: {e}")

    def generate_session_title(self, sender, message, session_date, language):
        try:
            self.logger.debug("generate_session_title")
            generate_title = MPT(SessionTitleGenerator.generate_title_mpt_filename, mojo_knowledge=self.knowledge_collector.mojo_knowledge,
                                         global_context=self.knowledge_collector.global_context,
                                         username=self.knowledge_collector.user_name,
                                         user_company_knowledge=self.knowledge_collector.user_company_knowledge,
                                         sender=sender, message=message, session_date=session_date, language=language)
            responses = generate_title.run(user_id= self.user_id, temperature=0.5,
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
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(
                    f"_save_to_db : {internal_request.status_code} - {internal_request.text}")
        except Exception as e:
            self.logger.error(f"_save_to_db :: {e}")
