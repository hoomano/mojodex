import json

import requests
from google.oauth2 import service_account
from db_models import *
from mojodex_backend_logger import MojodexBackendLogger
from app import log_error, db
import google.auth.transport.requests
import os

class PushNotificationSender:
    logger_prefix = "PushNotificationSender::"

    def __init__(self):
        try:
            self.logger = MojodexBackendLogger(f"{PushNotificationSender.logger_prefix}")
            self.project_id = os.environ['FIREBASE_PROJECT_ID']
        except Exception as e:
            log_error(f"{self.logger_prefix} __init__: {e}", notify_admin=True)

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

    def send_notification_to_user(self, user_id, title, description, data):
        try:
            access_token = self._get_access_token()
            devices = db.session.query(MdDevice).filter(MdDevice.user_id == user_id).filter(
                MdDevice.valid == True).all()
            successes = 0
            for device in devices:
                success = self._send_notification_to_device(access_token, device, title, description, data)
                if success:
                    successes += 1
            return successes > 0
        except Exception as e:
            log_error(f"{self.logger_prefix} send_notification_to_user: "
                      f"- user_id {user_id} - title: {title} - description: {description} - data {data}: {e}", notify_admin=True)

    def _send_notification_to_device(self, access_token, device, title, description, data):
        try:
            base_url = f'https://fcm.googleapis.com/v1/projects/{self.project_id}/messages:send'
            headers = {'Authorization': 'Bearer ' + access_token,
                       'Content-Type': 'application/json; UTF-8'}
            data = {
                "message": {
                    "token": device.fcm_token,  # token of the user
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
                    self._invalidate_device(device)
                else:
                    raise Exception(f"{resp.status_code}: {resp.text}")
            elif resp.status_code == 400 and resp.json()['error']['status'] == 'UNREGISTERED':
                self._invalidate_device(device)
            elif resp.status_code != 200:
                raise Exception(f"{resp.status_code}: {resp.text}")
            return True
        except Exception as e:
            return False

    def _invalidate_device(self, device):
        try:
            device.valid = False
            db.session.commit()
        except Exception as e:
            log_error(
                f"{self.logger_prefix} _invalidate_device: {e}",
                notify_admin=True)
