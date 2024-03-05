from app import db, log_error, server_socket, executor, timing_logger, placeholder_generator
from mojodex_core.entities import *
from datetime import datetime
from jinja2 import Template
import os
from sqlalchemy import or_, func

from mojodex_backend_logger import MojodexBackendLogger
from models.knowledge.knowledge_manager import KnowledgeManager

import requests

from models.tasks.task_executor import TaskExecutor
from models.tasks.task_inputs_manager import TaskInputsManager
from models.tasks.task_tool_manager import TaskToolManager

from app import socketio_message_sender
from mojodex_core.mojodex_openai import MojodexOpenAI
#from mojodex_core.mojodex_mistral import MojodexMistralAI, mistral_medium_conf
from models.produced_text_manager import ProducedTextManager
from azure_openai_conf import AzureOpenAIConf
from packaging import version

class TaskManager:
    logger_prefix = "TaskManager::"
    user_language_start_tag = "<user_language>"
    user_language_end_tag = "</user_language>"

    answer_user_prompt = "/data/prompts/tasks/run.txt"
    user_answerer = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "ANSWER_USER", AzureOpenAIConf.azure_gpt4_32_conf)
    
    # EXPERIMENTAL: MistralAI see doc [here](docs/llm_providers/mistral.md)
    #user_answerer = MojodexMistralAI(mistral_medium_conf, "ANSWER_USER")

    def __init__(
        self, user, session_id, platform, voice_generator, mojo_messages_audio_storage,
        task=None, user_task_execution=None):
        try:
            self.logger = MojodexBackendLogger(
                f"{TaskManager.logger_prefix} -- session {session_id}")
            self.session_id = session_id
            self.platform = platform
            self.voice_generator = voice_generator
            self.mojo_messages_audio_storage = mojo_messages_audio_storage
            self.user_id = user.user_id
            self.username = user.name
            self.language = None
            self.mojo_token_callback = lambda partial_text: server_socket.emit('mojo_token', {"text": partial_text, "session_id": self.session_id},
                                                                               to=self.session_id)
            self.produced_text_done = None
            if task is not None:
                self.set_task_and_execution(task, user_task_execution)
            else:
                # will be set later
                self.task = None
                self.user_task = None
                self.task_execution = None
                self.task_displayed_data = None
            self.lexical_produced_text_waiting_for_acknowledgment = None
            self.task_input_manager = TaskInputsManager(session_id, TaskManager.remove_tags_from_text)
            self.task_tool_manager = TaskToolManager(session_id, TaskManager.remove_tags_from_text)
            self.task_executor = TaskExecutor(session_id, self.user_id, self.__mojo_message_to_db, self.__message_will_have_audio, self.__generate_voice)

        except Exception as e:
            raise Exception(f"{TaskManager.logger_prefix} :: __init__ :: {e}")

    def __get_task_tools_json(self):
        try:
            task_tool_associations = db.session.query(MdTaskToolAssociation, MdTool)\
                .join(MdTool, MdTool.tool_pk == MdTaskToolAssociation.tool_fk)\
                .filter(MdTaskToolAssociation.task_fk == self.task.task_pk).all()
            return [{"task_tool_association_pk": task_tool_association.task_tool_association_pk,
                     "usage_description": task_tool_association.usage_description,
                     "tool_name": tool.name}
                    for task_tool_association, tool in task_tool_associations]
        except Exception as e:
            raise Exception(f"_get_task_tools :: {e}")

    # setter pour self.task
    def set_task_and_execution(self, task, user_task_execution):
        self.task = task
        
        self.task_displayed_data = (
            db.session
            .query(
                MdTaskDisplayedData,
            )
            .join(
                MdUser, 
                MdUser.user_id == self.user_id
            )
            .filter(
                MdTaskDisplayedData.task_fk == self.task.task_pk
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

        self.answer_user_prompt = TaskManager.answer_user_prompt
        self.user_task = self.__get_user_task(self.user_id)
        self.task_execution = user_task_execution if user_task_execution else self.__get_task_execution()
        self.task_tool_associations_json = self.__get_task_tools_json()


    def __get_user_task(self, user_id):
        try:
            user_task = db.session.query(MdUserTask).filter(MdUserTask.user_id == user_id,
                                                            MdUserTask.task_fk == self.task.task_pk).first()
            if user_task is None:
                # For the moment, every task is available to every user. When it comes time to restrict tasks, user_task should be created before that (even before classification)
                user_task = MdUserTask(user_id=user_id, task_fk=self.task.task_pk)
                db.session.add(user_task)
                db.session.commit()
            return user_task
        except Exception as e:
            raise Exception(f"__get_user_task :: {e}")

    def __get_task_execution(self):
        try:
            # Is there a task execution running for this task in this session ?
            task_execution = db.session.query(MdUserTaskExecution) \
                .filter(MdUserTaskExecution.user_task_fk == self.user_task.user_task_pk) \
                .filter(MdUserTaskExecution.session_id == self.session_id) \
                .filter(MdUserTaskExecution.end_date == None) \
                .first()
            if task_execution is None:
                task_execution = self.__create_task_execution()
            return task_execution
        except Exception as e:
            raise Exception(f"__get_task_execution :: {e}")

    def __create_task_execution(self):
        try:
            empty_json_input_values = self.__get_empty_json_input_values()
            task_execution = MdUserTaskExecution(user_task_fk=self.user_task.user_task_pk, start_date=datetime.now(),
                                                 json_input_values=empty_json_input_values, session_id=self.session_id)
            db.session.add(task_execution)
            db.session.commit()
            return task_execution
        except Exception as e:
            raise Exception(f"__create_task_execution :: {e}")

    def __get_empty_json_input_values(self):
        try:
            empty_json_input_values = []
            for input in self.task_displayed_data.json_input:
                input["value"] = None
                empty_json_input_values.append(input)
            return empty_json_input_values
        except Exception as e:
            raise Exception(f"__get_empty_json_input_values :: {e}")

    def __draft_token_stream_callback(self, partial_text):
        title = TaskManager.remove_tags_from_text(partial_text.strip(), ProducedTextManager.title_start_tag,
                                                  ProducedTextManager.title_end_tag)
        production = TaskManager.remove_tags_from_text(partial_text.strip(), ProducedTextManager.draft_start_tag,
                                                       ProducedTextManager.draft_end_tag)
        server_socket.emit('draft_token', {"produced_text_title": title,
                                           "produced_text": production,
                                           "session_id": self.session_id,
                                           "text": ProducedTextManager.remove_tags(partial_text)}, to=self.session_id)

    @staticmethod
    def remove_tags_from_text(text, start_tag, end_tag):
        return text.split(start_tag)[1].split(end_tag)[0].strip() if start_tag in text else ""

    def __give_title_and_summary_task_execution(self, user_task_execution_pk):
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

    def response_to_user_message(self, app_version, user_message=None, mojo_token_callback=None, tag_proper_nouns=False):
        """This function is used when task are executed through chat"""
        try:
            self.logger.debug(f"response_to_user_message")
            server_socket.start_background_task(self.__give_title_and_summary_task_execution,
                                                self.task_execution.user_task_execution_pk)
            self.mojo_token_callback = mojo_token_callback
            mojo_message = self.__answer_user(app_version, user_message, tag_proper_nouns=tag_proper_nouns)

            return 'mojo_message', mojo_message
        except Exception as e:
            raise Exception(f"{TaskManager.logger_prefix} :: response_to_user_message :: {e}")

    def __prepare_answers(self, app_version, use_message_placeholder=False, use_draft_placeholder=False, tag_proper_nouns=False):
        try:
            mojo_message = self.__answer_user(app_version, use_message_placeholder=use_message_placeholder,
                                             use_draft_placeholder=use_draft_placeholder, tag_proper_nouns=tag_proper_nouns)
            self.logger.debug(f"__prepare_answers :: mojo_message : {mojo_message}")
            if mojo_message is not None:
                self.__new_mojo_message(mojo_message, app_version)
        except Exception as e:
            raise Exception(f"{TaskManager.logger_prefix} :: __prepare_answers :: {e}")

    def start_task_from_form(self, app_version, use_message_placeholder=False, use_draft_placeholder=False, tag_proper_nouns=False):
        try:
            self.logger.debug(f"start_task_from_form")
            if self.task_execution.title is None:
                server_socket.start_background_task(self.__give_title_and_summary_task_execution,
                                                    self.task_execution.user_task_execution_pk)

            self.logger.debug(f"self.platform : {self.platform}")
            self.__prepare_answers(app_version, use_message_placeholder=use_message_placeholder,
                                   use_draft_placeholder=use_draft_placeholder, tag_proper_nouns=tag_proper_nouns)
            db.session.close()
        except Exception as e:
            try:
                log_error(f"{TaskManager.logger_prefix} :: response_to_user_message :: {e}")
                last_user_message_pk = self.__get_last_user_message()
                message = socketio_message_sender.send_error("Error during session receive_system_message: " + str(e),
                                                             self.session_id, user_message_pk=last_user_message_pk)
                self.__mojo_message_to_db(message, 'error')
                db.session.close()
            except Exception as e:
                db.session.close()

    def __super_prompt_token_callback(self, partial_text):
        partial_text = partial_text.strip()
        if not partial_text.lower().startswith("<"):
            # s'il y a pas de tags => go
            if self.mojo_token_callback:
                self.mojo_token_callback(partial_text)
        else:
            if TaskInputsManager.ask_user_input_start_tag in partial_text:
                # take the text between <ask_user_input> and </ask_user_input>
                text = TaskManager.remove_tags_from_text(partial_text, TaskInputsManager.ask_user_input_start_tag,
                                                         TaskInputsManager.ask_user_input_end_tag)
                if self.mojo_token_callback:
                    self.mojo_token_callback(text)
            if TaskToolManager.tool_usage_start_tag in partial_text:
                text = TaskManager.remove_tags_from_text(partial_text, TaskToolManager.tool_usage_start_tag,
                                                         TaskToolManager.tool_usage_end_tag)
                if self.mojo_token_callback:
                    self.mojo_token_callback(text)
            if TaskExecutor.execution_start_tag in partial_text:
                # take the text between <execution> and </execution>
                text = TaskManager.remove_tags_from_text(partial_text, TaskExecutor.execution_start_tag,
                                                         TaskExecutor.execution_end_tag)
                self.__draft_token_stream_callback(text)

    def __get_produced_text_done(self):
        return db.session.query(MdProducedText).filter(
            MdProducedText.user_task_execution_fk == self.task_execution.user_task_execution_pk).count() > 1

    def __answer_user(self, app_version, user_message=None, use_message_placeholder=False, use_draft_placeholder=False, tag_proper_nouns=False):
        self.logger.debug(f"__answer_user")
        try:
            if user_message:
                use_message_placeholder = user_message["use_message_placeholder"] if (
                        "use_message_placeholder" in user_message) else False
                use_draft_placeholder = user_message["use_draft_placeholder"] if (
                        "use_draft_placeholder" in user_message) else False
        except Exception as e:
            use_message_placeholder, use_draft_placeholder = False, False
        try:

            user_task_inputs = [{k: input[k] for k in
                                 ("input_name", "description_for_system", "type", "value")} for input in
                                self.task_execution.json_input_values if input["value"]]

            if len(user_task_inputs) == 0:
                user_task_inputs = None

            self.produced_text_done = self.__get_produced_text_done()
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()
            user_company_knowledge = KnowledgeManager.get_user_company_knowledge(self.user_task.user_id)

            if use_message_placeholder or use_draft_placeholder:
                if use_message_placeholder:
                    response = f"{TaskInputsManager.ask_user_input_start_tag}{placeholder_generator.mojo_message}{TaskInputsManager.ask_user_input_end_tag}"
                else:
                    response = f"{TaskExecutor.execution_start_tag}" \
                               f"{ProducedTextManager.title_start_tag}{placeholder_generator.mojo_draft_title}{ProducedTextManager.title_end_tag}" \
                               f"{ProducedTextManager.draft_start_tag}{placeholder_generator.mojo_draft_body}{ProducedTextManager.title_end_tag}" \
                               f"{TaskExecutor.execution_end_tag}"
                placeholder_generator.stream(response, self.__super_prompt_token_callback)
            else:
                with open(self.answer_user_prompt, 'r') as f:
                    template = Template(f.read())

                    mega_prompt = template.render(mojo_knowledge=mojo_knowledge,
                                                  global_context=global_context,
                                                  username=self.username,
                                                  user_company_knowledge=user_company_knowledge,
                                                  task=self.task,
                                                  user_task_inputs=user_task_inputs,
                                                  produced_text_done=self.produced_text_done,
                                                  language=self.language,
                                                  audio_message=self.platform == "mobile",
                                                  tag_proper_nouns=tag_proper_nouns,
                                                  title_start_tag=ProducedTextManager.title_start_tag,
                                                  title_end_tag=ProducedTextManager.title_end_tag,
                                                  draft_start_tag=ProducedTextManager.draft_start_tag,
                                                  draft_end_tag=ProducedTextManager.draft_end_tag,
                                                  task_tool_associations=self.task_tool_associations_json
                                                  )

                    conversation_list = self.__get_conversation_as_list()
                    messages = [{"role": "system", "content": mega_prompt}] + conversation_list

                responses = TaskManager.user_answerer.chat(messages, self.user_task.user_id,
                                                           temperature=0, max_tokens=2000,
                                                           user_task_execution_pk=self.task_execution.user_task_execution_pk,
                                                           task_name_for_system=self.task.name_for_system,
                                                           stream=True,
                                                           stream_callback=self.__super_prompt_token_callback,
                                                           )



                response = responses[0].strip()

            if self.language is None and TaskManager.user_language_start_tag in response:
                try:
                    self.language = TaskManager.remove_tags_from_text(response, TaskManager.user_language_start_tag,
                                                                      TaskManager.user_language_end_tag).lower()
                    self.logger.info(f"language: {self.language}")
                    # update session
                    db_session = db.session.query(MdSession).filter(MdSession.session_id == self.session_id).first()
                    db_session.language = self.language
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"Error while updating session language: {e}")
            if TaskInputsManager.ask_user_input_start_tag in response:
                return self.task_input_manager.manage_ask_input_text(response)
            if TaskToolManager.tool_usage_start_tag in response:
                return self.task_tool_manager.manage_tool_usage_text(response,
                                                                     self.task_execution.user_task_execution_pk,
                                                                     self.task_tool_associations_json)
            if TaskExecutor.execution_start_tag in response:
                self.logger.debug(f"TaskExecutor.execution_start_tag in response")
                return self.task_executor.manage_execution_text(execution_text=response, task=self.task, task_displayed_data=self.task_displayed_data,
                                                                user_task_execution_pk=self.task_execution.user_task_execution_pk,
                                                                user_message=user_message,
                                                                app_version = app_version,
                                                                use_draft_placeholder=use_draft_placeholder)
            return {"text": response}

        except Exception as e:
            raise Exception(f"__answer_user :: {e}")

    def __mojo_message_to_db(self, mojo_message, event_name):
        try:
            db_message = MdMessage(session_id=self.session_id, sender='mojo', event_name=event_name,
                                message=mojo_message,
                                creation_date=datetime.now(), message_date=datetime.now())
            db.session.add(db_message)
            db.session.commit()
            db.session.refresh(db_message)
            return db_message
        except Exception as e:
            raise Exception(f"__mojo_message_to_db :: {e}")

    def __new_mojo_message(self, mojo_message, app_version):
        try:
            self.logger.debug(f"__new_mojo_message :: {mojo_message}")
            db_message = self.__mojo_message_to_db(mojo_message, 'mojo_message')
            message_pk = db_message.message_pk
            mojo_message["message_pk"] = message_pk
            mojo_message["audio"] = self.__message_will_have_audio(mojo_message)

            socketio_message_sender.send_mojo_message_with_ack(mojo_message, self.session_id)
            if mojo_message["audio"]:
                self.__generate_voice(db_message)
            return message_pk
        except Exception as e:
            raise Exception(f"__new_mojo_message :: message: {mojo_message} :: {e}")

    def __message_will_have_audio(self, mojo_message):
        return "text" in mojo_message and self.platform == "mobile" and self.voice_generator is not None

    def __generate_voice(self, db_message):
        output_filename = os.path.join(self.mojo_messages_audio_storage, f"{db_message.message_pk}.mp3")
        try:
            self.voice_generator.text_to_speech(db_message.message["text"], self.language, self.user_id,
                                                output_filename,
                                                user_task_execution_pk=self.task_execution.user_task_execution_pk,
                                                task_name_for_system=self.task.name_for_system)

        except Exception as e:
            db_message.in_error_state = datetime.now()
            log_error(str(e), session_id=self.session_id, notify_admin=True)

    def __get_conversation_as_list(self, without_last_message=False, agent_key="assistant", user_key="user"):
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == self.session_id).order_by(
                MdMessage.message_date).all()
            if without_last_message:
                messages = messages[:-1]
            conversation = []
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation.append({"role": user_key, "content": message.message['text']})
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message:
                            conversation.append({"role": agent_key, "content": message.message['text_with_tags']})
                        else:
                            conversation.append({"role": agent_key, "content": message.message['text']})
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("Error during _get_conversation: " + str(e))

    def __get_last_user_message(self):
        try:
            last_user_message_pk = db.session.query(MdMessage.message_pk) \
                .filter(MdMessage.session_id == self.session_id) \
                .filter(MdMessage.sender == 'user') \
                .order_by(MdMessage.message_date.desc()).first()
            if last_user_message_pk is None:
                return None
            return last_user_message_pk[0] if last_user_message_pk else None
        except Exception as e:
            raise Exception(f"__get_last_user_message :: {e}")
