import os
from jinja2 import Template

from mojodex_core.email_sender.email_service import EmailService

from mojodex_core.knowledge_manager import KnowledgeManager
from models.events.events_generator import EventsGenerator
from mojodex_core.json_loader import json_decode_retry
from mojodex_core.logging_handler import log_error, on_json_error
from mojodex_core.llm_engine.mpt import MPT


class TodoDailyEmailsGenerator(EventsGenerator):

    message_from_mojodex_email = "mojodex_core/mails_templates/message_from_mojodex.html"
    todo_daily_email_text_mpt_filename = "instructions/todo_daily_emails_text_prompt.mpt"
    todo_daily_email_type = "todo_daily_email"

    def generate_events(self, users):
        try:
            for user in users:
                user_id, email = user["user_id"], user["email"]
                email_json = self._generate_emails_text(KnowledgeManager().mojodex_knowledge, user["datetime_context"], user_id,
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
                        body = template.render(mojodex_message=body, mojodex_webapp_url=os.environ["MOJODEX_WEBAPP_URI"],
                                               button_text="View To-do List")
                    self.send_event(user_id, message={"subject": subject, "body": body, 'email': email},
                                    event_type=TodoDailyEmailsGenerator.todo_daily_email_type)
                except Exception as e:
                    EmailService().send_technical_error_email(
                        f"{self.__class__.__name__} : generate_events : Error sending todo daily remind_email to {email} : {e}")

        except Exception as e:
            EmailService().send_technical_error_email(
                f"{self.__class__.__name__} : generate_events : Error preparing emails: {e}")

    @json_decode_retry(retries=3, required_keys=["subject", "body"], on_json_error=on_json_error)
    def _generate_emails_text(self, mojo_knowledge, user_datetime_context, user_id, username, user_company_knowledge,
                               user_business_goal, language, today_todo_list, rescheduled_todos, deleted_todos):
        try:
            todo_daily_email_text = MPT(TodoDailyEmailsGenerator.todo_daily_email_text_mpt_filename,
                                        mojo_knowledge=mojo_knowledge,
                                        user_datetime_context=user_datetime_context,
                                        username=username,
                                        user_company_knowledge=user_company_knowledge,
                                        user_business_goal=user_business_goal,
                                        todo_list=today_todo_list,
                                        rescheduled_todo_items=rescheduled_todos,
                                        deleted_todo_items=deleted_todos,
                                        language=language
                                        )
            
            email_message_json = todo_daily_email_text.run(user_id=user_id,
                                                           temperature=0,
                                                           max_tokens=4000,
                                                           json_format=True)[0]
            return email_message_json
        except Exception as e:
            raise Exception(f"_generate_emails_text: {e}")
