from mojodex_core.db import with_db_session
from mojodex_core.entities.db_base_entities import MdCalendarSuggestion, MdTask
from mojodex_core.entities.user import User
from mojodex_core.json_loader import json_decode_retry

from mojodex_core.email_sender.email_service import EmailService
from mojodex_core.knowledge_manager import KnowledgeManager
from mojodex_core.logging_handler import on_json_error
from models.events.events_generator import PushNotificationEventGenerator
from mojodex_core.llm_engine.mpt import MPT


class CalendarSuggestionNotificationsGenerator(PushNotificationEventGenerator):
    calendar_suggestion_notification_text_mpt_filename = "instructions/calendar_suggestion_reminder_notification.mpt"

    def __init__(self, user_id, since_date, until_date):
        self.user_id = user_id
        self.since_date = since_date
        self.until_date = until_date
        super().__init__()

    @with_db_session
    def _collect_data(self, db_session):
        try:
            user: User = db_session.query(User).get(self.user_id)
            calendar_suggestion, task = db_session.query(MdCalendarSuggestion, MdTask) \
                .join(MdTask, MdTask.task_pk == MdCalendarSuggestion.proposed_task_fk) \
                .filter(MdCalendarSuggestion.reminder_date.isnot(None)) \
                .filter(MdCalendarSuggestion.reminder == True) \
                .filter(MdCalendarSuggestion.reminder_date.between(self.since_date, self.until_date)) \
                .filter(MdCalendarSuggestion.user_id == self.user_id) \
                .first()

            return user.datetime_context, user.name, user.company_description, user.goal, calendar_suggestion.suggestion_text, task.name_for_system, task.task_pk
        except Exception as e:
            raise Exception(f"_collect_data: {e}")

    def generate_events(self):
        try:
            collected_data = self._collect_data()
            task_pk = collected_data[-1]
            notification_message = self._generate_notif_text(*collected_data[:-1])

            notification_title, notification_body = notification_message["title"], notification_message["message"]
            data = {"user_id": self.user_id,
                    "task_pk": str(task_pk),
                    "type": "calendar_suggestion"}
            self.send_event(self.user_id,
                            event_type="calendar_suggestion_notification", 
                            notification_title=notification_title,
                            notification_body=notification_body,
                            data=data)
        except Exception as e:
            EmailService().send_technical_error_email(
                f"{self.__class__.__name__} : generate_events: Error preparing notifications: {e}")

    @json_decode_retry(retries=3, required_keys=["title", "message"], on_json_error=on_json_error)
    def _generate_notif_text(self, user_datetime_context, username, user_company_knowledge,
                              user_business_goal, calendar_suggestion, task_name):
        try:
            calendar_suggestion_notification = MPT(CalendarSuggestionNotificationsGenerator.calendar_suggestion_notification_text_mpt_filename, 
                                                   mojo_knowledge=KnowledgeManager().mojodex_knowledge,
                                                   user_datetime_context=user_datetime_context,
                                                   username=username,
                                                   user_company_knowledge=user_company_knowledge,
                                                   user_business_goal=user_business_goal,
                                                   calendar_suggestion=calendar_suggestion
                                                   )

            notification_message = calendar_suggestion_notification.run(user_id=self.user_id,
                                                                        temperature=1,
                                                                        max_tokens=50,
                                                                        json_format=True,
                                                                        user_task_execution_pk=None,
                                                                        task_name_for_system=task_name
                                                                        )
            # try to load as json to extract title and body
            return notification_message
        except Exception as e:
            raise Exception(f"_generate_notif_text: {e}")
