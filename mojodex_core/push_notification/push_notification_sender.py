from abc import ABC, abstractmethod


class PushNotificationSender(ABC):

    @abstractmethod
    def send_notification(self, device_fcm_token: str,  title: str, description: str, data: dict):
        pass

