import os

from flask import request
from flask_restful import Resource
from app import db, authenticate
from db_models import MdTool, MdTaskToolAssociation, MdTask
from sqlalchemy import func


class Tool(Resource):


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
            tool_name = request.json["name"]
            tool_definition = request.json["definition"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if name already exists
            tool = db.session.query(MdTool).filter(MdTool.name == tool_name).first()
            if tool is not None:
                return {"error": f"Tool name {tool_name} already exists"}, 400

            # Create tool
            tool = MdTool(
                name=tool_name,
                definition=tool_definition,
            )
            db.session.add(tool)
            db.session.flush()
            db.session.refresh(tool)

            db.session.commit()
            return {"tool_pk": tool.tool_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating tool: {e}"}, 500


    def get(self):
        
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.args["datetime"]
            tool_pk = request.args["tool_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            result = db.session.query(MdTool)\
                .filter(MdTool.tool_pk == tool_pk)\
                .first()
            if result is None:
                return {"error": f"Tool with pk {tool_pk} not found"}, 404
            tool = result

            task_tool_association = (
                db.session
                .query(MdTask)
                .join(MdTaskToolAssociation, MdTaskToolAssociation.task_fk == MdTask.task_pk)
                .filter(MdTaskToolAssociation.tool_fk == tool_pk)
                .all()
            )

            tasks = [task.name_for_system for task in task_tool_association]

            tool_json = {
                "tool_pk": tool.tool_pk,
                "name": tool.name,
                "definition": tool.definition,
                "tasks": tasks
                }

            return tool_json, 200

        except Exception as e:
            db.session.rollback()
            return {"error": f"Error getting tool json : {e}"}, 500