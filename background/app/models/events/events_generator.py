import os
from abc import ABC, abstractmethod
from datetime import datetime
from mojodex_core.db import with_db_session
from mojodex_core.email_sender.email_service import EmailService
from mojodex_core.entities.db_base_entities import MdEvent
from mojodex_core.logging_handler import log_error
from mojodex_core.push_notification.push_notification_service import PushNotificationService


class EventsGenerator(ABC):

    @abstractmethod
    def generate_events(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def send_event(self, user_id, message, event_type, data=None):
        raise NotImplementedError
    
    @with_db_session
    def _add_event_to_db(self, creation_date, event_type, user_id, message, db_session):
        try:
            event = MdEvent(creation_date=creation_date, event_type=event_type,
                            user_id=user_id,
                            message=message)
            db_session.add(event)
            db_session.commit()
        except Exception as e:
            raise Exception(f"_add_event_to_db: {e}")
        
        

class EmailEventGenerator(EventsGenerator, ABC):

    def send_event(self, user_id, event_type, subject, body, email_address):
        try:
            EmailService().send(subject=subject,recipients=[email_address], html_body=body)
            self._add_event_to_db(creation_date=datetime.now(), event_type=event_type, user_id=user_id,
                                    message={"subject": subject, "body": body, 'email': email_address})
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : send_event: {e}")
        

class PushNotificationEventGenerator(EventsGenerator, ABC):
    
    def send_event(self, user_id, event_type, notification_title, notification_body, data):
        try:
            success = PushNotificationService().send(user_id, notification_title, notification_body, data)
            if success:
                self._add_event_to_db(creation_date=datetime.now(), event_type=event_type, user_id=user_id,
                                        message={"title": notification_title, "body": notification_body})
            else:
                log_error(f"Mojo tried to send a notification to user {user_id} but failed either because "
                            "the user has no device or because the notification failed to be sent on every devices.")
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : send_event: {e}")