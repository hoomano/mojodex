import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, log_error, document_manager
from mojodex_core.entities import *

from app import embedder, embedding_conf

from sqlalchemy import func


class RetrieveProducedText(Resource):
    embedder = embedder(embedding_conf, label="PRODUCED_TEXT_QUERY_EMBEDDER")

    def get(self):
        log_message = "Error retrieving produced_texts"
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"{log_message} : Authentication error")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(
                f"{log_message} : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.args["datetime"]
            query = request.args["query"]
            n_max = request.args["n_max"]
            max_distance = request.args["max_distance"]
            user_id = request.args["user_id"]
            user_task_execution_pk = request.args["user_task_execution_pk"]
            task_name_for_system = request.args["task_name_for_system"]
        except KeyError as e:
            return {"error": f"Missing key {e} in args"}, 400

        try:
            embedded_query = RetrieveProducedText.embedder.embed(query, user_id,
                                                                 user_task_execution_pk=user_task_execution_pk,
                                                                 task_name_for_system=task_name_for_system)

            # Subquery to get last produced text versions
            produced_text_subquery = db.session.query(
                MdProducedText.user_task_execution_fk,
                MdProducedText.produced_text_pk,
                MdProducedTextVersion.title,
                MdProducedTextVersion.production,
                MdProducedTextVersion.produced_text_version_pk,
                MdProducedTextVersion.embedding,
                func.row_number().over(
                    partition_by=MdProducedText.user_task_execution_fk,
                    order_by=MdProducedTextVersion.creation_date.desc()).label(
                    'row_number')) \
                .join(MdProducedTextVersion, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                .filter(MdProducedTextVersion.embedding.isnot(None)) \
                .subquery()

            nearest_neighbors_subquery = db.session.query(produced_text_subquery) \
                .filter(produced_text_subquery.c.row_number == 1) \
                .subquery()

            cosine_distance = nearest_neighbors_subquery.c.embedding.cosine_distance(
                embedded_query)

            nearest_neighbors = db.session.query(nearest_neighbors_subquery, MdTask.name_for_system, MdTask.icon) \
                .add_columns(cosine_distance.label("cosine_distance")) \
                .join(MdUserTaskExecution,
                      MdUserTaskExecution.user_task_execution_pk == nearest_neighbors_subquery.c.user_task_execution_fk) \
                .join(MdUserTask, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk) \
                .join(MdUser, MdUser.user_id == MdUserTask.user_id) \
                .join(MdTask, MdTask.task_pk == MdUserTask.task_fk) \
                .order_by(cosine_distance) \
                .filter(cosine_distance < max_distance) \
                .filter(MdUser.user_id == user_id) \
                .limit(n_max) \
                .all()

            return {"retrieved_produced_texts": [
                {'user_task_execution_pk': produced_text.user_task_execution_fk,
                 'produced_text_title': produced_text.title,
                 'produced_text': produced_text.production,
                 'task_name': produced_text.name_for_system,
                 'task_icon': produced_text.icon,
                 }
                for produced_text in nearest_neighbors]}, 200

        except Exception as e:
            log_error(f"{log_message}: {e}")
            return {"error": f"{log_message}: {e}"}, 500
