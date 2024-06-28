from datetime import datetime

from mojodex_core.knowledge_manager import KnowledgeManager
from mojodex_core.tag_manager import TagManager
from models.assistant.chat_assistant import ChatAssistant
from app import placeholder_generator, server_socket

from models.tasks.instruct_tasks.instruct_task_manager import InstructTaskManager
from mojodex_core.entities.session import Session
from mojodex_core.entities.user import User

from mojodex_core.entities.instruct_user_task_execution import InstructTaskExecution

from mojodex_core.entities.instruct_user_task import InstructUserTask
from mojodex_core.llm_engine.mpt import MPT
from mojodex_core.task_execution_title_summary_generator import TaskExecutionTitleSummaryGenerator


class HomeChatAssistant(ChatAssistant):
    mpt_file = "instructions/home_chat_run.mpt"
    user_message_start_tag, user_message_end_tag = "<message_to_user>", "</message_to_user>"
    task_pk_start_tag, task_pk_end_tag = "<task_pk>", "</task_pk>"

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder,
                 user_id, session_id, tag_proper_nouns, user_messages_are_audio, running_user_task_execution: InstructTaskExecution,
                 db_session):
        try:
            super().__init__(mojo_message_token_stream_callback, draft_token_stream_callback,
                             tag_proper_nouns, user_messages_are_audio, db_session)
            self.instruct_task_execution = running_user_task_execution if running_user_task_execution else None
            self.user = self.instruct_task_execution.user if self.instruct_task_execution else self.db_session.query(User).get(user_id)
            self.session = self.instruct_task_execution.session if self.instruct_task_execution else self.db_session.query(
                Session).get(session_id)
            self.use_message_placeholder = use_message_placeholder
            self.task_manager = InstructTaskManager(self.session.session_id, self.user.user_id)
            self.user_message_tag_manager = TagManager("user_message")

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
        return self.user_message_tag_manager.add_tags_to_text(placeholder_generator.mojo_message)

    @property
    def _mpt(self):
        try:
            return MPT(self.mpt_file, mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                       global_context=self.user.datetime_context,
                       username=self.user.name,
                       user_company_knowledge=self.user.company_description,
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

    def _create_user_task_execution(self, task_pk):
        try:
            user_task = self.db_session.query(InstructUserTask) \
                .filter(InstructUserTask.task_fk == task_pk) \
                .filter(InstructUserTask.user_id == self.user.user_id) \
                .first()
            self.instruct_task_execution = InstructTaskExecution(
                user_task_fk=user_task.user_task_pk,
                start_date=datetime.now(),
                json_input_values=user_task.json_input_in_user_language,
                session_id=self.session.session_id,
            )
            self.db_session.add(self.instruct_task_execution)
            self.db_session.commit()
        except Exception as e:
            raise Exception(f"_create_user_task_execution :: {e}")

    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()

        # if text contains no tag
        if not partial_text.lower().startswith("<") and self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(partial_text)

        else:

            # At any time we need to check if the assistant has detected the task_pk tag and if yes, what is the detected task_pk 
            task_pk_spotted, task_pk = self.__spot_task_pk(partial_text)
            if task_pk_spotted:  # task tag detected
                if task_pk is not None:  # a task is running
                    if not self.instruct_task_execution or task_pk != self.instruct_task_execution.task.task_pk:
                        # if the task is different from the running task, we set the new task
                        self._create_user_task_execution(task_pk)
                        # associate previous user message to this task
                        if self.session.last_user_message:
                            self.session.last_user_message.user_task_execution_pk = self.instruct_task_execution.user_task_execution_pk

                        server_socket.start_background_task(TaskExecutionTitleSummaryGenerator.generate_title_and_summary, self.instruct_task_execution.user_task_execution_pk)
                        return True  # we stop the stream
                else:  # detected task is null
                    if self.instruct_task_execution:
                        # if the task is null and a task is running, we stop the task
                        self.instruct_task_execution = None
                        # do not stop the stream, this will take effect at next run

            if self.user_message_start_tag in partial_text:
                text = self.user_message_tag_manager.remove_tags_from_text(partial_text)
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
                text = self.user_message_tag_manager.remove_tags_from_text(response)
                return {"text": text, 'text_with_tags': response}
            return self.task_manager.manage_response_task_tags(response)
        except Exception as e:
            raise Exception(f"_manage_response_tags :: {e}")
