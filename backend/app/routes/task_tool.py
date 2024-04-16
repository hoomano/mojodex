import os

from flask import request
from flask_restful import Resource
from mojodex_core.entities import MdTool, MdTask, MdTaskToolAssociation
from sqlalchemy import func
from app import db

class TaskTool(Resource):

    # Route to create a new task tool association
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
            task_pk = request.json["task_pk"]
            tool_pk = request.json["tool_pk"]
            usage_description = request.json["usage_description"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if association already exists for tool_pk and task_pk
            task_tool_association = db.session.query(MdTaskToolAssociation)\
                .filter(MdTaskToolAssociation.task_fk == task_pk)\
                .filter(MdTaskToolAssociation.tool_fk == tool_pk)\
                .first()
            if task_tool_association is not None:
                return {"error": f"Task tool association already exists for task_pk:{task_pk} and tool_pk:{tool_pk} "}, 400
            
            # Create task tool association
            task_tool_association = MdTaskToolAssociation(
                task_fk=task_pk,
                tool_fk=tool_pk,
                usage_description=usage_description
            )
            db.session.add(task_tool_association)
            db.session.flush()
            db.session.refresh(task_tool_association)

            db.session.commit()
            return {"task_tool_association_pk": task_tool_association.task_tool_association_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating task tool association: {e}"}, 500


    # Route used only by Backoffice
    # Protected by a secret
    def post(self):
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
            task_tool_pk = request.json["task_tool_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if task tool association exists
            task_tool_association = db.session.query(MdTaskToolAssociation)\
                .filter(MdTaskToolAssociation.task_tool_association_pk == task_tool_pk)\
                .first()
            if task_tool_association is None:
                return {"error": f"Task tool association pk {task_tool_pk} does not exist"}, 400

            if 'usage_description' in request.json:
                task_tool_association.usage_description = request.json["usage_description"]


            db.session.commit()
            return {"task_tool_association_pk": task_tool_association.task_tool_association_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while updating task tool association: {e}"}, 500

    # Route to get all task tool associations for a task or a tool
    def get(self):

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            return {"error": f"Missing Authorization secret in headers"}, 403

        try:
            datetime = request.args["datetime"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            if 'task_pk' in request.args:
                task_pk = request.args["task_pk"]
                task_tool_associations = db.session.query(MdTaskToolAssociation)\
                    .filter(MdTaskToolAssociation.task_fk == task_pk)\
                    .all()
                return {"task_tool_associations": [task_tool_association.to_dict() for task_tool_association in task_tool_associations]}, 200
            elif 'tool_pk' in request.args:
                tool_pk = request.args["tool_pk"]
                task_tool_associations = db.session.query(MdTaskToolAssociation)\
                    .filter(MdTaskToolAssociation.tool_fk == tool_pk)\
                    .all()
                return {"task_tool_associations": [task_tool_association.to_dict() for task_tool_association in task_tool_associations]}, 200
            else:
                return {"error": f"Missing field task_pk or tool_pk"}, 400

        except Exception as e:
            return {"error": f"Error while getting task tool association: {e}"}, 500



