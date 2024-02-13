import json
import os
from datetime import datetime

import requests
from background_logger import BackgroundLogger

from azure_openai_conf import AzureOpenAIConf
from jinja2 import Template
from llm_calls.mojodex_openai import MojodexOpenAI
from llm_calls.json_loader import json_decode_retry
from app import on_json_error

class UserPreferencesManager:
    logger_prefix = "UserPreferencesManager"

    preferences_extractor_prompt = "/data/prompts/background/user_preferences/extract.txt"
    preferences_concatenator_prompt = "/data/prompts/background/user_preferences/concatenate.txt"
    preferences_extractor = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "EXTRACT_USER_PREFERENCES")
    preferences_concatenator = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "CONCATENATE_USER_PREFERENCES")

    def __init__(self, user_id, username, knowledge_collector):
        try:
            self.logger = BackgroundLogger(f"{UserPreferencesManager.logger_prefix} - user_id {user_id}")
            self.user_id = user_id
            self.username = username
            self.knowledge_collector = knowledge_collector
        except Exception as e:
            self.logger.error(f"__init__ :: {e}")

    def update(self, task_name, task_definition, task_input_values, user_messages_conversation, existing_tags):
        try:
            self.logger.debug(f"update")
            # 1. extract
            extracted_preferences = self.__extract(task_name, task_definition, task_input_values, user_messages_conversation, existing_tags)['user_preferences']

            grouped_by_tag_extracted_preferences = self.__group_extracted_preferences_by_tags(extracted_preferences)

            # 2. for each tag, concat
            for tag, extracted_preferences in grouped_by_tag_extracted_preferences.items():
                concatenated_preferences = self.__concat(tag, extracted_preferences)
                # 3. send to backend
                self.__save_to_db(tag, concatenated_preferences)

        except Exception as e:
            raise Exception(f"{self.logger_prefix} update :: {e}")

    def __group_extracted_preferences_by_tags(self, extracted_preferences):
        """ # extracted_preferences looks like:
         # [{
         #             "tag": "food",
         #             "description": "Does not eat meat, only vegetarian dishes are preferred.",
         #         },
         #         {
         #             "tag": "food",
         #             "description": "Allergic to sesame, almonds, hazelnuts, goat's milk, and sheep's milk.",
         #         },...]
         # This method group those by tags as follow:
         # {
         #     "food": ["Does not eat meat, only vegetarian dishes are preferred.", "Allergic to sesame, almonds, hazelnuts, goat's milk, and sheep's milk."],
         #     "music": ["Likes to listen to jazz and classical music."],
         # }"""
        try:
            self.logger.debug(f"__group_extracted_preferences_by_tags")
            grouped_extracted_preferences = {}
            for preference in extracted_preferences:
                tag = preference['tag'].lower().strip()
                if tag not in grouped_extracted_preferences:
                    grouped_extracted_preferences[tag] = []
                grouped_extracted_preferences[tag].append(preference['description'])

            return grouped_extracted_preferences
        except Exception as e:
            raise Exception(f"{self.logger_prefix} __group_extracted_preferences_by_tags :: {e}")

    @json_decode_retry(retries=3, required_keys=['user_preferences'], on_json_error=on_json_error)
    def __extract(self, task_name, task_definition, task_input_values, user_messages_conversation, existing_tags):
        self.logger.debug(f"__extract")
        try:
            with open(self.preferences_extractor_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(mojo_knowledge=self.knowledge_collector.mojo_knowledge,
                                         global_context=self.knowledge_collector.global_context,
                                         username=self.username,
                                         task_name=task_name,
                                         task_definition=task_definition,
                                         user_task_inputs=task_input_values,
                                         user_messages_conversation=user_messages_conversation,
                                         existing_tags=existing_tags
                                         )
            
                messages = [{"role": "system", "content": prompt}]
            responses = UserPreferencesManager.preferences_extractor.chat(messages, self.user_id, temperature=0,
                                                                          json_format=True,
                                                                          max_tokens=4000)
            
            self.logger.debug(f"__extract done")
            return responses[0]
        except Exception as e:
            raise Exception(f"{self.logger_prefix} __extract :: {e}")

    def __concat(self, tag, extracted_preferences):
        self.logger.debug(f"__concat")
        try:
            known_user_preferences = self.__get_user_preferences(tag)
            with open(self.preferences_concatenator_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(
                    mojo_knowledge=self.knowledge_collector.mojo_knowledge,
                    global_context=self.knowledge_collector.global_context,
                    username=self.username,
                    tag=tag,
                    extracted_preferences=extracted_preferences,
                    user_preferences=known_user_preferences)
                messages = [{"role": "system", "content": prompt}]
            responses = UserPreferencesManager.preferences_concatenator.chat(messages, self.user_id, temperature=0,
                                                                             max_tokens=4000)
            response = responses[0]
            self.logger.debug(f"__concat :: {response}")
            return response
        except Exception as e:
            raise Exception(f"{self.logger_prefix} __concat :: {e}")

    def __get_user_preferences(self, tag):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/user_preference"
            params = {'datetime': datetime.now().isoformat(),
                      'tag': tag,
                      'user_id': self.user_id}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.get(uri, params=params, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(f"{internal_request.status_code} - {internal_request.text}")
            return internal_request.json()['user_preference']
        except Exception as e:
            raise Exception(f"{self.logger_prefix} __get_user_preferences :: {e}")

    def __save_to_db(self, tag, concatenated_preferences):
        try:
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/user_preference"
            pload = {'datetime': datetime.now().isoformat(),
                     'tag': tag, 'user_id': self.user_id, 'user_preference': concatenated_preferences}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(f"{internal_request.status_code} - {internal_request.text}")
        except Exception as e:
            raise Exception(f"{self.logger_prefix} __save_to_db :: {e}")
