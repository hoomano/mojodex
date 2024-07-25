import os
from flask import request
from flask_restful import Resource
from mojodex_core.authentication import authenticate_with_scheduler_secret
from mojodex_core.logging_handler import log_error
from mojodex_core.push_notification.push_notification_service import PushNotificationService


class IsPushNotifServiceConfigured(Resource):

    def __init__(self):
        IsPushNotifServiceConfigured.method_decorators = [authenticate_with_scheduler_secret(methods=["GET"])]


    def get(self):
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
        