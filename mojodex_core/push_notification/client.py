import os
from mojodex_core.db import with_db_session
from mojodex_core.entities.db_base_entities import MdDevice
from mojodex_core.logging_handler import MojodexCoreLogger
from mojodex_core.push_notification.firebase_push_notification_sender import FirebasePushNotificationSender
from mojodex_core.push_notification.push_notification_sender import PushNotificationSender


class PushNotificationClient:  # Singleton
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PushNotificationClient, cls).__new__(
                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        try:
            self.push_notification_logger = MojodexCoreLogger("push_notification_logger")
            self._push_notification_sender: PushNotificationSender = self._configure_push_notification_sender()
        except Exception as e:
            self.push_notification_logger.error(f"Error initializing push notification client :: {e}")

    @property
    def configured(self):
        return self._push_notification_sender is not None

    def _configure_push_notification_sender(self) -> PushNotificationSender:
        try:
            push_notification_client = None
            if os.environ.get('FIREBASE_PROJECT_ID', ''):
                push_notification_client = FirebasePushNotificationSender()
                self.push_notification_logger.info("Firebase push notification client configured.")
            else:
                self.push_notification_logger.warning("No push notification client configured.")
            return push_notification_client
        except Exception as e:
            raise Exception(f"_configure_push_notification_sender: {e}")

    @with_db_session
    def send_notification(self, user_id: str, title: str, description: str, data: dict, db_session):
        """
        Collect all devices associated with a user. Sends a push notification to each device using self._push_notification_sender.
        """
        try:
            if self._push_notification_sender is None:
                raise Exception("No push notification client configured.")
            devices = db_session.query(MdDevice).filter(MdDevice.user_id == user_id).filter(
                MdDevice.valid == True).all()
            successes = 0
            for device in devices:
                try:
                    device_is_valid = self._push_notification_sender.send_notification(device.fcm_token, title, description, data)
                    if device_is_valid:
                        device.valid = True
                        successes += 1
                    else:
                        device.valid = False
                except Exception as e:
                    # No need to raise an exception if 1 call to a device fails, only log it and move on to the next device
                    self.push_notification_logger.error(f"{self.__class__.__name__} - error sending notification to device {device.device_id}: {e}")

            db_session.commit()
            return successes > 0
        except Exception as e:
            db_session.rollback()
            self.push_notification_logger.error(f"{self.__class__.__name__} send_notification: "
                                                f"- user_id {user_id} - title: {title} - description: {description} - data {data}: {e}")
