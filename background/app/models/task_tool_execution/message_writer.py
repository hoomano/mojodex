import os
from datetime import datetime

import requests
from jinja2 import Template

from llm_api.mojodex_background_openai import OpenAIConf
from background_logger import BackgroundLogger

from app import llm, llm_conf


class MessageWriter:
    logger_prefix = "MessageWriter ::"
    tool_result_start_tag, tool_result_end_tag = "<tool_results>", "</tool_results>"

    message_prompt = "/data/prompts/background/task_tool_execution/message_writer/message_prompt.txt"
    writer = llm(llm_conf, label="TASK_TOOL_EXECUTION_MESSAGE_WRITER")

    def __init__(self, title_start_tag, title_end_tag, draft_start_tag, draft_end_tag):
        self.logger = BackgroundLogger(f"{MessageWriter.logger_prefix}")
        self.logger.debug(f"__init__")
        self.title_start_tag = title_start_tag
        self.title_end_tag = title_end_tag
        self.draft_start_tag = draft_start_tag
        self.draft_end_tag = draft_end_tag

    def write_message(self, knowledge_collector, task, tool, task_tool_association, conversation, results,
                      language, user_id, session_id, user_task_execution_pk):
        try:
            self.logger.info(f"write_and_send_message")
            message_text = self._write_message(knowledge_collector, task, tool, task_tool_association, conversation,
                                               results, language, user_id, user_task_execution_pk)
            message = {"text": message_text,
                       "text_with_tags": f"{MessageWriter.tool_result_start_tag}{message_text}{MessageWriter.tool_result_end_tag}"}
            return message
        except Exception as e:
            raise Exception(
                f"{self.logger_prefix} write_and_send_message :: {e}")

    def _write_message(self, knowledge_collector, task, tool, task_tool_association, conversation, results, language,
                       user_id, user_task_execution_pk):
        try:
            self.logger.info(f"_write_message")
            with open(MessageWriter.message_prompt, "r") as f:
                template = Template(f.read())
                prompt = template.render(mojo_knowledge=knowledge_collector.mojo_knowledge,
                                         global_context=knowledge_collector.global_context,
                                         username=knowledge_collector.user_name,
                                         task=task,
                                         title_start_tag=self.title_start_tag,
                                         title_end_tag=self.title_end_tag,
                                         draft_start_tag=self.draft_start_tag,
                                         draft_end_tag=self.draft_end_tag,
                                         tool=tool,
                                         task_tool_association=task_tool_association,
                                         conversation=conversation,
                                         results=results,
                                         language=language
                                         )

            messages = [{"role": "system", "content": prompt}]
            responses = MessageWriter.writer.invoke(messages, user_id,
                                                  temperature=0,
                                                  max_tokens=3000,
                                                  user_task_execution_pk=user_task_execution_pk,
                                                  task_name_for_system=task.name_for_system,
                                                  )

            response = responses[0].strip()
            return response
        except Exception as e:
            raise Exception(f"_write_message :: {e}")
