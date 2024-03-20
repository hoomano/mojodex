
import os
from datetime import datetime

import requests

from background_logger import BackgroundLogger
from models.task_tool_execution.tools.tool import Tool
from mojodex_core.json_loader import json_decode_retry
from app import on_json_error

from mojodex_core.llm_engine.mpt import MPT


class InternalMemoryTool(Tool):
    logger_prefix = "InternalMemoryTool ::"

    name = "internal_memory"
    tool_specifications = """{
         "query": <query you want to search in past tasks' results. It has to be made of precise keywords.>
        }"""
    n_total_usages = 1

    produced_text_retrieval_url = "retrieve_produced_text"
    information_extractor_mpt_filename = "instructions/internal_memory_information_extractor.mpt"

    def __init__(self, user_id, task_tool_execution_pk, user_task_execution_pk, task_name_for_system, **kwargs):
        self.logger = BackgroundLogger(f"{InternalMemoryTool.logger_prefix}")
        self.logger.debug(f"__init__")
        self.gantry_logger = kwargs.get("gantry_logger")
        self.conversation_list = kwargs.get("conversation_list", [])
        super().__init__(InternalMemoryTool.name, InternalMemoryTool.tool_specifications, task_tool_execution_pk,
                         self.logger, user_id, user_task_execution_pk, task_name_for_system, self.n_total_usages)

    def run_tool(self, json_params, tool_execution_context, usage_description, knowledge_collector):
        try:
            self.logger.debug(f"run_tool with params {json_params}")
            query = json_params["query"]
            self.gantry_logger.start({"query": query, "timestamp": datetime.now(
            ).isoformat(), "chat_history": self.conversation_list})
            self.logger.debug(f"run_tool :: query {query}")
            try:
                nearest_neighbors = self.__get_nearest_neighbors(query)
                self.logger.debug(
                    f"run_tool :: nearest_neighbors: {nearest_neighbors}")
                self.gantry_logger.add_retrieval_step(
                    query,
                    [{"content": str(produced_text)}
                     for produced_text in nearest_neighbors]
                )
            except Exception as e:
                self.logger.error(f"run_tool :: {e}")
                nearest_neighbors = []

            try:
                results = self.__extract_key_points_by_batch(
                    query, nearest_neighbors, tool_execution_context, usage_description, knowledge_collector)
                self.logger.debug(f"run_tool :: results : {results}")
            except Exception as e:
                self.logger.error(f"run_tool :: {e}")
                results = None
            return results
        except Exception as e:
            raise Exception(f"activate :: {e}")

    def __get_nearest_neighbors(self, query, n_max=10, max_distance=0.2):
        try:
            self.logger.debug(f"__get_nearest_neighbors :: query {query}")
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/{InternalMemoryTool.produced_text_retrieval_url}"
            # Save follow-ups in db => send to mojodex-backend
            pload = {'datetime': datetime.now().isoformat(), 'query': query,
                     'n_max': n_max, 'max_distance': max_distance,
                     'user_id': self.user_id, 'user_task_execution_pk': self.user_task_execution_pk,
                     'task_name_for_system': self.task_name_for_system}
            headers = {
                'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.get(uri, params=pload, headers=headers)
            if internal_request.status_code != 200:
                self.logger.error(internal_request.json())
                raise Exception(str(internal_request.json()))

            results = internal_request.json()["retrieved_produced_texts"]
            return results
        except Exception as e:
            raise Exception(f"__get_nearest_neighbors :: {e}")

    @json_decode_retry(retries=3, required_keys=['relevant_results'], on_json_error=on_json_error)
    def __extract_key_points(self, query, results, tool_execution_context, usage_description, knowledge_collector):
        try:
            internal_memory_information_extractor = MPT(InternalMemoryTool.information_extractor_mpt_filename,
                                                        mojo_knowledge=knowledge_collector.mojodex_knowledge,
                                                        global_context=knowledge_collector.localized_context,
                                                        username=knowledge_collector.user_name,
                                                        user_company_knowledge=knowledge_collector.user_company_knowledge,
                                                        tool_execution_context=tool_execution_context,
                                                        tool_name=self.name,
                                                        usage_description=usage_description,
                                                        query=query,
                                                        results=results)

            responses = internal_memory_information_extractor(self.user_id,
                                                              temperature=0, max_tokens=4000,
                                                              json_format=True,
                                                              user_task_execution_pk=self.user_task_execution_pk,
                                                              task_name_for_system=self.task_name_for_system,
                                                              )

            response = responses[0]
            self.gantry_logger.add_llm_step(messages, response,
                                            {"model": InternalMemoryTool.information_extractor.model,
                                             "temperature": 0,
                                             "max_tokens": 4000})
            return response
        except Exception as e:
            raise Exception(f"__extract_key_points: {e}")

    def __extract_key_points_by_batch(self, query, results, tool_execution_context, usage_description, knowledge_collector, step=3):
        try:
            # extract key points of <step> first results, then <step> next results, etc.
            key_points = []
            while len(results) > 0:
                key_points += self.__extract_key_points(
                    query, results[:step], tool_execution_context, usage_description, knowledge_collector)['relevant_results']
                results = results[step:]
            return key_points
        except Exception as e:
            raise Exception(f"__extract_key_points_by_batch: {e}")
