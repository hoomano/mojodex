import os

from jinja2 import Template

from background_logger import BackgroundLogger


from app import send_admin_error_email

from models.events.events_generator import EventsGenerator
from mojodex_core.json_loader import json_decode_retry
from app import on_json_error

from models.knowledge.knowledge_collector import KnowledgeCollector

from mojodex_core.llm_engine.mpt import MPT


class TodoDailyEmailsGenerator(EventsGenerator):
    logger_prefix = "TodoDailyEmailsGenerator::"
    message_from_mojodex_email = "/data/mails/message_from_mojodex.html"
    todo_daily_email_text_mpt_filename = "background/app/instructions/todo_daily_emails_text_prompt.mpt"
    todo_daily_email_type = "todo_daily_email"

    def __init__(self):
        self.logger = BackgroundLogger(
            f"{TodoDailyEmailsGenerator.logger_prefix}")
        self.logger.info("__init__")

    def generate_events(self, mojo_knowledge, users):
        try:
            self.logger.info("generate_events")
            for user in users:
                user_id, email = user["user_id"], user["email"]
                global_context = KnowledgeCollector.get_global_context_knowledge(
                    user["user_timezone_offset"])
                email_json = self.__generate_emails_text(mojo_knowledge, global_context, user_id,
                                                         user["username"],
                                                         user["company_description"], user["goal"],
                                                         user["language"],
                                                         user["today_todo_list"],
                                                         user["rescheduled_todos"],
                                                         user["deleted_todos"])

                subject, body = email_json["subject"], email_json["body"]
                try:
                    with open(TodoDailyEmailsGenerator.message_from_mojodex_email, "r") as f:
                        template = Template(f.read())
                        body = template.render(mojodex_message=body, mojodex_link=os.environ["MOJODEX_WEBAPP_URI"],
                                               button_text="View To-do List")
                    self.send_event(user_id, message={"subject": subject, "body": body, 'email': email},
                                    event_type=TodoDailyEmailsGenerator.todo_daily_email_type)
                except Exception as e:
                    send_admin_error_email(
                        f"Error sending todo daily remind_email to {email} : {e}")

        except Exception as e:
            send_admin_error_email(
                f"{self.logger.name} : Error preparing emails: {e}")

    @json_decode_retry(retries=3, required_keys=["subject", "body"], on_json_error=on_json_error)
    def __generate_emails_text(self, mojo_knowledge, global_context, user_id, username, user_company_knowledge,
                               user_business_goal, language, today_todo_list, rescheduled_todos, deleted_todos):
        try:
            self.logger.info(f"generate_emails_text for user {user_id}")
            todo_daily_email_text = MPT(TodoDailyEmailsGenerator.todo_daily_email_text_mpt_filename,
                                        mojo_knowledge=mojo_knowledge,
                                        global_context=global_context,
                                        username=username,
                                        user_company_knowledge=user_company_knowledge,
                                        user_business_goal=user_business_goal,
                                        todo_list=today_todo_list,
                                        rescheduled_todo_items=rescheduled_todos,
                                        deleted_todo_items=deleted_todos,
                                        language=language
                                        )
            
            email_message_json = todo_daily_email_text.run(user_id,
                                                           temperature=0,
                                                           max_tokens=4000,
                                                           json_format=True)[0]
            return email_message_json
        except Exception as e:
            raise Exception(f"generate_email_text: " + str(e))
