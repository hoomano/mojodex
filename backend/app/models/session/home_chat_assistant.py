from app import server_socket
import os
from datetime import datetime
import requests

from models.session.instruct_task_execution import InstructTaskExecution, User
from models.knowledge.knowledge_manager import KnowledgeManager
from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from models.session.execution_manager import ExecutionManager
from models.tasks.task_executor import TaskExecutor
from models.tasks.task_inputs_manager import TaskInputsManager
from models.tasks.task_tool_manager import TaskToolManager

from models.produced_text_managers.instruct_task_produced_text_manager import InstructTaskProducedTextManager

from models.session.assistant_message_generators.general_chat_response_generator import \
    GeneralChatResponseGenerator

from models.session.instruct_task_execution import ChatSession
from mojodex_core.llm_engine.providers.openai_vision_llm import VisionMessagesData
from mojodex_core.logging_handler import log_error
from app import placeholder_generator, model_loader
from jinja2 import Template
from mojodex_core.db import engine, Session


class HomeChatAssistant:
    prompt_file = "mojodex_core/prompts/home_chat/run.txt"
    language_start_tag, language_end_tag = "<user_language>", "</user_language>"
    user_message_start_tag, user_message_end_tag = "<message_to_user>", "</message_to_user>"
    task_pk_start_tag, task_pk_end_tag = "<task_pk>", "</task_pk>"

    def __del__(self):
        self.db_session.close()

    def __init__(self, mojo_message_token_stream_callback, draft_token_stream_callback, use_message_placeholder,
                 user_id, session_id,
                 tag_proper_nouns, user_messages_are_audio, running_user_task_execution_pk):
        try:
            self.db_session = Session(engine)
            self.instruct_task_execution = InstructTaskExecution(
                running_user_task_execution_pk, self.db_session ) if running_user_task_execution_pk else None
            self.user = self.instruct_task_execution.user if self.instruct_task_execution else User(user_id,
                                                                                                    self.db_session)
            self.session = self.instruct_task_execution.session if self.instruct_task_execution else ChatSession(
                session_id, self.db_session)

            self.use_message_placeholder = use_message_placeholder
            self.tag_proper_nouns = tag_proper_nouns
            self.user_messages_are_audio = user_messages_are_audio
            self.mojo_message_token_stream_callback = mojo_message_token_stream_callback
            self.draft_token_stream_callback = draft_token_stream_callback
            self.task_input_manager = TaskInputsManager(self.session.session_id)
            # self.task_tool_manager = TaskToolManager(self.instruct_task_execution.session.session_id)
            self.execution_manager = ExecutionManager(self.session.session_id)
            self.task_executor = TaskExecutor(self.session.session_id,
                                              self.user.user_id)
            self.language = None

        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ :: {e}")

    def generate_message(self):
        try:
            # call background for title and summary
            if self.instruct_task_execution:
                server_socket.start_background_task(self._give_task_execution_title_and_summary,
                                                    self.instruct_task_execution.user_task_execution_pk)

            # If placeholder is required, return it
            if self.use_message_placeholder:
                return self._handle_placeholder()

            # Else, prepare prompt
            prompt = self._render_prompt_from_template()

            # Write prompt to file
            with open("/data/prompt.txt", "w") as f:
                f.write(prompt)

            # Call LLM
            llm_output = self._call_llm(prompt)



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

    def _give_task_execution_title_and_summary(self, user_task_execution_pk):
        try:
            # call background backend /end_user_task_execution to update user task execution title and summary
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/user_task_execution_title_and_summary"
            pload = {'datetime': datetime.now().isoformat(),
                     'user_task_execution_pk': user_task_execution_pk}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(
                    f"Error while calling background user_task_execution_title_and_summary : {internal_request.json()}")
        except Exception as e:
            print(f"🔴 __give_title_and_summary_task_execution :: {e}")

    def _handle_placeholder(self):
        try:
            if self.use_message_placeholder:
                placeholder = self._get_message_placeholder()
                placeholder_generator.stream(placeholder, self._token_callback)
                return placeholder
        except Exception as e:
            raise Exception(f"_handle_placeholder :: {e}")

    def _get_message_placeholder(self):
        return f"{GeneralChatResponseGenerator.user_message_start_tag}{placeholder_generator.mojo_message}{GeneralChatResponseGenerator.user_message_end_tag}"

    def _get_task_execution_placeholder(self):
        return f"{ExecutionManager.execution_start_tag}" \
               f"{InstructTaskProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{InstructTaskProducedTextManager.title_end_tag}" \
               f"{InstructTaskProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{InstructTaskProducedTextManager.draft_end_tag}" \
               f"{ExecutionManager.execution_end_tag}"

    def _render_prompt_from_template(self):
        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()

            with open(self.prompt_file, 'r') as f:
                prompt_template = Template(f.read())
            return prompt_template.render(mojo_knowledge=mojo_knowledge,
                                          global_context=global_context,
                                          username=self.user.username,
                                          user_company_knowledge=self.user.company_knowledge,
                                          tasks=self.user.available_instruct_tasks,
                                          running_task=self.instruct_task_execution.task if self.instruct_task_execution else None,
                                          infos_to_extract=self.instruct_task_execution.task.infos_to_extract if self.instruct_task_execution else None,
                                          task_specific_instructions=self.instruct_task_execution.instructions if self.instruct_task_execution else None,
                                          produced_text_done=self.instruct_task_execution.produced_text_done if self.instruct_task_execution else None,
                                          audio_message=self.user_messages_are_audio,
                                          tag_proper_nouns=self.tag_proper_nouns,
                                          language=None
                                          )
        except Exception as e:
            raise Exception(f"_render_prompt_from_template :: {e}")

    def _call_llm(self, prompt):
        try:
            # TODO: what if instruct_task_execution
            conversation_list = self.session.conversation
            temperature, max_tokens, label = 0, 4000, 'home_chat_assistant'
            messages = [{"role": "system", "content": prompt}] + conversation_list
            responses = model_loader.main_llm.invoke(messages, self.user.user_id,
                                                     temperature=temperature,
                                                     max_tokens=max_tokens,
                                                     label=label,
                                                     stream=True, stream_callback=self._token_callback,
                                                     user_task_execution_pk=self.instruct_task_execution.user_task_execution_pk if self.instruct_task_execution else None,
                                                     task_name_for_system=self.instruct_task_execution.task.name_for_system if self.instruct_task_execution else None)

            return responses[0].strip() if responses else None
        except Exception as e:
            raise Exception(f"_call_llm :: {e}")

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
                print(f"🔵 TASK PK SPOTTED: {task_pk}")
                if task_pk is not None:  # a task is spotted
                    if not self.instruct_task_execution or task_pk != self.instruct_task_execution.task.task_pk:
                        # if the task is different from the running task, we set the new task
                        self.instruct_task_execution = InstructTaskExecution.create_from_user_task(self.user, task_pk,
                                                                                                   self.session,
                                                                                                   self.db_session)
                        # associate previous user message to this task
                        self.session.associate_last_user_message_with_user_task_execution_pk(self.instruct_task_execution.user_task_execution_pk)
                        return True  # we stop the stream
                else:  # task is null
                    if self.instruct_task_execution:
                        # if the task is null and a task is running, we stop the task
                        self.instruct_task_execution = None
                        # do not stop the stream, this will take effect at next run

            if self.user_message_start_tag in partial_text:
                print(f"🔵 user_message_start_tag")
                text = AssistantMessageGenerator.remove_tags_from_text(partial_text, self.user_message_start_tag,
                                                                       self.user_message_end_tag)
                self.mojo_message_token_stream_callback(text)

            # else, task specific tags
            text = None
            if TaskInputsManager.ask_user_input_start_tag in partial_text:
                text = AssistantMessageGenerator.remove_tags_from_text(partial_text,
                                                                       TaskInputsManager.ask_user_input_start_tag,
                                                                       TaskInputsManager.ask_user_input_end_tag)
            # elif TaskToolManager.tool_usage_start_tag in partial_text:
            #     text = AssistantMessageGenerator.remove_tags_from_text(partial_text, TaskToolManager.tool_usage_start_tag,
            #                                                           TaskToolManager.tool_usage_end_tag)
            if text and self.mojo_message_token_stream_callback:
                self.mojo_message_token_stream_callback(text)

            elif ExecutionManager.execution_start_tag in partial_text:
                # take the text between <execution> and </execution>
                text = AssistantMessageGenerator.remove_tags_from_text(partial_text,
                                                                       ExecutionManager.execution_start_tag,
                                                                       ExecutionManager.execution_end_tag)
                self.draft_token_stream_callback(text)

    def _handle_llm_output(self, llm_output):
        try:
            self._manage_response_language_tags(llm_output)
            response = self._manage_response_tags(llm_output)
            return response
        except Exception as e:
            raise Exception(f"_handle_llm_output:: {e}")

    def _manage_response_language_tags(self, response):
        """
        Remove language tags from the response and update the language in the context
        :param response: response
        """
        try:
            if self.language_start_tag in response:
                try:
                    self.language = AssistantMessageGenerator.remove_tags_from_text(response,
                                                                                    self.language_start_tag,
                                                                                    self.language_end_tag).lower()
                except Exception as e:
                    pass
        except Exception as e:
            raise Exception(f"__manage_response_language_tags:: {e}")

    def _manage_response_task_tags(self, response):
        try:
            if self.user_message_start_tag in response:
                text = AssistantMessageGenerator.remove_tags_from_text(response, self.user_message_start_tag,
                                                                       self.user_message_end_tag)
                return {"text": text, 'text_with_tags': response}
            if TaskInputsManager.ask_user_input_start_tag in response:
                return self.task_input_manager.manage_ask_input_text(response)
            # if TaskToolManager.tool_usage_start_tag in response:
            #    return self.task_tool_manager.manage_tool_usage_text(response,
            #                                                         self.running_user_task_execution.user_task_execution_pk,
            #                                                         self._get_task_tools_json(self.running_task))
            return {"text": response}
        except Exception as e:
            raise Exception(f"_manage_response_task_tags :: {e}")

    def _manage_execution_tags(self, response):
        try:
            if ExecutionManager.execution_start_tag in response:
                return self.execution_manager.manage_execution_text(response, self.instruct_task_execution.task,
                                                                    self.instruct_task_execution.task.get_name_in_language(
                                                                        self.instruct_task_execution.user.language_code),
                                                                    self.instruct_task_execution.user_task_execution_pk,
                                                                    self.task_executor)
        except Exception as e:
            raise Exception(f"_manage_execution_tags :: {e}")

    def _manage_response_tags(self, response):
        try:
            execution = self._manage_execution_tags(response)
            if execution:
                return execution
            return self._manage_response_task_tags(response)
        except Exception as e:
            raise Exception(f"_manage_response_tags :: {e}")
