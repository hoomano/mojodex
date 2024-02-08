from flask import request
from flask_restful import Resource
from app import db, executor
from db_models import *

from models.cortex.first_session_message_cortex import FirstSessionMessageCortex


class FirstSessionMessage(Resource):
    # A session just started, let's give it a title
    def post(self):
        try:
            session_id = request.json['session_id']
            timestamp = request.json['datetime']
            sender= request.json['sender']
            message = request.json['message']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            # check session exists
            session = db.session.query(MdSession).filter(MdSession.session_id == session_id).first()
            if session is None:
                return {"error": "session not found"}, 404

            cortex = FirstSessionMessageCortex(sender, message, session_id)
            def run_cortex(cortex):
                try:
                    cortex.generate_session_title()
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(run_cortex, cortex)
            return {"success": "Process started"}, 200
        except Exception as e:
            return {"error": f"Error in first session message : {e}"}, 404


