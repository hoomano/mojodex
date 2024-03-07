from azure_openai_conf import AzureOpenAIConf
from models.session.assistant_message_generator import AssistantMessageGenerator
from models.llm_calls.mojodex_openai import MojodexOpenAI
from models.produced_text_manager import ProducedTextManager
from models.session.assistant_response_generator import AssistantResponseGenerator, ChatContext, ChatState
from abc import ABC, abstractmethod
from app import placeholder_generator, db
from db_models import *
from sqlalchemy import or_, func
from models.knowledge.knowledge_manager import KnowledgeManager
from models.tasks.task_executor import TaskExecutor
from models.tasks.task_inputs_manager import TaskInputsManager
from models.tasks.task_tool_manager import TaskToolManager
from jinja2 import Template

class TaskEnabledChatState(ChatState):

    def __init__(self, running_user_task_execution_pk):
        super().__init__()
        if running_user_task_execution_pk:
            self._set_task_and_execution(running_user_task_execution_pk)
        else:
            self.running_task = None
            self.running_user_task_execution = None
            self.running_task_displayed_data = None
            self.running_user_task = None

    def get_produced_text_done(self):
        try:
            if self.running_user_task_execution is None:
                return False
            return db.session.query(MdProducedText).filter(
                MdProducedText.user_task_execution_fk == self.running_user_task_execution.user_task_execution_pk).count() > 1
        except Exception as e:
            raise Exception(f"get_produced_text_done :: {e}")
        
    def _set_task_and_execution(self, user_task_execution_pk):
        self.running_task, self.running_user_task, self.running_user_task_execution = db.session.query(MdTask, MdUserTask, MdUserTaskExecution) \
            .join(MdUserTask, MdUserTask.task_fk == MdTask.task_pk) \
            .join(MdUserTaskExecution, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
            .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
            .first()
        
        self.running_task_displayed_data = (
            db.session
            .query(
                MdTaskDisplayedData,
            )
            .join(MdTask,
                  MdTask.task_pk == MdTaskDisplayedData.task_fk)
            .join(
                MdUserTask, 
                MdUserTask.task_fk == MdTask.task_pk
            )
            .join(
                MdUser, 
                MdUser.user_id == MdUserTask.user_id
            )
            .filter(
                MdTaskDisplayedData.task_fk == self.running_task.task_pk
            )
            .filter(
                or_(
                    MdTaskDisplayedData.language_code == MdUser.language_code,
                    MdTaskDisplayedData.language_code == 'en'
                )
            )
            .order_by(
                # Sort by user's language first otherwise by english
                func.nullif(MdTaskDisplayedData.language_code, 'en').asc()
            )
            .first())


class TaskEnabledChatContext(ChatContext):

    def __init__(self, user, session_id, origin, user_messages_are_audio, chat_state):
        super().__init__(user, session_id, origin, user_messages_are_audio, chat_state)
    
class TaskEnabledAssistantResponseGenerator(AssistantResponseGenerator, ABC):
    task_specific_instructions_prompt = "/data/prompts/tasks/task_specific_instructions.txt"
    #prompt_template_path = "/data/prompts/mega_mega_prompt.txt"
    message_generator = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "CHAT", AzureOpenAIConf.azure_gpt4_32_conf)

    def __init__(self, prompt_template_path, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, chat_context, llm_call_temperature):
        super().__init__(prompt_template_path, self.message_generator, chat_context, use_message_placeholder, use_draft_placeholder, tag_proper_nouns, llm_call_temperature)
        self.mojo_message_token_stream_callback = mojo_message_token_stream_callback
        self.draft_token_stream_callback = draft_token_stream_callback
        self.task_input_manager = TaskInputsManager(chat_context.session_id)
        self.task_tool_manager = TaskToolManager(chat_context.session_id)
        self.task_executor = TaskExecutor(chat_context.session_id, chat_context.user_id)

    # getter for running_task
    @property
    def running_task(self):
        return self.chat_context.state.running_task
    
    @property
    def running_user_task_execution(self):
        return self.chat_context.state.running_user_task_execution
    
    @property
    def running_task_displayed_data(self):
        return self.chat_context.state.running_task_displayed_data
    
    def _handle_placeholder(self):
        try:
            placeholder = None
            if self.use_message_placeholder:
                placeholder = self._get_message_placeholder()
            elif self.use_draft_placeholder:
                placeholder = self._get_task_execution_placeholder()
            if placeholder:
                placeholder_generator.stream(placeholder, self._token_stream_callback)
                return placeholder
        except Exception as e:
            raise Exception(f"_handle_placeholder :: {e}")
        

    def _render_prompt_from_template(self):
        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()
            user_company_knowledge = KnowledgeManager.get_user_company_knowledge(self.chat_context.user_id)
            available_user_tasks = self.__get_available_user_tasks()
            task_specific_instructions = self.__get_specific_task_instructions(self.running_task) if self.running_task else None
            produced_text_done = self.chat_context.state.get_produced_text_done()

            return self.prompt_template.render(mojo_knowledge=mojo_knowledge,
                                                    global_context=global_context,
                                                    username=self.chat_context.username,
                                                    user_company_knowledge=user_company_knowledge,
                                                    general_chat = self.chat_context.origin=='home_chat',
                                                    tasks = available_user_tasks,
                                                    running_task=self.running_task,
                                                    task_specific_instructions=task_specific_instructions,
                                                    produced_text_done=produced_text_done,
                                                    audio_message=self.chat_context.user_messages_are_audio,
                                                    tag_proper_nouns=self.tag_proper_nouns
                                                    )
        except Exception as e:
            raise Exception(f"_render_prompt_from_template :: {e}")

    def _manage_response_task_tags(self, response):
        try:
            if TaskInputsManager.ask_user_input_start_tag in response:
                return self.task_input_manager.manage_ask_input_text(response)
            if TaskToolManager.tool_usage_start_tag in response:
                return self.task_tool_manager.manage_tool_usage_text(response,
                                                                        self.running_user_task_execution.user_task_execution_pk,
                                                                        self._get_task_tools_json(self.running_task))
            elif TaskExecutor.execution_start_tag in response:
                # take the text between <execution> and </execution>
                print(f"TaskExecutor.execution_start_tag in response")
                return self.task_executor.manage_execution_text(execution_text=response, task=self.running_task, task_displayed_data=self.running_task_displayed_data,
                                                                user_task_execution_pk=self.running_user_task_execution.user_task_execution_pk,
                                                                use_draft_placeholder=self.use_draft_placeholder)
            return {"text": response}
        except Exception as e:
            raise Exception(f"_manage_response_task_tags :: {e}")
    
    def _manage_response_tags(self, response):
        return self._manage_response_task_tags(response)

    @abstractmethod
    def _get_message_placeholder(self):
        pass

    ### SPECIFIC METHODS FOR TASKS ###
    def _get_task_execution_placeholder(self):
        return f"{TaskExecutor.execution_start_tag}" \
                        f"{ProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{ProducedTextManager.title_end_tag}" \
                        f"{ProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{ProducedTextManager.title_end_tag}" \
                        f"{TaskExecutor.execution_end_tag}"

    def _get_task_input_placeholder(self):
        return f"{TaskInputsManager.user_message_start_tag}{placeholder_generator.mojo_message}{TaskInputsManager.user_message_end_tag}"
    
    def __get_available_user_tasks(self):
        try:
            user_tasks = db.session.query(MdTask).\
                join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk).\
                filter(MdUserTask.user_id == self.chat_context.user_id).\
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
                                    title_start_tag=ProducedTextManager.title_start_tag,
                                    title_end_tag=ProducedTextManager.title_end_tag,
                                    draft_start_tag=ProducedTextManager.draft_start_tag,
                                    draft_end_tag=ProducedTextManager.draft_end_tag,
                                    task_tool_associations=self.__get_task_tools_json(task),
                                    user_task_inputs=self.__get_running_user_task_execution_inputs()
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
            raise Exception(f"_get_task_tools_json :: {e}")

    def __get_running_user_task_execution_inputs(self):
        try:
            user_task_inputs = [{k: input[k] for k in
                                 ("input_name", "description_for_system", "type", "value")} for input in
                                self.running_user_task_execution.json_input_values if input["value"]]

            if len(user_task_inputs) == 0:
                user_task_inputs = None

            return user_task_inputs
        except Exception as e:
            raise Exception(f"__get_running_user_task_execution_inputs :: {e}")
        
    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()
        if not partial_text.lower().startswith("<"):
           self._stream_no_tag_text(partial_text)
        else:            
            self._stream_task_tokens(partial_text)

    def _stream_no_tag_text(self, partial_text):
        if self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(partial_text)

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

        elif TaskExecutor.execution_start_tag in partial_text:
            # take the text between <execution> and </execution>
            text = AssistantMessageGenerator.remove_tags_from_text(partial_text, TaskExecutor.execution_start_tag,
                                                        TaskExecutor.execution_end_tag)
            self.draft_token_stream_callback(text)
