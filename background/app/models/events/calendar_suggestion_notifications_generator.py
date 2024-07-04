from mojodex_core.json_loader import json_decode_retry
from mojodex_core.knowledge_manager import KnowledgeManager
from mojodex_core.logging_handler import log_error, on_json_error
from models.events.events_generator import EventsGenerator
from mojodex_core.llm_engine.mpt import MPT


class CalendarSuggestionNotificationsGenerator(EventsGenerator):
    calendar_suggestion_notification_text_mpt_filename = "instructions/calendar_suggestion_reminder_notification.mpt"

    def generate_events(self, calendar_suggestions):
        try:
            for calendar_suggestion in calendar_suggestions:
                user_id = calendar_suggestion["user_id"]
                try:
                    notification_message = self._generate_notif_text(KnowledgeManager().mojodex_knowledge, user["datetime_context"],
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
                    log_error(
                        f"{self.__class__.__name__} : generate_events: Error preparing notification for user {user_id}: {e}", notify_admin=True)
        except Exception as e:
            log_error(
                f"{self.__class__.__name__} : generate_events: {e}", notify_admin=True)


    @json_decode_retry(retries=3, required_keys=["title", "message"], on_json_error=on_json_error)
    def _generate_notif_text(self, mojo_knowledge, user_datetime_context, user_id, username, user_company_knowledge,
                              user_business_goal, calendar_suggestion, task_name):
        try:
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
            raise Exception(f"_generate_notif_text: {e}")
