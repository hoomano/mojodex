import os

import requests
from jinja2 import Template
from datetime import datetime

from background_logger import BackgroundLogger

from background.app.llm_api.mojodex_background_openai import OpenAIConf

from app import llm, llm_conf


class UserKnowledgeExtractor:
    logger_prefix = "UserKnowledgeExtractor::"

    extract_user_knowledge_prompt = "/data/prompts/background/knowledge/user_knowledge_extractor/extract_user_knowledge_prompt.txt"
    user_knowledge_extractor = llm(llm_conf, "EXTRACT_USER_KNOWLEDGE")

    def __init__(self, session_id, user_id, conversation):
        self.logger = BackgroundLogger(
            f"{UserKnowledgeExtractor.logger_prefix} - session_id {session_id}")
        self.session_id = session_id
        self.user_id = user_id
        self.conversation = conversation

    def update_user_summary(self, current_summary):
        try:
            # update user summary
            with open(UserKnowledgeExtractor.extract_user_knowledge_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(
                    conversation=self.conversation, existing_summary=current_summary)
            messages = [{"role": "user", "content": prompt}]

            response = UserKnowledgeExtractor.user_knowledge_extractor.chat(messages, self.user_id,
                                                                            temperature=0, max_tokens=200)
            new_summary = response[0].strip()

            self._save_user_summary(new_summary)
            return new_summary
        except Exception as e:
            raise Exception(f"update_user_summary :: {e}")

    def _save_user_summary(self, summary):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/user_summary"
            pload = {'datetime': datetime.now().isoformat(
            ), 'session_id': self.session_id, 'summary': summary}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(
                    f"_save_user_summary :: {internal_request.text}")
                return {"error": f"Error while calling background _save_user_summary : {internal_request.text}"}, 400
        except Exception as e:
            raise Exception(f"_save_user_summary :: {e}")
