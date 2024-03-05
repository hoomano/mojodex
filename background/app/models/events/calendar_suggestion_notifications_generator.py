import json

from jinja2 import Template

from background_logger import BackgroundLogger
from mojodex_background_openai import MojodexBackgroundOpenAI
from mojodex_core.json_loader import json_decode_retry
from azure_openai_conf import AzureOpenAIConf

from app import send_admin_error_email, on_json_error

from models.events.events_generator import EventsGenerator

from models.knowledge.knowledge_collector import KnowledgeCollector


class CalendarSuggestionNotificationsGenerator(EventsGenerator):
    logger_prefix = "CalendarSuggestionNotificationsGenerator::"
    calendar_suggestion_notification_text_prompt = "/data/prompts/engagement/notifications/calendar_suggestion_reminder_notification.txt"
    calendar_suggestion_notification_text_generator = MojodexBackgroundOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf,
                                                                "CALENDAR_SUGGESTION_NOTIFICATION")

    def __init__(self):
        self.logger = BackgroundLogger(f"{CalendarSuggestionNotificationsGenerator.logger_prefix}")
        self.logger.info("__init__")

    def generate_events(self, mojo_knowledge, calendar_suggestions):
        try:
            self.logger.info(" generate_events")
            for calendar_suggestion in calendar_suggestions:
                user_id = calendar_suggestion["user_id"]
                try:
                    global_context = KnowledgeCollector.get_global_context_knowledge(
                        calendar_suggestion["user_timezone_offset"])
                    notification_message = self.__generate_notif_text(mojo_knowledge, global_context,
                                                                      user_id,
                                                                      calendar_suggestion["user_name"],
                                                                      calendar_suggestion[
                                                                          "user_company_description"],
                                                                      calendar_suggestion["user_goal"],
                                                                      calendar_suggestion["suggestion_text"],
                                                                      calendar_suggestion["task_name"])

                    notification_title, notification_body = notification_message["title"], notification_message[
                        "message"]
                    data = {"user_id": user_id,
                            "task_pk": str(calendar_suggestion["task_pk"]),
                            "type": "calendar_suggestion"}
                    self.send_event(user_id, message={"title": notification_title, "body": notification_body},
                                    event_type="calendar_suggestion_notification", data=data)
                except Exception as e:
                    send_admin_error_email(f"{self.logger.name} : Error preparing notification for user {user_id}: {e}")
        except Exception as e:
            send_admin_error_email(f"{self.logger.name} : Error preparing notifications: {e}")

    @json_decode_retry(retries=3, required_keys=["title", "message"], on_json_error=on_json_error)
    def __generate_notif_text(self, mojo_knowledge, global_context, user_id, username, user_company_knowledge,
                              user_business_goal, calendar_suggestion, task_name):
        try:
            self.logger.info(f"generate_notif_text for user {user_id}")
            with open(CalendarSuggestionNotificationsGenerator.calendar_suggestion_notification_text_prompt, "r") as f:
                template = Template(f.read())

                prompt = template.render(
                    mojo_knowledge=mojo_knowledge,
                    global_context=global_context,
                    username=username,
                    user_company_knowledge=user_company_knowledge,
                    user_business_goal=user_business_goal,
                    calendar_suggestion=calendar_suggestion
                )

            # call openai to generate text
            messages = [{"role": "system", "content": prompt}]
            notification_message = \
                CalendarSuggestionNotificationsGenerator.calendar_suggestion_notification_text_generator.chat(messages, user_id,
                                                                                                    temperature=1,
                                                                                                    max_tokens=50,
                                                                                                    json_format=True,
                                                                                                    user_task_execution_pk=None,
                                                                                                    task_name_for_system=task_name
                                                                                                    )[0]
            # try to load as json to extract title and body
            return notification_message
        except Exception as e:
            raise Exception(f"generate_notif_text: " + str(e))
