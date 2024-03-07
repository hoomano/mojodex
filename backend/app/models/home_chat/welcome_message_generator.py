from datetime import datetime, timedelta

from jinja2 import Template
from app import db, placeholder_generator
from models.knowledge.knowledge_manager import KnowledgeManager
from models.llm_calls.mojodex_openai import MojodexOpenAI
from db_models import *
from azure_openai_conf import AzureOpenAIConf
from sqlalchemy import and_

class WelcomeMessageGenerator:
    logger_prefix = "HomeChatManager::"
    first_message_prompt = "/data/prompts/home_chat/welcome_message.txt"
   
   
    first_message_generator = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "HOME_CHAT_FIRST_MESSAGE",
                                             AzureOpenAIConf.azure_gpt4_32_conf)

    first_message_header_start_tag, first_message_header_end_tag = "<message_header>", "</message_header>"
    first_message_body_start_tag, first_message_body_end_tag = "<message_body>", "</message_body>"



    def __init__(self, user):
        try:
            self.username = user.name
            self.language = user.language_code

        except Exception as e:
            raise Exception(f"{self.logger_prefix} :: __init__ :: {e}")


    def _get_user_tasks():
        pass

    def _get_all_session_messages(self, session_id):
        pass

    def __get_this_week_home_conversations(self):
        try:
            # 1. get list of this week's home_chat sessions
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            sessions = db.session.query(MdSession)\
            .join(MdHomeChat, MdSession.session_id == MdHomeChat.session_id)\
            .filter(and_(MdHomeChat.start_date.isnot(None), MdHomeChat.start_date >= week_start_date))\
            .filter(MdSession.user_id == self.user_id)\
                .all()
            if not sessions:
                return []

            return [{
                "date": session.creation_date,
                "conversation": self._get_conversation_as_string(session.session_id, agent_key="YOU", user_key="USER",
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
                .filter(MdUserTask.user_id == self.user_id) \
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

    def generate_first_message(self, use_message_placeholder):
        try:
            if use_message_placeholder:
                header = placeholder_generator.welcome_message_header_placeholder
                body = placeholder_generator.welcome_message_body_placeholder
                return {"header": header,
                    "body": body,
                    "text": f"{header}\n{body}"}
            previous_conversations = self.__get_this_week_home_conversations()
            with open(self.first_message_prompt, 'r') as f:
                template = Template(f.read())
                home_chat_prompt = template.render(mojo_knowledge=KnowledgeManager.get_mojo_knowledge(),
                                       global_context=KnowledgeManager.get_global_context_knowledge(),
                                       username=self.username,
                                       tasks=self._get_user_tasks(),
                                       first_time_this_week=len(previous_conversations) == 0,
                                       user_task_executions = self.__get_this_week_task_executions(),
                                       previous_conversations = previous_conversations,
                                       language=self.language)
            messages = [{"role": "system", "content": home_chat_prompt}]

            responses = WelcomeMessageGenerator.first_message_generator.chat(messages, self.user_id,
                                                           temperature=1, max_tokens=1000)

            response = responses[0].strip()
            header = WelcomeMessageGenerator.remove_tags_from_text(response, WelcomeMessageGenerator.first_message_header_start_tag,
                                                             WelcomeMessageGenerator.first_message_header_end_tag)
            body = WelcomeMessageGenerator.remove_tags_from_text(response, WelcomeMessageGenerator.first_message_body_start_tag,
                                                                WelcomeMessageGenerator.first_message_body_end_tag)
            return {"header": header,
                    "body": body,
                    "text": f"{header}\n{body}"}
        except Exception as e:
            raise Exception(f"generate_first_message :: {e}")


    def _get_conversation_as_string(self, session_id, agent_key="Agent", user_key="User", with_tags=True):
        try:
            messages = self._get_all_session_messages(session_id)
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

