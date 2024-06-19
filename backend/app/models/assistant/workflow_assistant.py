from models.knowledge.knowledge_manager import KnowledgeManager
from models.assistant.chat_assistant import ChatAssistant
from app import placeholder_generator

from models.tasks.workflows.workflow_manager import WorkflowManager
from mojodex_core.llm_engine.mpt import MPT


class WorkflowAssistant(ChatAssistant):
    mpt_file = "instructions/workflow_step_run.mpt"

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder,
                 use_draft_placeholder,
                 tag_proper_nouns, user_messages_are_audio, running_user_task_execution, db_session):
        try:

            super().__init__(mojo_message_token_stream_callback, draft_token_stream_callback,
                             tag_proper_nouns, user_messages_are_audio, db_session)

            self.workflow_execution = running_user_task_execution
            self.use_message_placeholder = use_message_placeholder
            self.use_draft_placeholder = use_draft_placeholder

            self.workflow_manager = WorkflowManager()

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    def generate_message(self):
        try:
            # If placeholder is required, return it
            if self.use_message_placeholder or self.use_draft_placeholder:
                return self._handle_placeholder()

            # Call LLM
            llm_output = self._call_llm(self.workflow_execution.session.conversation,
                                        self.workflow_execution.user.user_id,
                                        self.workflow_execution.session.session_id,
                                        user_task_execution_pk=self.workflow_execution.user_task_execution_pk,
                                        task_name_for_system=self.workflow_execution.task.name_for_system)

            # Handle LLM output
            if llm_output:
                message = self._handle_llm_output(llm_output)
                message['user_task_execution_pk'] = self.workflow_execution.user_task_execution_pk
                return message

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: generate_message :: {e}")

    def _handle_placeholder(self):
        try:
            placeholder = None
            # TODO: change message/draft make no sense. Replace with a placeholder value = "instruction" or "clarification"
            if self.use_message_placeholder:
                placeholder = self.workflow_manager.workflow_step_clarification_manager
            elif self.use_draft_placeholder:
                placeholder = self.workflow_manager.workflow_step_instruction_manager
            if placeholder:
                placeholder_generator.stream(placeholder, self._token_callback)
                return placeholder
        except Exception as e:
            raise Exception(f"_handle_placeholder :: {e}")

    @property
    def _mpt(self):
        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()

            return MPT(self.mpt_file, mojo_knowledge=mojo_knowledge,
                       global_context=global_context,
                       username=self.workflow_execution.user.name,
                       user_company_knowledge=self.workflow_execution.user.company_description,
                       infos_to_extract=self.workflow_execution.task.infos_to_extract,
                       workflow=self.workflow_execution.task,
                       user_workflow_inputs=self.workflow_execution.json_input_values,
                       audio_message=self.user_messages_are_audio,
                       tag_proper_nouns=self.tag_proper_nouns)
        except Exception as e:
            raise Exception(f"_mpt :: {e}")

    @property
    def requires_vision_llm(self):
        return self.workflow_execution.has_images_inputs

    @property
    def input_images(self):
        return self.workflow_execution.images_input_names

    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()

        # if text contains no tag
        if not partial_text.lower().startswith("<") and self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(partial_text)

        else:
            self.workflow_manager.manage_task_stream(partial_text, self.mojo_message_token_stream_callback)

    def _manage_response_tags(self, response):
        try:
            return self.workflow_manager.manage_response_task_tags(response, self.workflow_execution)
        except Exception as e:
            raise Exception(f"_manage_response_tags :: {e}")
