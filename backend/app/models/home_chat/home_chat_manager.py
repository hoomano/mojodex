import os
from datetime import datetime, timedelta

from jinja2 import Template
from mojodex_backend_logger import MojodexBackendLogger
from app import db, placeholder_generator
from models.knowledge.knowledge_manager import KnowledgeManager

from models.llm_calls.mojodex_openai import MojodexOpenAI
from mojodex_core.entities import *
from azure_openai_conf import AzureOpenAIConf
from sqlalchemy import and_

from models.home_chat.task_suggestion_manager import TaskSuggestionManager


class HomeChatManager:
    logger_prefix = "HomeChatManager::"
    answer_user_prompt = "/data/prompts/home_chat/run.txt"
    user_answerer = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "HOME_CHAT",
                                  AzureOpenAIConf.azure_gpt4_32_conf)

    user_message_start_tag, user_message_end_tag = "<message_body>", "</message_body>"
    user_message_header_start_tag, user_message_header_end_tag = "<message_header>", "</message_header>"


    def __init__(self, session_id, user, mojo_token_callback=None):
        self.logger = MojodexBackendLogger(
            f"{HomeChatManager.logger_prefix} -- session {session_id}")
        self.session_id = session_id
        self.user = user
        self.mojo_token_callback = mojo_token_callback
        self.task_suggestion_manager = TaskSuggestionManager(session_id, self.remove_tags_from_text)


    def __get_user_tasks(self):
        try:
            user_tasks = db.session.query(MdTask).\
                join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk).\
                filter(MdUserTask.user_id == self.user.user_id).all()
            return [{
                'task_pk': task.task_pk,
                'icon': task.icon,
                'name_for_system': task.name_for_system,
                'description': task.definition_for_system
            } for task in user_tasks]
        except Exception as e:
            raise Exception(f"__get_user_tasks :: {e}")

    def __get_this_week_home_conversations(self):
        try:
            # 1. get list of this week's home_chat sessions
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            sessions = db.session.query(MdSession)\
            .join(MdHomeChat, MdSession.session_id == MdHomeChat.session_id)\
            .filter(and_(MdHomeChat.start_date.isnot(None), MdHomeChat.start_date >= week_start_date))\
            .filter(MdSession.user_id == self.user.user_id)\
                .all()
            if not sessions:
                return []

            return [{
                "date": session.creation_date,
                "conversation": self.__get_conversation_as_string(session.session_id, agent_key="YOU", user_key="USER",
                                                                  with_tags=False)
            } for session in sessions]

        except Exception as e:
            raise Exception(f"__get_this_week_home_conversations :: {e}")

    def __get_this_week_task_executions(self):
        try:
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            # last 20 tasks executions of the user this week order by start_date
            user_task_executions = db.session.query(MdUserTaskExecution.title, MdUserTaskExecution.summary, MdTask.name_for_system) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                .filter(MdUserTask.user_id == self.user.user_id) \
                .filter(and_(MdUserTaskExecution.start_date.isnot(None), MdUserTaskExecution.start_date >= week_start_date)) \
                .order_by(MdUserTaskExecution.start_date.desc()) \
                .limit(20) \
                .all()
            return [{
                "title": execution.title,
                "summary": execution.summary,
                "task": execution.name_for_system
            } for execution in user_task_executions]
        except Exception as e:
            raise Exception(f"__get_this_week_task_executions :: {e}")


    @staticmethod
    def remove_tags_from_text(text, start_tag, end_tag):
        try:
            return text.split(start_tag)[1].split(end_tag)[0].strip() if start_tag in text else ""
        except Exception as e:
            raise Exception(f"remove_tags_from_text :: text: {text} - start_tag: {start_tag} - end_tag: {end_tag} - {e}")

    def __use_placeholder(self, user_message):
        try:
            return user_message["use_message_placeholder"] if (
                    "use_message_placeholder" in user_message) else False
        except Exception as e:
            return False

    def __token_callback(self, partial_text):
        try:
            partial_text = partial_text.strip()
            if not partial_text.lower().startswith("<"):
                # s'il y a pas de tags => go
                if self.mojo_token_callback:
                    self.mojo_token_callback(partial_text)
            else:
                # remove tags and stream
                text = HomeChatManager.remove_tags_from_text(partial_text, HomeChatManager.user_message_start_tag,
                                                         HomeChatManager.user_message_end_tag)
                if self.mojo_token_callback:
                    self.mojo_token_callback(text)
        except Exception as e:
            raise Exception(f"__token_callback :: {e}")

    def response_to_user_message(self, app_version, user_message):
        try:
            use_message_placeholder = self.__use_placeholder(user_message)
            return 'mojo_message', self.__answer_user(app_version, use_message_placeholder)
        except Exception as e:
            raise Exception(f"receive_human_message :: {e}")

    def generate_first_message(self, app_version, use_message_placeholder):
        try:
            return self.__answer_user(app_version, use_message_placeholder)
        except Exception as e:
            raise Exception(f"generate_first_message :: {e}")

    def __answer_user(self, app_version, use_message_placeholder=False):
        self.logger.debug(f"__answer_user")

        try:
            mojo_knowledge = KnowledgeManager.get_mojo_knowledge()
            global_context = KnowledgeManager.get_global_context_knowledge()
            previous_conversations = self.__get_this_week_home_conversations()
            user_tasks = self.__get_user_tasks()
            user_task_executions= self.__get_this_week_task_executions() if os.environ["ENVIRONMENT"] == "prod" else []
            conversation_list = self.__get_conversation_as_list()

            if use_message_placeholder:
                response = f"{HomeChatManager.user_message_start_tag}{placeholder_generator.mojo_message}{HomeChatManager.user_message_end_tag}"
                placeholder_generator.stream(response, self.__token_callback)
            else:

                with open(self.answer_user_prompt, 'r') as f:
                    template = Template(f.read())
                    home_chat_prompt = template.render(mojo_knowledge=mojo_knowledge,
                                                       global_context=global_context,
                                                       username=self.user.name,
                                                       tasks=user_tasks,
                                                       first_time_this_week=len(previous_conversations) == 0,
                                                       previous_conversations=previous_conversations,
                                                       user_task_executions=user_task_executions,
                                                       audio_message=True,
                                                       first_message=len(conversation_list) == 0,
                                                       language=self.user.language_code if self.user.language_code else "en"
                                                  )

                    with open("/data/home_chat_prompt.txt", "w") as f:
                        f.write(home_chat_prompt)


                    messages = [{"role": "system", "content": home_chat_prompt}] + conversation_list

                responses = HomeChatManager.user_answerer.chat(messages, self.user.user_id,
                                                           temperature=1, max_tokens=2000,
                                                           stream=True, stream_callback=self.__token_callback)

                response = responses[0].strip()

                with open("/data/home_chat_response.txt", "w") as f:
                    f.write(response)


            mojo_message = {"text_with_tags": response}
            if HomeChatManager.user_message_header_start_tag in response and len(conversation_list) == 0: # first message only
                header = HomeChatManager.remove_tags_from_text(response, HomeChatManager.user_message_header_start_tag,
                                                             HomeChatManager.user_message_header_end_tag)
                mojo_message["header"] = header

            if HomeChatManager.user_message_start_tag in response:
                body = HomeChatManager.remove_tags_from_text(response, HomeChatManager.user_message_start_tag,
                                                             HomeChatManager.user_message_end_tag)
                mojo_message["body"] = body

            if TaskSuggestionManager.task_pk_start_tag in response:
                task_response = self.task_suggestion_manager.manage_task_suggestion_text(response)
                # add all items of dict task_response to mojo_message
                mojo_message.update(task_response)
            if "header" in mojo_message and "body" in mojo_message:
                mojo_message["text"] = f"{mojo_message['header']}\n{mojo_message['body']}"
            elif "body" in mojo_message:
                mojo_message["text"] = mojo_message['body']
            else:
                mojo_message["text"] = response
            return mojo_message

        except Exception as e:
            raise Exception(f"__answer_user :: {e}")


    def __get_conversation_as_string(self, session_id, agent_key="Agent", user_key="User", with_tags=True):
        try:
            messages = self.__get_all_session_messages(session_id)
            conversation = ""
            for message in messages:
                if message.sender == "user":  # Session.user_message_key:
                    if "text" in message.message:
                        conversation += f"{user_key}: {message.message['text']}\n"
                elif message.sender == "mojo":  # Session.agent_message_key:
                    if "text" in message.message:
                        if "text_with_tags" in message.message and with_tags:
                            conversation += f"{agent_key}: {message.message['text_with_tags']}\n"
                        else:
                            conversation += f"{agent_key}: {message.message['text']}\n"
                else:
                    raise Exception("Unknown message sender")
            return conversation
        except Exception as e:
            raise Exception("_get_conversation_as_string: " + str(e))

    def __get_all_session_messages(self, session_id):
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == session_id).order_by(
                MdMessage.message_date).all()
            return messages
        except Exception as e:
            raise Exception("_get_all_session_messages: " + str(e))

    def __get_conversation_as_list(self, without_last_message=False, agent_key="assistant", user_key="user"):
        try:
            messages = self.__get_all_session_messages(self.session_id)
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

