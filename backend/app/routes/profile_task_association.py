import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities import *


class ProfileTaskAssociation(Resource):
    active_status = "active"

    # Route to create a new profile_task_association
    # Route used only by Backoffice
    # Protected by a secret
    def put(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            timestamp = request.json["datetime"]
            profile_pk = request.json["product_pk"]
            task_pk = request.json["task_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if profile_pk exists
            profile = db.session.query(MdProfile).filter(MdProfile.profile_pk == profile_pk).first()
            if profile is None:
                return {"error": f"Profile pk {profile_pk} does not exist"}, 400

            # Check if task_pk exists
            task = db.session.query(MdTask).filter(MdTask.task_pk == task_pk).first()
            if task is None:
                return {"error": f"Task pk {task_pk} does not exist"}, 400

            # Check if profile_task_association already exists
            profile_task_association = db.session.query(MdProfileTask)\
                .filter(MdProfileTask.profile_fk == profile_pk, MdProfileTask.task_fk == task_pk).first()
            if profile_task_association is not None:
                return {"error": f"Profile task association already exists"}, 400

            # Create profile_task_association
            profile_task_association = MdProfileTask(profile_fk=profile_pk, task_fk=task_pk)
            db.session.add(profile_task_association)
            db.session.flush()

            # Enable user tasks to all users which active role is linked to this profile
            # Get all active roles linked to this profile
            roles = db.session.query(MdRole)\
                .filter(MdRole.profile_fk == profile_pk, MdRole.active == True).all()

            for role in roles:
                # if task not already in user_task, add it, else, enable it
                user_task = db.session.query(MdUserTask) \
                    .filter(MdUserTask.user_id == role.user_id) \
                    .filter(MdUserTask.task_fk == task.task_pk).first()

                if not user_task:
                    user_task = MdUserTask(
                        user_id=role.user_id,
                        task_fk=task.task_pk
                    )
                    db.session.add(user_task)
                else:
                    user_task.enabled = True
                db.session.flush()


            db.session.commit()
            return {"product_task_association_pk": profile_task_association.profile_task_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating profile_task_association: {e}"}, 500
