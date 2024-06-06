from models.assistant.models.instruct_task_execution import InstructTaskExecution, User, ChatSession
from models.knowledge.knowledge_manager import KnowledgeManager
from models.assistant.chat_assistant import ChatAssistant
from app import placeholder_generator
from models.tasks.task_manager import TaskManager
from mojodex_core.llm_engine.mpt import MPT


class HomeChatAssistant(ChatAssistant):
    mpt_file = "instructions/home_chat_run.mpt"
    user_message_start_tag, user_message_end_tag = "<message_to_user>", "</message_to_user>"
    task_pk_start_tag, task_pk_end_tag = "<task_pk>", "</task_pk>"

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder,
                 user_id, session_id, tag_proper_nouns, user_messages_are_audio, running_user_task_execution_pk):
        try:
            super().__init__(mojo_message_token_stream_callback, draft_token_stream_callback,
                             tag_proper_nouns, user_messages_are_audio)
            self.instruct_task_execution = InstructTaskExecution(
                running_user_task_execution_pk, self.db_session) if running_user_task_execution_pk else None
            self.user = self.instruct_task_execution.user if self.instruct_task_execution else User(user_id,
                                                                                                    self.db_session)
            self.session = self.instruct_task_execution.session if self.instruct_task_execution else ChatSession(
                session_id, self.db_session)
            self.use_message_placeholder = use_message_placeholder
            self.task_manager = TaskManager(self.session.session_id, self.user.user_id)


        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    def generate_message(self):
        try:
            # If placeholder is required, return it
            if self.use_message_placeholder:
                return self._handle_placeholder()

            # Call LLM
            llm_output = self._call_llm(self.session.conversation, self.user.user_id, self.session.session_id,
                                        user_task_execution_pk=self.instruct_task_execution.user_task_execution_pk if self.instruct_task_execution else None,
                                        task_name_for_system=self.instruct_task_execution.task.name_for_system if self.instruct_task_execution else None)

            # Handle LLM output
            if llm_output:
                message = self._handle_llm_output(llm_output)
                if self.instruct_task_execution:
                    message['user_task_execution_pk'] = self.instruct_task_execution.user_task_execution_pk
                return message
            else:
                # If llm_output is None, the response stream has been interrupted because the context has changed. Restart.
                return self.generate_message()

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: generate_message :: {e}")

    @property
    def requires_vision_llm(self):
        return False

    def _handle_placeholder(self):
        try:
            if self.use_message_placeholder:
                placeholder = self._get_message_placeholder()
                placeholder_generator.stream(placeholder, self._token_callback)
                return placeholder
        except Exception as e:
            raise Exception(f"_handle_placeholder :: {e}")

    def _get_message_placeholder(self):
        return f"{self.user_message_start_tag}{placeholder_generator.mojo_message}{self.user_message_end_tag}"

    @property
    def _mpt(self):
        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()

            return MPT(self.mpt_file, mojo_knowledge=mojo_knowledge,
                       global_context=global_context,
                       username=self.user.username,
                       user_company_knowledge=self.user.company_knowledge,
                       tasks=self.user.available_instruct_tasks,
                       running_task=self.instruct_task_execution.task if self.instruct_task_execution else None,
                       infos_to_extract=self.instruct_task_execution.task.infos_to_extract if self.instruct_task_execution else None,
                       task_specific_instructions=self.instruct_task_execution.instructions if self.instruct_task_execution else None,
                       produced_text_done=self.instruct_task_execution.produced_text_done if self.instruct_task_execution else None,
                       audio_message=self.user_messages_are_audio,
                       tag_proper_nouns=self.tag_proper_nouns)
        except Exception as e:
            raise Exception(f"_mpt :: {e}")

    def __spot_task_pk(self, response):
        try:
            if self.task_pk_end_tag in response:
                task_pk = response.split(self.task_pk_start_tag)[1].split(self.task_pk_end_tag)[0]
                if task_pk.strip().lower() == "null":
                    return True, None
                task_pk = int(task_pk.strip())

                # run specific task prompt
                return True, task_pk
            return False, None
        except Exception as e:
            raise Exception(f"__spot_task_pk :: {e}")

    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()

        # if text contains no tag
        if not partial_text.lower().startswith("<") and self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(partial_text)

        else:

            # if no task is running, eventually we could spot one
            task_pk_spotted, task_pk = self.__spot_task_pk(partial_text)
            if task_pk_spotted:  # task tag spotted
                if task_pk is not None:  # a task is spotted
                    if not self.instruct_task_execution or task_pk != self.instruct_task_execution.task.task_pk:
                        # if the task is different from the running task, we set the new task
                        self.instruct_task_execution = InstructTaskExecution.create_from_user_task(self.user, task_pk,
                                                                                                   self.session,
                                                                                                   self.db_session)
                        # associate previous user message to this task
                        self.session.associate_last_user_message_with_user_task_execution_pk(
                            self.instruct_task_execution.user_task_execution_pk)

                        # TODO: give task_execution a title and a summary
                        return True  # we stop the stream
                else:  # task is null
                    if self.instruct_task_execution:
                        # if the task is null and a task is running, we stop the task
                        self.instruct_task_execution = None
                        # do not stop the stream, this will take effect at next run

            if self.user_message_start_tag in partial_text:
                text = ChatAssistant.remove_tags_from_text(partial_text, self.user_message_start_tag,
                                                           self.user_message_end_tag)
                self.mojo_message_token_stream_callback(text)

            # else, task specific tags
            self.task_manager.manage_task_stream(partial_text, self.mojo_message_token_stream_callback,
                                                 self.draft_token_stream_callback)

    def _manage_response_tags(self, response):
        try:
            execution = self._manage_execution_tags(response)
            if execution:
                if self.instruct_task_execution:
                    return self.task_manager.task_executor.manage_execution_text(execution_text=execution,
                                                                                 task=self.instruct_task_execution.task,
                                                                                 task_name=self.instruct_task_execution.task_name_in_user_language,
                                                                                 user_task_execution_pk=self.instruct_task_execution.user_task_execution_pk)
            if self.user_message_start_tag in response:
                text = ChatAssistant.remove_tags_from_text(response, self.user_message_start_tag,
                                                           self.user_message_end_tag)
                return {"text": text, 'text_with_tags': response}
            return self.task_manager.manage_response_task_tags(response)
        except Exception as e:
            raise Exception(f"_manage_response_tags :: {e}")
