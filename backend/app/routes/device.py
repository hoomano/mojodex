from app import authenticate, db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from flask import request
from flask_restful import Resource
from datetime import datetime


class Device(Resource):

    def __init__(self):
        Device.method_decorators = [authenticate()]

    def put(self, user_id):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            fcm_token = request.json["fcm_token"]
        except KeyError as e:
            log_error(f"Error creating device for user {user_id}: Missing field {e} - request.json: {request.json}",
                      notify_admin=True)
            return {"error": f"Missing input: {e}"}, 400

        # Logic
        try:
            device = MdDevice(
                user_id=user_id,
                creation_date=datetime.now(),
                fcm_token=fcm_token
            )
            db.session.add(device)
            db.session.commit()
            return {"device_pk": device.device_pk}, 200
        except Exception as e:
            log_error(f"Error creating device for user {user_id} - fcm_token: {fcm_token}: {e}", notify_admin=True)
            return {"error": "Error creating device"}, 400
