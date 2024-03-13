from models.session.assistant_message_context.assistant_message_context import AssistantMessageContext
from models.session.assistant_message_generators.assistant_message_generator import AssistantMessageGenerator
from models.knowledge.knowledge_manager import KnowledgeManager
from datetime import datetime, timedelta
from app import db, placeholder_generator, llm, llm_conf, llm_backup_conf
from mojodex_core.entities import *
from sqlalchemy import and_

class WelcomeMessageGenerator(AssistantMessageGenerator):
    logger_prefix = "WelcomeMessageGenerator :: "
    prompt_template_path = "/data/prompts/home_chat/welcome_message.txt"
    welcome_message_generator = llm(llm_conf, label="HOME_CHAT_FIRST_MESSAGE", llm_backup_conf=llm_backup_conf)
    message_header_start_tag, message_header_end_tag = "<message_header>", "</message_header>"
    message_body_start_tag, message_body_end_tag = "<message_body>", "</message_body>"


    def __init__(self, user, use_message_placeholder, tag_proper_nouns=False):
        try:
            context = AssistantMessageContext(user)
            self.use_message_placeholder = use_message_placeholder
            super().__init__(WelcomeMessageGenerator.prompt_template_path, WelcomeMessageGenerator.welcome_message_generator, tag_proper_nouns, context)
        except Exception as e:
            raise Exception(f"{WelcomeMessageGenerator.logger_prefix} __init__ :: {e}")
        
    def _handle_placeholder(self):
        try:
            if self.use_message_placeholder:
                header = placeholder_generator.welcome_message_header_placeholder
                body = placeholder_generator.welcome_message_body_placeholder
                return {"header": header,
                    "body": body,
                    "text": f"{header}\n{body}"}
        except Exception as e:
            raise Exception(f"{WelcomeMessageGenerator.logger_prefix} _handle_placeholder :: {e}")

    def __get_available_user_tasks(self):
        try:
            user_tasks = db.session.query(MdTask).\
                join(MdUserTask, MdTask.task_pk == MdUserTask.task_fk).\
                filter(MdUserTask.user_id == self.context.user_id).\
                filter(MdUserTask.enabled==True).all()
            return [{
                'task_pk': task.task_pk,
                'icon': task.icon,
                'name_for_system': task.name_for_system,
                'description': task.definition_for_system
            } for task in user_tasks]
        except Exception as e:
            raise Exception(f"__get_available_user_tasks :: {e}")

    def _render_prompt_from_template(self):
        try:
            previous_conversations = self.__get_this_week_home_conversations()
            return self.prompt_template.render(mojo_knowledge=KnowledgeManager.get_mojo_knowledge(),
                                    global_context=KnowledgeManager.get_global_context_knowledge(),
                                    username=self.context.username,
                                    tasks=self.__get_available_user_tasks(),
                                    first_time_this_week=len(previous_conversations) == 0,
                                    user_task_executions = self.__get_this_week_task_executions(),
                                    previous_conversations = previous_conversations,
                                    language=self.context.user.language_code)
        except Exception as e:
            raise Exception(f"{WelcomeMessageGenerator.logger_prefix} _render_prompt_from_template :: {e}")

    def _generate_message_from_prompt(self, prompt):
        try:
            messages = [{"role": "system", "content": prompt}]
            responses = self.message_generator.invoke(messages, self.context.user_id, temperature=1, max_tokens=1000)
            return responses[0].strip()
        except Exception as e:
            raise Exception(f"{WelcomeMessageGenerator.logger_prefix} _generate_message_from_prompt :: {e}")

    def _handle_llm_output(self, llm_output):
        try:
            header = WelcomeMessageGenerator.remove_tags_from_text(llm_output, WelcomeMessageGenerator.message_header_start_tag,
                                                                WelcomeMessageGenerator.message_header_end_tag)
            body = WelcomeMessageGenerator.remove_tags_from_text(llm_output, WelcomeMessageGenerator.message_body_start_tag,
                                                                WelcomeMessageGenerator.message_body_end_tag)
            return {"header": header,
                    "body": body,
                    "text": f"{header}\n{body}"}
        except Exception as e:
            raise Exception(f"{WelcomeMessageGenerator.logger_prefix} _handle_llm_output :: {e}")

    ### SPECIFIC METHODS ###
    def __get_this_week_home_conversations(self):
        try:
            # 1. get list of this week's home_chat sessions
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            sessions = db.session.query(MdSession)\
            .join(MdHomeChat, MdSession.session_id == MdHomeChat.session_id)\
            .filter(and_(MdHomeChat.start_date.isnot(None), MdHomeChat.start_date >= week_start_date))\
            .filter(MdSession.user_id == self.context.user_id)\
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

    def _get_all_session_messages(self, session_id):
        try:
            messages = db.session.query(MdMessage).filter(MdMessage.session_id == session_id).order_by(
                MdMessage.message_date).all()
            return messages
        except Exception as e:
            raise Exception("_get_all_session_messages: " + str(e))

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

    def __get_this_week_task_executions(self):
        try:
            week_start_date = datetime.now().date() - timedelta(days=datetime.now().date().weekday())
            # last 20 tasks executions of the user this week order by start_date
            user_task_executions = db.session.query(MdUserTaskExecution.title, MdUserTaskExecution.summary, MdTask.name_for_system) \
                .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
                .join(MdTask, MdUserTask.task_fk == MdTask.task_pk) \
                .filter(MdUserTask.user_id == self.context.user_id) \
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
