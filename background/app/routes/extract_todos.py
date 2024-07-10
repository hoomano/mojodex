from operator import and_
from sqlalchemy import desc, func
from models.todos.todos_creator import TodosCreator
from flask import request
from flask_restful import Resource
from app import db, executor
from mojodex_core.entities.db_base_entities import MdProducedText, MdProducedTextVersion, MdUserTaskExecution
from datetime import datetime, timedelta
class ExtractTodos(Resource):

    def post(self):
        try:
            timestamp = request.json['datetime']
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:

            # find all the user_task_execution_pks that are ready for followup suggestion
            now = datetime.now()
            time_20_min_ago = now - timedelta(minutes=20)
            time_10_min_ago = now - timedelta(minutes=10)

            offset = 0
            n_user_task_executions = 50
            user_task_execution_pks = []
            results = []

            while len(results) == 50 or offset == 0:
                # Subquery to find last associated produced text version's date
                last_produced_text_version_subquery = db.session.query(MdProducedText.user_task_execution_fk.label('user_task_execution_fk'),
                                                  MdProducedTextVersion.creation_date.label('creation_date'),
                                                  func.row_number().over(
                                                      partition_by=MdProducedText.user_task_execution_fk,
                                                      order_by=desc(MdProducedTextVersion.creation_date),
                                                  ).label("row_number")) \
                    .join(MdProducedTextVersion, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk) \
                    .subquery()

                results = (
                    db.session.query(MdUserTaskExecution.user_task_execution_pk)
                    .join(last_produced_text_version_subquery, and_(
                        last_produced_text_version_subquery.c.user_task_execution_fk == MdUserTaskExecution.user_task_execution_pk,
                        last_produced_text_version_subquery.c.row_number == 1))
                    .filter(
                        and_(
                            last_produced_text_version_subquery.c.creation_date > time_20_min_ago,
                            last_produced_text_version_subquery.c.creation_date <= time_10_min_ago
                        )
                    )
                    .filter(MdUserTaskExecution.todos_extracted.is_(None))
                    .order_by(MdUserTaskExecution.user_task_execution_pk)
                    .limit(n_user_task_executions)
                    .offset(offset)
                    .all()
                )

                user_task_execution_pks+=[user_task_execution_pk[0] for user_task_execution_pk in results]
                offset += n_user_task_executions

            def extract_todos_by_batches(user_task_execution_pks):
                for user_task_execution_pk in user_task_execution_pks:
                    todos_creator = TodosCreator(user_task_execution_pk)
                    todos_creator.extract_and_save()

            executor.submit(extract_todos_by_batches, user_task_execution_pks)

            return {"user_task_execution_pks": user_task_execution_pks}, 200
        except Exception as e:
            return {"error": f"Error in extract todos route : {e}"}, 404


