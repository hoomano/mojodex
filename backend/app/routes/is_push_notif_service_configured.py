import os
from flask import request
from flask_restful import Resource
from mojodex_core.logging_handler import log_error
from mojodex_core.push_notification.push_notification_service import PushNotificationService


class IsPushNotifServiceConfigured(Resource):

    def get(self):
        try:
           secret = request.headers['Authorization']
           if secret != os.environ["MOJODEX_SCHEDULER_SECRET"]:
               log_error(f"Error with route IsPushNotifServiceConfigured : Authentication error : Wrong secret", notify_admin=True)
               return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
           log_error(f"Error with route IsPushNotifServiceConfigured : Missing Authorization secret in headers", notify_admin=True)
           return {"error": f"Missing Authorization secret in headers"}, 403
        
        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error getting push notifications service configuration : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400
        
        try:
            return {"is_configured": PushNotificationService().configured}
        except Exception as e:
            log_error(f"Error getting push notifications service configuration : {e}")
            return {"error": f"Error getting push notifications service configuration : {e}"}, 500
        