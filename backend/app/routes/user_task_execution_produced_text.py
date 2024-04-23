from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import MdProducedText, MdProducedTextVersion


class UserTaskExecutionProducedText(Resource):

    def __init__(self):
        UserTaskExecutionProducedText.method_decorators = [authenticate(methods=["GET"])]

    def get(self, user_id):
        error_message = "Error getting user_task_execution's produced_text"
        try:
            timestamp = request.args["datetime"]
            produced_text_version_index = int(request.args["produced_text_version_index"])
            user_task_execution_pk = request.args["user_task_execution_pk"]
        except KeyError as e:
            log_error(f"{error_message}: Missing field {e}")
            return {"error": f"Missing field {e}"}, 400
        
        try:
            # ensure produced_text_version_index is > 0
            if produced_text_version_index <= 0:
                return {"error": "produced_text_version_index must be > 0"}, 400
            # get index produced_text_version_index of user_task_execution's produced_text
            produced_text_version = db.session.query(MdProducedTextVersion) \
                .join(MdProducedText, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .filter(MdProducedText.user_task_execution_fk == user_task_execution_pk) \
                .order_by(MdProducedTextVersion.creation_date) \
                .offset(produced_text_version_index-1) \
                .first()
            
            if produced_text_version is None:
                return {'produced_text_version_pk': None}, 200
            
            return {'produced_text_version_pk': produced_text_version.produced_text_version_pk,
                    'produced_text_pk': produced_text_version.produced_text_fk,
                    'produced_text_title': produced_text_version.title,
                    'produced_text_production': produced_text_version.production,
                    'produced_text_version_index': produced_text_version_index,
                    }, 200
        except Exception as e:
            log_error(f"{error_message}: {str(e)}")
            return {"error": str(e)}, 400
        
