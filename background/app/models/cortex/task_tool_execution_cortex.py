import os

from app import db, language_retriever, conversation_retriever
from mojodex_core.entities import *
from background_logger import BackgroundLogger
from gantry.logger.eval_logger import EvalLogger
from jinja2 import Template
from models.task_tool_execution.tools.google_search import GoogleSearchTool
from models.task_tool_execution.tools.internal_memory import InternalMemoryTool
from models.knowledge.knowledge_collector import KnowledgeCollector

from models.task_tool_execution.message_writer import MessageWriter

from models.events.task_tool_execution_notifications_generator import TaskToolExecutionNotificationsGenerator

from datetime import datetime
import requests

class TaskToolExecutionCortex:
    logger_prefix = "TaskToolExecutionCortex"
    title_start_tag, title_end_tag = "<title>", "</title>"
    draft_start_tag, draft_end_tag = "<draft>", "</draft>"
    execution_start_tag, execution_end_tag = "<execution>", "</execution>"
    available_tools = [GoogleSearchTool, InternalMemoryTool]

    # TODO: with @kelly check how to mpt-ize this
    tool_execution_context_template = "/data/prompts/background/task_tool_execution/tool_execution_context_template.txt"

    def __init__(self, task_tool_execution):
        try:
            self.logger = BackgroundLogger(
                f"{TaskToolExecutionCortex.logger_prefix} - task_tool_execution_pk {task_tool_execution.task_tool_execution_pk}")
            self.logger.debug(f"__init__")
            self.task_tool_execution_pk = task_tool_execution.task_tool_execution_pk
            self.task_tool, self.tool, self.task, self.user_task_execution, self.session, self.user = self._get_task_tool(task_tool_execution)
            if self.session.language:
                self.language = self.session.language
            elif self.user.language_code:
                self.language = self.user.language_code
            else:
                self.language = "en" # this is just a safety net but should never happen
            self.conversation = conversation_retriever.get_conversation_as_string(self.user_task_execution.session_id, with_tags=False)
            self.conversation_list = conversation_retriever.get_conversation_as_list(self.user_task_execution.session_id, with_tags=False)
            self.knowledge_collector = KnowledgeCollector(self.user.name, self.user.timezone_offset, self.user.summary, self.user.company_description, self.user.goal)
        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")

    def execute_task_tool(self):
        try:
            self.logger.debug(f"execute_task_tool")
            gantry_logger = EvalLogger("/data/internal_memory_data.jsonl")
            try:
                tool_queries, produced_text = self._run_tool(gantry_logger)
            except Exception as e:
                self.logger.error(f"execute_task_tool :: {e}")
                tool_queries, produced_text = None, None # go on supposing Mojo has not found anything

            if produced_text:
                title, production = produced_text['title'], produced_text['production']
                produced_text_pk, produced_text_version_pk = self.__save_produced_text_to_db(title, production)
            else:
                message_writer = MessageWriter(self.title_start_tag, self.title_end_tag, self.draft_start_tag,
                                               self.draft_end_tag)
                mojo_message = message_writer.write_message(self.knowledge_collector, self.task, self.tool,
                                                            self.task_tool,
                                                            self.conversation, tool_queries, self.language,
                                                            self.user.user_id,
                                                            self.user_task_execution.user_task_execution_pk)

                # add user_task_execution_pk to the message
                mojo_message["user_task_execution_pk"] = self.user_task_execution.user_task_execution_pk
                self.__save_message_to_db(mojo_message)
            try:
                gantry_logger.end({"response": f"{title}\n{production}" if produced_text else mojo_message['text']})
                gantry_logger.close()
            except Exception as e:
                self.logger.error(f"execute_task_tool :: gantry_logger end:: {e}")
            push_notification = 'FIREBASE_PROJECT_ID' in os.environ and os.environ['FIREBASE_PROJECT_ID']
            if push_notification:
                notification_generator = TaskToolExecutionNotificationsGenerator()
                notification_generator.generate_events(self.user.user_id, self.knowledge_collector, self.task.name_for_system,
                                                      self.task.definition_for_system, self.user_task_execution.title, self.user_task_execution.summary,
                                                      self.tool.name, self.task_tool, result, self.language, self.user_task_execution.user_task_execution_pk)
        except Exception as e:
            self.logger.error(f"execute_task_tool: {e}")

    def _run_tool(self, gantry_logger):
        try:
            tool_class = self._get_tool(self.tool.name)
            if tool_class is None:
                raise Exception(f"Tool {self.tool.name} not found")
            # TODO: I think n_total_usages might be dependent on the task_tool_association too
            tool_execution_context = self._get_tool_execution_context()
            tool = tool_class(self.user.user_id, self.task_tool_execution_pk,
                              self.user_task_execution.user_task_execution_pk, self.task.name_for_system,
                              user_task_inputs=self.user_task_inputs, gantry_logger=gantry_logger,
                              conversation_list=self.conversation_list)  # instanciate the tool

            tool_queries, tool_results = tool.activate(tool_execution_context, self.task_tool.usage_description,
                                                       self.knowledge_collector, user_id=self.user.user_id)
            produced_text = tool.generate_produced_text() if tool_results else None

            return tool_queries, produced_text
        except Exception as e:
            raise Exception(f"_run_tool :: {e}")

    def _get_tool(self, tool_name):
        return next((tool for tool in TaskToolExecutionCortex.available_tools if tool.name == tool_name), None)

    def _get_task_tool(self, task_tool_execution):
        return db.session.query(MdTaskToolAssociation, MdTool, MdTask, MdUserTaskExecution, MdSession, MdUser)\
            .join(MdTool, MdTool.tool_pk == MdTaskToolAssociation.tool_fk)\
            .join(MdTask, MdTask.task_pk == MdTaskToolAssociation.task_fk)\
            .join(MdUserTaskExecution, MdUserTaskExecution.user_task_execution_pk == task_tool_execution.user_task_execution_fk)\
            .join(MdSession, MdSession.session_id == MdUserTaskExecution.session_id)\
            .join(MdUser, MdUser.user_id == MdSession.user_id)\
            .filter(MdTaskToolAssociation.task_tool_association_pk == task_tool_execution.task_tool_association_fk)\
            .first()

    def _get_tool_execution_context(self):

        # Following is only useful for webapp form
        self.user_task_inputs=[{k: input[k] for k in
                                 ("input_name", "description_for_system", "type", "value")} for input in
                                self.user_task_execution.json_input_values if input["value"]]

        with open(TaskToolExecutionCortex.tool_execution_context_template, "r") as f:
            template = Template(f.read())
            tool_execution_context = template.render(task=self.task,
                                                            tool=self.tool,
                                                     task_tool_association=self.task_tool,
                                                            conversation=self.conversation,
                                                            user_task_inputs=self.user_task_inputs,
                                                            title_start_tag=TaskToolExecutionCortex.title_start_tag,
                                                            title_end_tag=TaskToolExecutionCortex.title_end_tag,
                                                            draft_start_tag=TaskToolExecutionCortex.draft_start_tag,
                                                            draft_end_tag=TaskToolExecutionCortex.draft_end_tag)
        return tool_execution_context

    def __save_message_to_db(self, message):
        try:
            # Save in db => send to mojodex-backend
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/mojo_message"
            pload = {'datetime': datetime.now().isoformat(), "message": message,
                     "session_id": self.user_task_execution.session_id}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.put(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(str(internal_request.json()))
        except Exception as e:
            raise Exception(f"__save_message_to_db: {e}")

    def __save_produced_text_to_db(self, title, production):
        try:
            # Save in db => send to mojodex-backend
            uri = f"{os.environ['MOJODEX_BACKEND_URI']}/produced_text"
            pload = {'datetime': datetime.now().isoformat(), "production": production, "title": title,
                     "session_id": self.user_task_execution.session_id, "user_id": self.user.user_id,
                     "user_task_execution_pk": self.user_task_execution.user_task_execution_pk}
            headers = {'Authorization': os.environ['MOJODEX_BACKGROUND_SECRET'], 'Content-Type': 'application/json'}
            internal_request = requests.post(uri, json=pload, headers=headers)
            if internal_request.status_code != 200:
                raise Exception(str(internal_request.json()))
            return internal_request.json()["produced_text_pk"], internal_request.json()["produced_text_version_pk"]
        except Exception as e:
            raise Exception(f"__save_produced_text_to_db: {e}")