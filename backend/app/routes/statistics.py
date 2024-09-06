from flask import request
from flask_restful import Resource
from datetime import datetime, timedelta
from app import db
from mojodex_core.entities.db_base_entities import MdUser, MdUserTask, MdUserTaskExecution, MdProducedText

from mojodex_core.authentication import authenticate_with_backoffice_secret

from sqlalchemy import func

class Statistics(Resource):


    def __init__(self):
        Statistics.method_decorators = [authenticate_with_backoffice_secret(methods=["GET"])]

    def get(self):
        try:
            # Get the current date
            today = datetime.now().date()

            # Query to get the number of new users during the day
            new_users_count = db.session.query(MdUser).filter(MdUser.creation_date >= today).count()
            # Query to get the breakdown of user_task_execution with at least one produced_text per user_email
            user_task_executions = db.session.query(
                MdUser.email,
                func.count(MdUserTaskExecution.user_task_execution_pk).label('task_execution_count')
            ).join(MdUserTask, MdUser.user_id == MdUserTask.user_id
            ).join(MdUserTaskExecution, MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk
            ).join(MdProducedText, MdUserTaskExecution.user_task_execution_pk == MdProducedText.user_task_execution_fk 
            ).filter(MdUserTaskExecution.start_date >= today
            ).group_by(MdUser.email).all()

            # Format the result
            user_task_executions_breakdown = [
                {"email": email, "task_execution_count": task_execution_count}
                for email, task_execution_count in user_task_executions
            ]

            return {
                "new_users_count": new_users_count,
                "user_task_executions_breakdown": user_task_executions_breakdown
            }, 200

        except Exception as e:
        
            return {"error": f"{e}"}, 500