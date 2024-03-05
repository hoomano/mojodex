from abc import ABC, abstractmethod
from jinja2 import Template
import requests
from app import db, log_error, placeholder_generator, server_socket
from models.produced_text_manager import ProducedTextManager
from mojodex_backend_logger import MojodexBackendLogger
from db_models import *
from datetime import datetime
import os
from models.tasks.task_executor import TaskExecutor
from models.tasks.task_inputs_manager import TaskInputsManager
from models.tasks.task_tool_manager import TaskToolManager
from models.knowledge.knowledge_manager import KnowledgeManager
from sqlalchemy.orm.attributes import flag_modified
from models.llm_calls.mojodex_openai import MojodexOpenAI
from azure_openai_conf import AzureOpenAIConf


        


class AssistantMessageGenerator(ABC):

    user_language_start_tag, user_language_end_tag = "<user_language>",  "</user_language>"
    user_message_start_tag, user_message_end_tag = "<message_to_user>", "</message_to_user>"
    task_pk_start_tag, task_pk_end_tag = "<task_pk>", "</task_pk>"

    task_specific_instructions_prompt = "/data/prompts/tasks/task_specific_instructions.txt"
    answer_user_prompt = "/data/prompts/mega_mega_prompt.txt"
    user_answerer = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "CHAT",
                                  AzureOpenAIConf.azure_gpt4_32_conf)

    def __init__(self, user, session_id, platform, voice_generator, mojo_messages_audio_storage, logger_prefix, mojo_token_callback, app_version, origin):
        self.origin = origin
        self.user_id = user.user_id
        self.username = user.name
        self.session_id = session_id
        self.platform = platform
        self.voice_generator = voice_generator
        self.mojo_messages_audio_storage = mojo_messages_audio_storage
        self.mojo_token_callback = mojo_token_callback
        self.app_version = app_version
        self.language = None
        self._running_task = None
        self._running_user_task = None
        self._running_user_task_execution = None
        self._running_task_displayed_data = None
        self.running_task_set=False
        self.task_input_manager = TaskInputsManager(session_id, self.remove_tags_from_text)
        self.task_tool_manager = TaskToolManager(session_id, self.remove_tags_from_text)
        self.task_executor = TaskExecutor(session_id, self.user_id, self._mojo_message_to_db, self._message_will_have_audio, self._generate_voice)
        self.logger = MojodexBackendLogger(f"{logger_prefix} -- session {session_id}")

    
    @staticmethod
    def remove_tags_from_text(text, start_tag, end_tag):
        try:
            return text.split(start_tag)[1].split(end_tag)[0].strip() if start_tag in text else ""
        except Exception as e:
            raise Exception(f"remove_tags_from_text :: text: {text} - start_tag: {start_tag} - end_tag: {end_tag} - {e}")
    
    @abstractmethod
    def _get_message_placeholder(self):
        raise NotImplementedError
    
    @abstractmethod
    def _get_execution_placeholder(self):
        raise NotImplementedError
    

    def _generate_assistant_response(self, tag_proper_nouns=False):
        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()
            user_company_knowledge = KnowledgeManager.get_user_company_knowledge(self.running_user_task.user_id)
            user_tasks = self.__get_user_tasks()
            task_specific_instructions = self.__get_specific_task_instructions(self.running_task) if self.running_task else None
            produced_text_done = self._get_produced_text_done()
            conversation_list = self._get_conversation_as_list()

            home_chat_prompt = self.__get_prompt(
                mojo_knowledge, global_context, user_company_knowledge, tag_proper_nouns, produced_text_done, user_tasks, task_specific_instructions)
            
            # Write prompt in /data/filled_prompt.txt
            with open("/data/filled_prompt.txt", "w") as file:
                file.write(home_chat_prompt)

            messages = [{"role": "system", "content": home_chat_prompt}] + conversation_list

            responses = self.user_answerer.chat(messages, self.user_id,
                                                        temperature=0 if self.running_task else 1, # TODO
                                                          max_tokens=4000,
                                                        stream=True, stream_callback=self._token_callback)

            if responses:
                # write response in /data/response.txt
                with open("/data/response.txt", "w") as file:
                    file.write(responses[0])
                return responses[0].strip()
            else:
                return self._generate_assistant_response(tag_proper_nouns)
        except Exception as e:
            raise Exception(f"_generate_assistant_response :: {e}")
    
    def __get_specific_task_instructions(self, task):
        try:
            with open(self.task_specific_instructions_prompt, "r") as f:
                template = Template(f.read())
                return template.render(task=task,
                                    title_start_tag=ProducedTextManager.title_start_tag,
                                    title_end_tag=ProducedTextManager.title_end_tag,
                                    draft_start_tag=ProducedTextManager.draft_start_tag,
                                    draft_end_tag=ProducedTextManager.draft_end_tag,
                                    task_tool_associations=self._get_task_tools_json(task),
                                    user_task_inputs=self.__get_running_user_task_execution_inputs()
                                    )
        except Exception as e:
            raise Exception(f"__get_running_task_instructions :: {e}")
        
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
    
    def __get_user_tasks(self):
        try:
            user_tasks = db.session.query(MdTask).\
                join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk).\
                filter(MdUserTask.user_id == self.user_id).all()
            return [{
                'task_pk': task.task_pk,
                'icon': task.icon,
                'name_for_system': task.name_for_system,
                'description': task.definition_for_system
            } for task in user_tasks]
        except Exception as e:
            raise Exception(f"__get_user_tasks :: {e}")

    def __get_prompt(self, mojo_knowledge, global_context, user_company_knowledge, tag_proper_nouns, produced_text_done, tasks, task_specific_instructions):
        try:
            with open(self.answer_user_prompt, 'r') as f:
                template = Template(f.read())

                mega_prompt = template.render(mojo_knowledge=mojo_knowledge,
                                                global_context=global_context,
                                                username=self.username,
                                                user_company_knowledge=user_company_knowledge,
                                                general_chat = self.origin=='home_chat', # TODO
                                                tasks = tasks,
                                                running_task=self.running_task,
                                                task_specific_instructions=task_specific_instructions,
                                                produced_text_done=produced_text_done,
                                                audio_message=self.platform == "mobile",
                                                tag_proper_nouns=tag_proper_nouns
                                                )
                return mega_prompt
        except Exception as e:
            raise Exception(f"_get_prompt :: {e}")
    
    def _draft_token_stream_callback(self, partial_text):
        title = self.remove_tags_from_text(partial_text.strip(), ProducedTextManager.title_start_tag,
                                                  ProducedTextManager.title_end_tag)
        production = self.remove_tags_from_text(partial_text.strip(), ProducedTextManager.draft_start_tag,
                                                       ProducedTextManager.draft_end_tag)
        server_socket.emit('draft_token', {"produced_text_title": title,
                                           "produced_text": production,
                                           "session_id": self.session_id,
                                           "text": ProducedTextManager.remove_tags(partial_text)}, to=self.session_id)

    def __create_user_task_execution(self):
        try:
            empty_json_input_values = self._get_empty_json_input_values()
           
            task_execution = MdUserTaskExecution(user_task_fk=self.running_user_task.user_task_pk, start_date=datetime.now(),
                                                 json_input_values=empty_json_input_values, session_id=self.session_id)
            db.session.add(task_execution)
            db.session.commit()
            self.running_user_task_execution = task_execution
        except Exception as e:
            raise Exception(f"__create_user_task_execution :: {e}")

    def __associate_previous_user_message(self):
        try:
            self.logger.debug(f"__associate_previous_user_message")
            from models.session import Session as SessionModel
            previous_user_message = db.session.query(MdMessage).filter(MdMessage.session_id == self.session_id).filter(
                MdMessage.sender == SessionModel.user_message_key).order_by(MdMessage.message_date.desc()).first()
            if previous_user_message:
                new_message = previous_user_message.message

                new_message['user_task_execution_pk'] = self.running_user_task_execution.user_task_execution_pk
                previous_user_message.message = new_message
                flag_modified(previous_user_message, "message")
                db.session.commit() 
        except Exception as e:
            raise Exception(f"__associate_previous_user_message :: {e}")
        
    def __set_running_task(self, task_pk):
        try:
            self.running_task_set = True
            if task_pk is not None:
                self.running_task, self.running_task_displayed_data, self.running_user_task = db.session.query(MdTask, MdTaskDisplayedData, MdUserTask)\
                    .join(MdTaskDisplayedData, MdTask.task_pk == MdTaskDisplayedData.task_fk)\
                    .join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk)\
                    .filter(MdTask.task_pk == task_pk).first()
                # create user_task_execution
                self.__create_user_task_execution()
                self.__associate_previous_user_message()
            else:
                self.running_task, self.running_task_displayed_data, self.running_user_task, self.running_user_task_execution = None, None, None, None
        except Exception as e:
            raise Exception(f"__set_running_task :: {e}")

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
        if not partial_text.lower().startswith("<"):
            # s'il y a pas de tags => go
            if self.mojo_token_callback:
                self.mojo_token_callback(partial_text)
        else:
            if not self.running_task_set:
                task_pk_spotted, task_pk = self.__spot_task_pk(partial_text)
                if task_pk_spotted:
                    running_task_pk = self.running_task.task_pk if self.running_task else None
                    if task_pk is not None and task_pk != running_task_pk:
                        self.__set_running_task(task_pk)
                        self.logger.debug("TASK SPOTTED")
                        return True # Stop the stream
                    elif task_pk is None and self.running_task is not None:
                        self.logger.debug("END OF TASK")
                        self.__set_running_task(None)
            text=None
            if self.user_message_start_tag in partial_text:
                    text = self.remove_tags_from_text(partial_text, self.user_message_start_tag, self.user_message_end_tag)
            elif TaskInputsManager.ask_user_input_start_tag in partial_text:
                text = self.remove_tags_from_text(partial_text, TaskInputsManager.ask_user_input_start_tag,
                                                         TaskInputsManager.ask_user_input_end_tag)
                if self.mojo_token_callback:
                    self.mojo_token_callback(text)
            elif TaskToolManager.tool_usage_start_tag in partial_text:
                text = self.remove_tags_from_text(partial_text, TaskToolManager.tool_usage_start_tag,
                                                         TaskToolManager.tool_usage_end_tag)
            if text and self.mojo_token_callback:
                self.mojo_token_callback(text)
            elif TaskExecutor.execution_start_tag in partial_text:
                # take the text between <execution> and </execution>
                text = self.remove_tags_from_text(partial_text, TaskExecutor.execution_start_tag,
                                                         TaskExecutor.execution_end_tag)
                self._draft_token_stream_callback(text)
    
    def launch_mojo_message_generation(self, user_message=None, use_message_placeholder=False, use_draft_placeholder=False, tag_proper_nouns=False):
        try:
            if self.running_user_task_execution:
                server_socket.start_background_task(self._give_title_and_summary_task_execution,
                                                self.running_user_task_execution.user_task_execution_pk)
            mojo_message = self._generate_mojo_message(user_message,  use_message_placeholder=use_message_placeholder,
                                             use_draft_placeholder=use_draft_placeholder, tag_proper_nouns=tag_proper_nouns)
            if mojo_message and self.running_user_task_execution:
                mojo_message['user_task_execution_pk'] = self.running_user_task_execution.user_task_execution_pk
            return 'mojo_message', mojo_message, self.language
        except Exception as e:
            raise Exception(f"response_to_user_message :: {e}")
    
    def _give_title_and_summary_task_execution(self, user_task_execution_pk):
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
            print(f"🔴 _give_title_and_summary_task_execution :: {e}")

    def _get_empty_json_input_values(self):
        try:
            empty_json_input_values = []
            for input in self.running_task_displayed_data.json_input:
                input["value"] = None
                empty_json_input_values.append(input)
            return empty_json_input_values
        except Exception as e:
            raise Exception(f"_get_empty_json_input_values :: {e}")

    def _manage_placeholders(self, use_message_placeholder, use_draft_placeholder):
        try:
            if use_message_placeholder:
                response = self._get_message_placeholder()
            elif use_draft_placeholder:
                response = self._get_execution_placeholder()
                placeholder_generator.stream(response, self._token_callback)
            return response
        except Exception as e:
            raise Exception(f"_manage_placeholders :: {e}")
        
    def _extract_placeholders_from_user_message(self, user_message):
        try:
            use_message_placeholder = user_message["use_message_placeholder"] if (
                    "use_message_placeholder" in user_message) else False
            use_draft_placeholder = user_message["use_draft_placeholder"] if (
                    "use_draft_placeholder" in user_message) else False
        except Exception as e:
            use_message_placeholder, use_draft_placeholder = False, False
        return use_message_placeholder, use_draft_placeholder
    
    def _generate_mojo_message(self, user_message=None, use_message_placeholder=False, use_draft_placeholder=False, tag_proper_nouns=False):
        self.logger.debug(f"_answer_user")
        
        try:
            if user_message is not None:
                use_message_placeholder, use_draft_placeholder = self._extract_placeholders_from_user_message(user_message)

            if use_message_placeholder or use_draft_placeholder:
                response = self._manage_placeholders(use_message_placeholder, use_draft_placeholder)
            else:
                response = self._generate_assistant_response(tag_proper_nouns=tag_proper_nouns)
                
            
            self._manage_response_language_tag(response)
            response = self._manage_response_tag(response, user_message, use_draft_placeholder)
            return response

        except Exception as e:
            raise Exception(f"_answer_user :: {e}")
    
    def _get_produced_text_done(self):
        try:
            if self.running_user_task_execution is None:
                return False
            return db.session.query(MdProducedText).filter(
                MdProducedText.user_task_execution_fk == self.running_user_task_execution.user_task_execution_pk).count() > 1
        except Exception as e:
            raise Exception(f"_get_produced_text_done :: {e}")

    def _get_task_tools_json(self, task):
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

    def _get_all_session_messages(self, session_id):
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == session_id).order_by(
                MdMessage.message_date).all()
            return messages
        except Exception as e:
            raise Exception("_get_all_session_messages: " + str(e))
        
    def _get_conversation_as_list(self, without_last_message=False, agent_key="assistant", user_key="user"):
        try:
            messages = self._get_all_session_messages(self.session_id)
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
 
    def _mojo_message_to_db(self, mojo_message, event_name):
        try:
            user_task_execution_pk = self.running_user_task_execution.user_task_execution_pk if self.running_user_task_execution else None
            if user_task_execution_pk:
                mojo_message["user_task_execution_pk"] = user_task_execution_pk
            db_message = MdMessage(session_id=self.session_id, sender='mojo', event_name=event_name,
                                message=mojo_message,
                                creation_date=datetime.now(), message_date=datetime.now())
            db.session.add(db_message)
            db.session.commit()
            db.session.refresh(db_message)
            return db_message
        except Exception as e:
            raise Exception(f"__mojo_message_to_db :: {e}")
        
    def _message_will_have_audio(self, mojo_message):
        return "text" in mojo_message and self.platform == "mobile" and self.voice_generator is not None
    
    def _generate_voice(self, db_message):
        output_filename = os.path.join(self.mojo_messages_audio_storage, f"{db_message.message_pk}.mp3")
        try:
            self.voice_generator.text_to_speech(db_message.message["text"], self.language, self.user_id,
                                                output_filename,
                                                user_task_execution_pk=self.running_user_task_execution.user_task_execution_pk if self.running_user_task_execution else None,
                                                task_name_for_system=self.running_task.name_for_system if self.running_task else None,)

        except Exception as e:
            db_message.in_error_state = datetime.now()
            log_error(str(e), session_id=self.session_id, notify_admin=True)

    def _manage_response_language_tag(self, response):
        try:
            if self.language is None and AssistantMessageGenerator.user_language_start_tag in response:
                try:
                    self.language = self.remove_tags_from_text(response, AssistantMessageGenerator.user_language_start_tag,
                                                                      AssistantMessageGenerator.user_language_end_tag).lower()
                    self.logger.info(f"language: {self.language}")
                    # update session
                    db_session = db.session.query(MdSession).filter(MdSession.session_id == self.session_id).first()
                    db_session.language = self.language
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"Error while updating session language: {e}")
        except Exception as e:
            raise Exception(f"_manage_response_language_tag :: {e}")
        
    def _manage_response_tag(self, response, user_message, use_draft_placeholder):
        try:
            if self.user_message_start_tag in response:
                text = self.remove_tags_from_text(response, self.user_message_start_tag, self.user_message_end_tag)
                return {"text": text, 'text_with_tags': response}
            if TaskInputsManager.ask_user_input_start_tag in response:
                return self.task_input_manager.manage_ask_input_text(response)
            if TaskToolManager.tool_usage_start_tag in response:
                return self.task_tool_manager.manage_tool_usage_text(response,
                                                                     self.running_user_task_execution.user_task_execution_pk,
                                                                     self._get_task_tools_json(self.running_task))
            elif TaskExecutor.execution_start_tag in response:
                # take the text between <execution> and </execution>
                self.logger.debug(f"TaskExecutor.execution_start_tag in response")
                return self.task_executor.manage_execution_text(execution_text=response, task=self.running_task, task_displayed_data=self.running_task_displayed_data,
                                                                user_task_execution_pk=self.running_user_task_execution.user_task_execution_pk,
                                                                user_message=user_message,
                                                                app_version = self.app_version,
                                                                use_draft_placeholder=use_draft_placeholder)
            return {"text": response}
        except Exception as e:
            raise Exception(f"_manage_response_tag :: {e}")