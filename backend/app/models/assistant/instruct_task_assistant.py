from models.assistant.models.instruct_task_execution import InstructTaskExecution
from models.knowledge.knowledge_manager import KnowledgeManager
from models.assistant.chat_assistant import ChatAssistant
from models.tasks.task_manager import TaskManager
from app import placeholder_generator
from mojodex_core.llm_engine.mpt import MPT


class InstructTaskAssistant(ChatAssistant):
    mpt_file = "instructions/task_run.mpt"

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder,
                 use_draft_placeholder,
                 tag_proper_nouns, user_messages_are_audio, running_user_task_execution_pk):
        try:
            super().__init__(mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder,
                             tag_proper_nouns, user_messages_are_audio)

            self.instruct_task_execution = InstructTaskExecution(running_user_task_execution_pk, self.db_session)
            self.use_draft_placeholder = use_draft_placeholder

            self.task_manager = TaskManager(self.instruct_task_execution.session.session_id,
                                            self.instruct_task_execution.user.user_id)

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    def generate_message(self):
        try:
            # If placeholder is required, return it
            if self.use_message_placeholder or self.use_draft_placeholder:
                return self._handle_placeholder()

            # Call LLM
            llm_output = self._call_llm(self.instruct_task_execution.session.conversation,
                                        self.instruct_task_execution.user.user_id,
                                        self.instruct_task_execution.session.session_id,
                                        user_task_execution_pk=self.instruct_task_execution.user_task_execution_pk,
                                        task_name_for_system=self.instruct_task_execution.task.name_for_system)

            # Handle LLM output
            if llm_output:
                message = self._handle_llm_output(llm_output)
                message['user_task_execution_pk'] = self.instruct_task_execution.user_task_execution_pk
                return message

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: generate_message :: {e}")

    def _handle_placeholder(self):
        try:
            placeholder = None
            if self.use_message_placeholder:
                placeholder = self.task_manager.task_message_placeholder
            elif self.use_draft_placeholder:
                placeholder = self.task_manager.task_execution_placeholder
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
                       username=self.instruct_task_execution.user.username,
                       user_company_knowledge=self.instruct_task_execution.user.company_knowledge,
                       infos_to_extract=self.instruct_task_execution.task.infos_to_extract,
                       task_specific_instructions=self.instruct_task_execution.instructions,
                       produced_text_done=self.instruct_task_execution.produced_text_done,
                       audio_message=self.user_messages_are_audio,
                       tag_proper_nouns=self.tag_proper_nouns)
        except Exception as e:
            raise Exception(f"_mpt :: {e}")

    @property
    def requires_vision_llm(self):
        return self.instruct_task_execution.has_images_inputs

    @property
    def input_images(self):
        return self.instruct_task_execution.images_input_names

    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()

        # if text contains no tag
        if not partial_text.lower().startswith("<") and self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(partial_text)

        else:
            self.task_manager.manage_task_stream(partial_text, self.mojo_message_token_stream_callback,
                                                 self.draft_token_stream_callback)

    def _manage_response_tags(self, response):
        try:
            execution = self._manage_execution_tags(response)
            if execution:
                return self.task_manager.task_executor.manage_execution_text(execution_text=execution,
                                                                             task=self.instruct_task_execution.task,
                                                                             task_name=self.instruct_task_execution.task.get_name_in_language(
                                                                                 self.instruct_task_execution.user.language_code),
                                                                             user_task_execution_pk=self.instruct_task_execution.user_task_execution_pk,
                                                                             use_draft_placeholder=self.use_draft_placeholder
                                                                             )
            return self.task_manager.manage_response_task_tags(response)
        except Exception as e:
            raise Exception(f"_manage_response_tags :: {e}")
