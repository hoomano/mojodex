from background_logger import BackgroundLogger
from mojodex_core.json_loader import json_decode_retry

from mojodex_core.email_sender.email_service import EmailService
from mojodex_core.logging_handler import on_json_error

from models.events.events_generator import EventsGenerator

from models.knowledge.knowledge_collector import KnowledgeCollector

from mojodex_core.llm_engine.mpt import MPT


class CalendarSuggestionNotificationsGenerator(EventsGenerator):
    logger_prefix = "CalendarSuggestionNotificationsGenerator::"
    calendar_suggestion_notification_text_mpt_filename = "instructions/calendar_suggestion_reminder_notification.mpt"

    def __init__(self):
        self.logger = BackgroundLogger(
            f"{CalendarSuggestionNotificationsGenerator.logger_prefix}")
        self.logger.info("__init__")

    def generate_events(self, mojo_knowledge, calendar_suggestions):
        try:
            self.logger.info(" generate_events")
            for calendar_suggestion in calendar_suggestions:
                user_id = calendar_suggestion["user_id"]
                try:
                    user_datetime_context = KnowledgeCollector.get_global_context_knowledge(
                        calendar_suggestion["user_timezone_offset"])
                    notification_message = self.__generate_notif_text(mojo_knowledge, user_datetime_context,
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
                    EmailService().send_technical_error_email(
                        f"{self.logger.name} : Error preparing notification for user {user_id}: {e}")
        except Exception as e:
            EmailService().send_technical_error_email(
                f"{self.logger.name} : Error preparing notifications: {e}")

    @json_decode_retry(retries=3, required_keys=["title", "message"], on_json_error=on_json_error)
    def __generate_notif_text(self, mojo_knowledge, user_datetime_context, user_id, username, user_company_knowledge,
                              user_business_goal, calendar_suggestion, task_name):
        try:
            self.logger.info(f"generate_notif_text for user {user_id}")
            calendar_suggestion_notification = MPT(CalendarSuggestionNotificationsGenerator.calendar_suggestion_notification_text_mpt_filename, 
                                                   mojo_knowledge=mojo_knowledge,
                                                   user_datetime_context=user_datetime_context,
                                                   username=username,
                                                   user_company_knowledge=user_company_knowledge,
                                                   user_business_goal=user_business_goal,
                                                   calendar_suggestion=calendar_suggestion
                                                   )

            notification_message = calendar_suggestion_notification.run(user_id=user_id,
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
