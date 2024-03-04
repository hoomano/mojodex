# This is abstract class for all tools
import json
import os
from abc import ABC, abstractmethod
from datetime import datetime

import requests
from jinja2 import Template
from llm_calls.mojodex_openai import MojodexOpenAI
from llm_calls.json_loader import json_decode_retry
from app import on_json_error
from azure_openai_conf import AzureOpenAIConf


class Tool(ABC):
    task_tool_query_url = "task_tool_query"

    params_generator_prompt = "/data/prompts/background/task_tool_execution/generate_tool_params.txt"
    json_params_generator = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "TOOL_PARAMS_GENERATOR")

    def __init__(self, name, tool_specifications, task_tool_execution_pk, logger, user_id, user_task_execution_pk,
                 task_name_for_system, n_total_usages):
        self.name = name
        self.specifications = tool_specifications
        self.logger = logger
        self.user_task_execution_pk = user_task_execution_pk
        self.task_tool_execution_pk = task_tool_execution_pk
        self.task_name_for_system = task_name_for_system
        self.user_id = user_id
        self.n_total_usages = n_total_usages # n_total_usages is the number of times the tool will be used (= query generated + result retrieved)

    @json_decode_retry(retries=3, required_keys=None, on_json_error=on_json_error)
    def __generate_tool_query(self, mojo_knowledge, global_context, user_name, user_company_knowledge,
                             tool_execution_context, usage_description, previous_results, n_total_usages, user_id):
        """Return a json with the parameters for the tool."""
        try:
            with open(Tool.params_generator_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(mojo_knowledge=mojo_knowledge,
                                         global_context=global_context,
                                         username=user_name,
                                         user_company_knowledge=user_company_knowledge,
                                         tool_execution_context=tool_execution_context,
                                         n_total_usages=n_total_usages,
                                         current_usage_index=len(previous_results) + 1,
                                         previous_results=previous_results,
                                         tool_specifications=self.specifications,
                                         tool_name=self.name,
                                         usage_description=usage_description,
                                         )

                messages = [{"role": "system", "content": prompt}]

                results = Tool.json_params_generator.chat(messages, user_id,
                                                          temperature=0,
                                                          max_tokens=2000,
                                                          json_format=True,
                                                          user_task_execution_pk=self.user_task_execution_pk,
                                                          task_name_for_system=self.task_name_for_system)
                result = results[0]

                return result

        except Exception as e:
            raise Exception(f"__generate_tool_query :: {e}")

    def activate(self, tool_execution_context, usage_description, knowledge_collector, user_id):
        try:
            queries, results = [], []
            for usage in range(self.n_total_usages):
                json_params = self.__generate_tool_query(
                    knowledge_collector.mojo_knowledge,
                    knowledge_collector.global_context,
                    knowledge_collector.user_name,
                    knowledge_collector.user_company_knowledge,
                    tool_execution_context, usage_description, queries, self.n_total_usages, user_id)

                task_tool_query_pk = self.__save_query_to_db(json_params)
                result = self.run_tool(json_params, tool_execution_context, usage_description, knowledge_collector)
                self.logger.debug(f"activate :: result {result}")
                self.__save_result_to_db(task_tool_query_pk, result)
                json_params.update({"result": result})
                queries.append(json_params)  # queries = [{'query': '', 'result': ''}, ...]
                if result:
                    results.append(result) # results = [result1, result2, ...]
            # if results is empty, it means that the tool did not return any result
            return queries, results
        except Exception as e:
            raise Exception(f"activate :: {e}")

    @abstractmethod
    def run_tool(self, json_params, tool_execution_context, usage_description, knowledge_collector):
        pass

    def generate_produced_text(self):
        # By default, a tool does not directly create a produced text
        # Next steps will generate a message addressed to the user to ask for confirmation before writing the produced text
        return None

    def __save_query_to_db(self, query):
        try:
            self.logger.debug(f"__save_query_to_db: {query}")
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/{Tool.task_tool_query_url}"
            # Save follow-ups in db => send to mojodex-backend
            pload = {'datetime': datetime.now().isoformat(), 'query': query,
                     'task_tool_execution_fk': self.task_tool_execution_pk}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(str(internal_request.json()))
            return internal_request.json()["task_tool_query_pk"]
        except Exception as e:
            raise Exception(f"__save_to_db: {e}")

    def __save_result_to_db(self, task_tool_query_pk, result):
        try:
            self.logger.debug(f"__save_result_to_db: {result}")
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/{Tool.task_tool_query_url}"
            # Save follow-ups in db => send to mojodex-backend
            pload = {'datetime': datetime.now().isoformat(), 'result': result,
                     'task_tool_query_pk': task_tool_query_pk}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(str(internal_request.json()))
        except Exception as e:
            raise Exception(f"__save_to_db: {e}")
