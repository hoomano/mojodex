import os
from datetime import datetime
from sqlalchemy import func
from flask import request
from flask_restful import Resource
from app import db, authenticate, authenticate_function
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *


from models.produced_text_managers.produced_text_manager import ProducedTextManager


class ProducedText(Resource):

    def __init__(self):
        ProducedText.method_decorators = [authenticate(methods=["GET", "DELETE"])]

    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error getting produced_text : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            if "produced_text_pk" in request.args:
                produced_text_pk = int(request.args["produced_text_pk"])
                result = db.session.query(MdProducedText, MdProducedTextVersion)\
                    .join(MdProducedTextVersion, MdProducedText.produced_text_pk == MdProducedTextVersion.produced_text_fk)\
                    .filter(MdProducedText.user_id == user_id)\
                    .filter(MdProducedText.deleted_by_user == None)\
                    .filter(MdProducedText.produced_text_pk == produced_text_pk).order_by(MdProducedTextVersion.creation_date.desc()).first()

                if result is None:
                    log_error(f"Error getting produced_text : ProducedText with produced_text_pk {produced_text_pk} does not exist for this user")
                    return {"error": f"Invalid produced_text produced_text_pk: {produced_text_pk} for this user"}, 400
                produced_text, produced_text_version = result
                text_type = db.session.query(MdTextType.name).filter(MdTextType.text_type_pk == produced_text_version.text_type_fk).first()
                return {"produced_text_pk": produced_text.produced_text_pk,
                        "user_task_execution_fk": produced_text.user_task_execution_fk,
                        "user_id": produced_text.user_id,
                        "production": produced_text_version.production,
                        "title": produced_text_version.title,
                        "creation_date": produced_text_version.creation_date.isoformat(),
                        "text_type": text_type[0] if text_type is not None else None,
                        }, 200

            # if no produced_text_pk is provided, return n_produced_texts first produced_texts
            n_produced_texts = min(50, int(request.args["n_produced_texts"])) if "n_produced_texts" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0

            latest = db.session.query(
                MdProducedTextVersion.produced_text_fk,
                func.max(MdProducedTextVersion.creation_date).label('max_creation_date')
            ).group_by(MdProducedTextVersion.produced_text_fk).subquery()

            # Execute the query
            results = db.session.query(
                MdProducedText, MdProducedTextVersion
            ).join(
                latest,
                (MdProducedTextVersion.produced_text_fk == latest.c.produced_text_fk)
                & (MdProducedTextVersion.creation_date == latest.c.max_creation_date)
            ).join(
            MdProducedText,
            (MdProducedText.produced_text_pk == MdProducedTextVersion.produced_text_fk)
            & (MdProducedText.deleted_by_user == None)
            & (MdProducedText.user_id == user_id)
            ).order_by(MdProducedTextVersion.creation_date.desc()).limit(n_produced_texts).offset(offset).all()

            text_type = db.session.query(MdTextType.name).filter(
                MdTextType.text_type_pk == produced_text_version.text_type_fk).first()

            return {"produced_texts": [{"produced_text_pk": produced_text.produced_text_pk,
                        "user_task_execution_fk": produced_text.user_task_execution_fk,
                        "user_id": produced_text.user_id,
                        "production": produced_text_version.production,
                        "title": produced_text_version.title,
                        "creation_date": produced_text_version.creation_date.isoformat(),
                        "text_type": text_type[0] if text_type is not None else None,
                        } for produced_text, produced_text_version in results]}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error getting produced_text : {e}")
            return {"error": f"{e}"}, 404


    # save (new or update)
    def post(self):
        try:
            user_id = None
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                auth = authenticate_function(request.headers['Authorization'])
                if auth[0] is not True:
                    return auth
                user_id = auth[1]
        except KeyError:
            log_error(f"Error updating user summary : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        if not request.is_json:
            log_error(f"Error saving produced_text : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            produced_text_pk = request.json["produced_text_pk"] if "produced_text_pk" in request.json else None
            user_task_execution_pk = request.json[
                "user_task_execution_pk"] if "user_task_execution_pk" in request.json else None
            session_id = request.json["session_id"] if "session_id" in request.json else None
            production = request.json["production"]
            title = request.json["title"] if "title" in request.json else None
            user_id = user_id if user_id else request.json["user_id"]
        except KeyError as e:
            log_error(f"Error saving produced_text : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # logic
        try:
            if produced_text_pk is not None:
                # update
                produced_text = db.session.query(MdProducedText)\
                    .filter(MdProducedText.produced_text_pk == produced_text_pk)\
                    .filter(MdProducedText.user_id==user_id).first()
                if produced_text is None:
                    log_error(f"Error saving produced_text : ProducedText with produced_text_pk {produced_text_pk} does not exist for this user")
                    return {"error": f"Invalid produced_text produced_text_pk for this user: {produced_text_pk}"}, 400

                # text_type = last version text_type
                text_type = db.session.query(MdTextType).join(MdProducedTextVersion, MdProducedTextVersion.text_type_fk == MdTextType.text_type_pk)\
                    .filter(MdProducedTextVersion.produced_text_fk == produced_text_pk)\
                    .order_by(MdProducedTextVersion.creation_date.desc()).first()
            else:
                # new
                produced_text = MdProducedText(
                    user_task_execution_fk=user_task_execution_pk,
                    user_id=user_id,
                    session_id=session_id
                )
                db.session.add(produced_text)
                db.session.flush()
                db.session.refresh(produced_text)
                produced_text_pk = produced_text.produced_text_pk
                text_type=None

            embedding = ProducedTextManager.embed_produced_text(title, production, user_id, user_task_execution_pk=produced_text.user_task_execution_fk,
                                                                task_name_for_system=None)
            # save version
            produced_text_version = MdProducedTextVersion(
                produced_text_fk=produced_text_pk,
                production=production,
                title=title,
                creation_date=datetime.now(),
                text_type_fk = text_type.text_type_pk if text_type is not None else None,
                embedding=embedding
            )
            db.session.add(produced_text_version)
            db.session.commit()
            return {"produced_text_pk": produced_text.produced_text_pk, "produced_text_version_pk": produced_text_version.produced_text_version_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error saving produced_text : {e}")
            return {"error": f"{e}"}, 404

    # delete
    def delete(self, user_id):

        try:
            timestamp = request.args["datetime"]
            produced_text_pk = int(request.args["produced_text_pk"])
        except KeyError as e:
            log_error(f"Error getting produced_text : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            produced_text = db.session.query(MdProducedText)\
                .filter(MdProducedText.produced_text_pk == produced_text_pk)\
                .filter(MdProducedText.user_id==user_id).first()
            if produced_text is None:
                log_error(f"Error deleting produced_text : ProducedText with produced_text_pk {produced_text_pk} does not exist")
                return {"error": f"Invalid produced_text produced_text_pk: {produced_text_pk}"}, 400
            produced_text.deleted_by_user = datetime.now()
            db.session.commit()
            return {"produced_text_pk": produced_text_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error deleting produced_text : {e}")
            return {"error": f"{e}"}, 404

