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


class TaskToolExecutionCortex:
    logger_prefix = "TaskToolExecutionCortex"
    title_start_tag, title_end_tag = "<title>", "</title>"
    draft_start_tag, draft_end_tag = "<draft>", "</draft>"
    available_tools = [GoogleSearchTool, InternalMemoryTool]

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
                result = self._run_tool(gantry_logger)
            except Exception as e:
                self.logger.error(f"execute_task_tool :: {e}")
                result = None # go on supposing Mojo has not found anything

            message_writer = MessageWriter(self.title_start_tag, self.title_end_tag, self.draft_start_tag, self.draft_end_tag)
            mojo_message = message_writer.write_and_send_message(self.knowledge_collector, self.task, self.tool, self.task_tool,
                                                                 self.conversation, result, self.language, self.user.user_id,
                                                                 self.user_task_execution.session_id, self.user_task_execution.user_task_execution_pk)
            try:
                gantry_logger.end({"response": mojo_message['text']})
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
            tool = tool_class(self.user.user_id, self.task_tool_execution_pk, self.user_task_execution.user_task_execution_pk, self.task.name_for_system, gantry_logger, self.conversation_list) # instanciate the tool
            tool_execution_context = self._get_tool_execution_context()
            result = tool.activate(tool_execution_context, self.task_tool.usage_description, self.knowledge_collector, user_id=self.user.user_id)
            return result
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
        user_task_inputs=[{k: input[k] for k in
                                 ("input_name", "description_for_system", "type", "value")} for input in
                                self.user_task_execution.json_input_values if input["value"]]

        with open(TaskToolExecutionCortex.tool_execution_context_template, "r") as f:
            template = Template(f.read())
            tool_execution_context = template.render(task=self.task,
                                                            tool=self.tool,
                                                     task_tool_association=self.task_tool,
                                                            conversation=self.conversation,
                                                            user_task_inputs=user_task_inputs,
                                                            title_start_tag=TaskToolExecutionCortex.title_start_tag,
                                                            title_end_tag=TaskToolExecutionCortex.title_end_tag,
                                                            draft_start_tag=TaskToolExecutionCortex.draft_start_tag,
                                                            draft_end_tag=TaskToolExecutionCortex.draft_end_tag)
        return tool_execution_context

