from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from abc import ABC, abstractmethod
from app import placeholder_generator, db

from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager

from models.session.execution_manager import ExecutionManager

from models.session.assistant_message_generators.task_enabled_assistant_response_generator import \
    TaskEnabledAssistantResponseGenerator
from mojodex_core.entities import *
from models.knowledge.knowledge_manager import KnowledgeManager
from models.tasks.task_executor import TaskExecutor
from models.tasks.task_inputs_manager import TaskInputsManager
from models.tasks.task_tool_manager import TaskToolManager
from jinja2 import Template


class InstructTaskEnabledAssistantResponseGenerator(TaskEnabledAssistantResponseGenerator, ABC):
    logger_prefix = "TaskEnabledAssistantResponseGenerator :: "

    # TODO: with @kelly check how to mpt-ize this
    task_specific_instructions_prompt = "mojodex_core/prompts/tasks/task_specific_instructions.txt"

    def __init__(self, prompt_template_path, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, chat_context, llm_call_temperature):
        try:
            super().__init__(prompt_template_path, mojo_message_token_stream_callback, use_message_placeholder, tag_proper_nouns, chat_context, llm_call_temperature)
            self.draft_token_stream_callback = draft_token_stream_callback
            self.use_draft_placeholder = use_draft_placeholder
            self.task_input_manager = TaskInputsManager(chat_context.session_id)
            self.task_tool_manager = TaskToolManager(chat_context.session_id)
            self.execution_manager = ExecutionManager(chat_context.session_id)
            self.task_executor = TaskExecutor(chat_context.session_id, chat_context.user_id)
        except Exception as e:
            raise Exception(f"{self.logger_prefix} __init__ :: {e}")

    
    def _handle_placeholder(self):
        try:
            placeholder = None
            if self.use_message_placeholder:
                placeholder = self._get_message_placeholder()
            elif self.use_draft_placeholder:
                placeholder = self._get_task_execution_placeholder()
            if placeholder:
                placeholder_generator.stream(placeholder, self._token_callback)
                return placeholder
        except Exception as e:
            raise Exception(f"{InstructTaskEnabledAssistantResponseGenerator.logger_prefix} _handle_placeholder :: {e}")

    def _render_prompt_from_template(self):
        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()
            user_company_knowledge = KnowledgeManager.get_user_company_knowledge(self.context.user_id)
            available_user_tasks = self.__get_available_user_instruct_tasks()
            task_specific_instructions = self.__get_specific_task_instructions(self.running_task) if self.running_task else None
            produced_text_done = self.context.state.get_produced_text_done()

            return self.prompt_template.render(mojo_knowledge=mojo_knowledge,
                                                    global_context=global_context,
                                                    username=self.context.username,
                                                    user_company_knowledge=user_company_knowledge,
                                                    tasks = available_user_tasks,
                                                    running_task=self.running_task,
                                                    task_specific_instructions=task_specific_instructions,
                                                    produced_text_done=produced_text_done,
                                                    audio_message=self.context.user_messages_are_audio,
                                                    tag_proper_nouns=self.tag_proper_nouns,
                                                    language=None
                                                    )
        except Exception as e:
            raise Exception(f"{InstructTaskEnabledAssistantResponseGenerator.logger_prefix} _render_prompt_from_template :: {e}")

    def _manage_response_task_tags(self, response):
        try:
            if TaskInputsManager.ask_user_input_start_tag in response:
                return self.task_input_manager.manage_ask_input_text(response)
            if TaskToolManager.tool_usage_start_tag in response:
                return self.task_tool_manager.manage_tool_usage_text(response,
                                                                        self.running_user_task_execution.user_task_execution_pk,
                                                                        self._get_task_tools_json(self.running_task))
            return {"text": response}
        except Exception as e:
            raise Exception(f"_manage_response_task_tags :: {e}")

    def _manage_execution_tags(self, response):
        try:
            if ExecutionManager.execution_start_tag in response:
                return self.execution_manager.manage_execution_text(response, self.running_task, self.running_task_displayed_data,
                                          self.running_user_task_execution, self.task_executor,
                                          use_draft_placeholder=self.use_draft_placeholder)
        except Exception as e:
            raise Exception(f"_manage_execution_tags :: {e}")
    
    def _manage_response_tags(self, response):
        execution = self._manage_execution_tags(response)
        if execution:
            return execution
        return self._manage_response_task_tags(response)

    @abstractmethod
    def _get_message_placeholder(self):
        raise NotImplementedError


    ### SPECIFIC METHODS FOR TASKS ###
    def _get_task_execution_placeholder(self):
        return f"{ExecutionManager.execution_start_tag}" \
                        f"{InstructTaskProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{InstructTaskProducedTextManager.title_end_tag}" \
                        f"{InstructTaskProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{InstructTaskProducedTextManager.draft_end_tag}" \
                        f"{ExecutionManager.execution_end_tag}"

    def _get_task_input_placeholder(self):
        return f"{TaskInputsManager.user_message_start_tag}{placeholder_generator.mojo_message}{TaskInputsManager.user_message_end_tag}"
    
    def __get_available_user_instruct_tasks(self):
        try:
            user_tasks = db.session.query(MdTask).\
                join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk).\
                filter(MdUserTask.user_id == self.context.user_id).\
                filter(MdTask.type == "instruct").\
                filter(MdUserTask.enabled==True).all()
            return [{
                'task_pk': task.task_pk,
                'icon': task.icon,
                'name_for_system': task.name_for_system,
                'description': task.definition_for_system
            } for task in user_tasks]
        except Exception as e:
            raise Exception(f"__get_available_user_tasks :: {e}")
    
    def __get_specific_task_instructions(self, task):
        try:
            with open(self.task_specific_instructions_prompt, "r") as f:
                template = Template(f.read())
                return template.render(task=task,
                                    title_start_tag=InstructTaskProducedTextManager.title_start_tag,
                                    title_end_tag=InstructTaskProducedTextManager.title_end_tag,
                                    draft_start_tag=InstructTaskProducedTextManager.draft_start_tag,
                                    draft_end_tag=InstructTaskProducedTextManager.draft_end_tag,
                                    task_tool_associations=self.__get_task_tools_json(task),
                                    user_task_inputs=self._get_running_user_task_execution_inputs()
                                    )
        except Exception as e:
            raise Exception(f"__get_running_task_instructions :: {e}")
        
    def __get_task_tools_json(self, task):
        try:
            if task is None:
                return None
            task_tool_associations = db.session.query(MdTaskToolAssociation, MdTool)\
                .join(MdTool, MdTool.tool_pk == MdTaskToolAssociation.tool_fk)\
                .filter(MdTaskToolAssociation.task_fk == task.task_pk).all()
            return [{"task_tool_association_pk": task_tool_association.task_tool_association_pk,
                     "usage_description": task_tool_association.usage_description,
                     "tool_name": tool.name}
                    for task_tool_association, tool in task_tool_associations]
        except Exception as e:
            raise Exception(f"__get_task_tools_json :: {e}")

    def _stream_task_tokens(self, partial_text):
        text=None
        if TaskInputsManager.ask_user_input_start_tag in partial_text:
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, TaskInputsManager.ask_user_input_start_tag,
                                                        TaskInputsManager.ask_user_input_end_tag)
        elif TaskToolManager.tool_usage_start_tag in partial_text:
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, TaskToolManager.tool_usage_start_tag,
                                                        TaskToolManager.tool_usage_end_tag)
        if text and self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(text)

        elif ExecutionManager.execution_start_tag in partial_text:
            # take the text between <execution> and </execution>
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, ExecutionManager.execution_start_tag,
                                                        ExecutionManager.execution_end_tag)
            self.draft_token_stream_callback(text)
