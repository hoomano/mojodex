from flask import request
from flask_restful import Resource
from mojodex_core.logging_handler import log_error
from app import mojo_mail_client


class IsEmailServiceConfigured(Resource):

    def get(self):
        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error getting email service configuration : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400
        
        try:
            return {"is_configured": mojo_mail_client is not None}
        except Exception as e:
            log_error(f"Error getting email service configuration : {e}")
            return {"error": f"Error getting email service configuration : {e}"}, 500
        