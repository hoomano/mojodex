from flask import request
from flask_restful import Resource
from mojodex_core.logging_handler import log_error
from mojodex_core.email_sender.email_service import EmailService


class IsEmailServiceConfigured(Resource):

    def get(self):
        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error getting email service configuration : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400
        
        try:
            return {"is_configured": EmailService().configured}
        except Exception as e:
            log_error(f"Error getting email service configuration : {e}")
            return {"error": f"Error getting email service configuration : {e}"}, 500
        