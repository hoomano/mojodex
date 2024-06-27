import json
import requests
from google.oauth2 import service_account
from mojodex_core.logging_handler import log_error
import google.auth.transport.requests
import os
from mojodex_core.push_notification.push_notification_sender import PushNotificationSender


class FirebasePushNotificationSender(PushNotificationSender):

    def __init__(self):
        try:
            self.project_id = os.environ['FIREBASE_PROJECT_ID']
        except Exception as e:
            log_error(f"{self.__class__.__name__} __init__: {e}", notify_admin=True)

    def _get_access_token(self):
        try:
            credentials = service_account.Credentials.from_service_account_info(
                json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT']),
                scopes=['https://www.googleapis.com/auth/firebase.messaging'])

            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            return credentials.token
        except Exception as e:
            raise Exception(f"_get_access_token: {e}")

    def send_notification(self, device_fcm_token: str, title: str, description: str, data: dict):
        try:
            access_token = self._get_access_token()
            return self._send_notification_to_device(access_token, device_fcm_token, title, description, data)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} send_notification: {e}")

    def _send_notification_to_device(self, access_token, device_fcm_token, title, description, data):
        """
        Tries to send a push notification to a device using its fcm token.
        Return true if device is valid and notification is sent successfully, false otherwise.
        :param access_token:
        :param device_fcm_token:
        :param title:
        :param description:
        :param data:
        :return:
        """
        try:
            base_url = f'https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send'
            headers = {'Authorization': 'Bearer ' + access_token,
                       'Content-Type': 'application/json; UTF-8'}
            data = {
                "message": {
                    "token": device_fcm_token,  # token of the user
                    "notification": {
                        "title": title,
                        "body": description
                    },
                    "data": data,
                }
            }
            resp = requests.post(base_url, json=data, headers=headers)
            if resp.status_code == 404 and resp.json()['error']['status'] == 'INVALID_ARGUMENT':
                # Not sure what to do because:
                # "INVALID_ARGUMENT is thrown in case of invalid fcm_token and also in cases of issues in the message payload,
                # it signals an invalid token only if the payload is completely valid."
                # https://firebase.google.com/docs/cloud-messaging/manage-tokens
                # There is a message coming along. We will check the message, if it is the one I observed, we will invalidate the device,
                # otherwise, send an email to admin so that we can investigate
                if resp.json()['error']['message'] == "The registration token is not a valid FCM registration token":
                    return False
                else:
                    raise Exception(f"{resp.status_code}: {resp.text}")
            elif resp.status_code == 400 and resp.json()['error']['status'] == 'UNREGISTERED':
                return False
            elif resp.status_code != 200:
                raise Exception(f"{resp.status_code}: {resp.text}")
            return True
        except Exception as e:
            raise Exception(f"_send_notification_to_device: {e}")

