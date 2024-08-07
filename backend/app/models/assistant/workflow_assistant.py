from mojodex_core.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from mojodex_core.knowledge_manager import KnowledgeManager
from models.assistant.chat_assistant import ChatAssistant
from app import placeholder_generator
from models.tasks.workflows.workflow_manager import WorkflowManager
from mojodex_core.entities.user_workflow_execution import UserWorkflowExecution
from mojodex_core.llm_engine.mpt import MPT


class WorkflowAssistant(ChatAssistant):
    mpt_file = "instructions/workflow_run.mpt"

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder,
                 use_draft_placeholder,
                 tag_proper_nouns, user_messages_are_audio, running_user_task_execution: UserWorkflowExecution, db_session):
        try:

            super().__init__(mojo_message_token_stream_callback, draft_token_stream_callback,
                             tag_proper_nouns, user_messages_are_audio, db_session)

            self.workflow_execution = running_user_task_execution
            self.use_message_placeholder = use_message_placeholder
            self.use_draft_placeholder = use_draft_placeholder

            self.workflow_manager = WorkflowManager(self.workflow_execution.session.session_id, self.workflow_execution.user.user_id)

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
                if message:
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
                placeholder = self.workflow_manager.task_execution_placeholder
            if placeholder:
                placeholder_generator.stream(placeholder, self._token_callback)
                return placeholder
        except Exception as e:
            raise Exception(f"_handle_placeholder :: {e}")

    @property
    def _mpt(self):
        try:
            return MPT(self.mpt_file, mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                       user_datetime_context=self.workflow_execution.user.datetime_context,
                       username=self.workflow_execution.user.name,
                       user_company_knowledge=self.workflow_execution.user.company_description,
                       workflow=self.workflow_execution.task,
                       title_start_tag=TaskProducedTextManager.title_tag_manager.start_tag,
                       title_end_tag=TaskProducedTextManager.title_tag_manager.end_tag,
                       draft_start_tag=TaskProducedTextManager.draft_tag_manager.start_tag,
                       draft_end_tag=TaskProducedTextManager.draft_tag_manager.end_tag,
                       user_workflow_inputs=self.workflow_execution.json_input_values,
                       produced_text_done=self.workflow_execution.produced_text_done,
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
            self.workflow_manager.manage_task_stream(partial_text, self.mojo_message_token_stream_callback, self.draft_token_stream_callback)

    def _manage_response_tags(self, response):
        try:
            message = None
            execution = self._manage_execution_tags(response)
            if execution:
                message= self.workflow_manager.task_executor.manage_execution_text(execution_text=execution,
                                                                             task=self.workflow_execution.task,
                                                                             task_name=self.workflow_execution.user_task.task_name_in_user_language,
                                                                             user_task_execution_pk=self.workflow_execution.user_task_execution_pk,
                                                                             use_draft_placeholder=self.use_draft_placeholder
                                                                             )
            else:
                message = self.workflow_manager.manage_response_task_tags(response, self.workflow_execution)
            if message:
                message['text_with_tags'] = response
            return message
        except Exception as e:
            raise Exception(f"_manage_response_tags :: {e}")
