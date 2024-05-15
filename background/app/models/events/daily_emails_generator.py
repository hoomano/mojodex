
import os
from jinja2 import Template

from background_logger import BackgroundLogger
from mojodex_core.json_loader import json_decode_retry


from mojodex_core.mail import send_technical_error_email
from mojodex_core.logging_handler import on_json_error

from models.events.events_generator import EventsGenerator

from models.knowledge.knowledge_collector import KnowledgeCollector

from mojodex_core.llm_engine.mpt import MPT


class DailyEmailsGenerator(EventsGenerator):
    logger_prefix = "DailyEmailsGenerator::"
    message_from_mojodex_email = "/data/mails/message_from_mojodex.html"
    daily_email_text_mpt_filename = "instructions/daily_emails_text_prompt.mpt"

    reminder_email_type = "reminder_email"
    summary_email_type = "summary_email"

    def __init__(self):
        self.logger = BackgroundLogger(f"{DailyEmailsGenerator.logger_prefix}")
        self.logger.info("__init__")

    def generate_events(self, mojo_knowledge, users):
        try:
            self.logger.info("generate_events")
            for user in users:
                user_id, email = user["user_id"], user["email"]
                # Temporarily removed because it felt too much to send users an email every day
                # if user['n_meeting_minutes_today'] > 0:
               #     email_body_template = Template("""Hey!
                #                                    It was a busy day:
                #                                    {{n_meeting_minutes}} meetings
                #                                    {%if n_processes_created_today > 0%}{{n_processes_created_today}} followup items{%endif%}
                #
                #                                    {%if last_three_proactive_followups%}I prepared for you to review and use:
                #                                   {%for followup in last_three_proactive_followups%}
                #                                   {{followup}}{%endfor%}{%endif%}
#
                #                                   {%if additional_feature %}I’m sure I can do more, like {{additional_feature}}.{%else%}I'm always here to help.{%endif%}
                #                                  Just ask me.""")
                #  try:
                #      email_body = email_body_template.render(n_meeting_minutes=user['n_meeting_minutes_today'],
                #                                              n_processes_created_today=user[
                #                                                  'n_processes_created_today'],
                #                                             last_three_proactive_followups=user[
                #                                                 'last_three_proactive_followups'],
                #                                             additional_feature=user[
                #                                                'first_enabled_not_executed_task_name'])

                #    self.send_event(user_id, message={"subject": "subject", "body": email_body, 'email': email},
                #                    event_type=DailyEmailsGenerator.summary_email_type)
                # except Exception as e:
                #    send_admin_error_email(f"Error sending daily recap email to {email} : {e}")
                if user['n_meeting_minutes_today'] == 0:
                    global_context = KnowledgeCollector.get_global_context_knowledge(
                        user["user_timezone_offset"])
                    email_message = self.__generate_emails_text(mojo_knowledge, global_context, user_id,
                                                                user["user_name"],
                                                                user["user_company_description"], user["user_goal"],
                                                                user["received_reminder_email_yesterday"],
                                                                user["language"])
                    subject, body = email_message["subject"], email_message["body"]
                    try:
                        with open(DailyEmailsGenerator.message_from_mojodex_email, "r") as f:
                            template = Template(f.read())
                            body = template.render(
                                mojodex_message=body, mojodex_link=os.environ["MOJODEX_WEBAPP_URI"], button_text="Login")
                        self.send_event(user_id, message={"subject": subject, "body": body, 'email': email},
                                        event_type=DailyEmailsGenerator.reminder_email_type)
                    except Exception as e:
                        send_technical_error_email(
                            f"Error sending daily remind_email to {email} : {e}")

        except Exception as e:
            send_technical_error_email(
                f"{self.logger.name} : Error preparing emails: {e}")

    @json_decode_retry(retries=3, required_keys=["subject", "body"], on_json_error=on_json_error)
    def __generate_emails_text(self, mojo_knowledge, global_context, user_id, username, user_company_knowledge,
                               user_business_goal,
                               received_reminder_email_yesterday, language, retry=2):
        try:
            self.logger.info(f"generate_emails_text for user {user_id}")
            daily_email_text = MPT(DailyEmailsGenerator.daily_email_text_mpt_filename,
                                   mojo_knowledge=mojo_knowledge,
                                   global_context=global_context,
                                   username=username,
                                   user_company_knowledge=user_company_knowledge,
                                   user_business_goal=user_business_goal,
                                   received_reminder_email_yesterday=received_reminder_email_yesterday,
                                   language=language
                                   )

            email_message = daily_email_text.run(user_id=user_id,
                                                 temperature=1, max_tokens=500,
                                                 json_format=True)[0]
            return email_message
        except Exception as e:
            raise Exception(f"generate_notif_text: " + str(e))
