import os

from flask import request
from flask_restful import Resource
from app import db, authenticate, authenticate_function,server_socket
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from models.session_creator import SessionCreator
from sqlalchemy import exists


class Session(Resource):

    def __init__(self):
        Session.method_decorators = [authenticate(methods=["GET", "PUT", "DELETE"])]
        self.session_creator = SessionCreator()

    # create a new session
    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error creating session : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            platform = request.json["platform"]
        except KeyError as e:
            log_error(f"Error creating session : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400


        return self.session_creator.create_session(user_id, platform, starting_mode="chat")

    # get list of sessions
    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
        except KeyError as e:
            log_error(f"Error getting sessions : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            n_sessions = min(50, int(request.args["n_sessions"])) if "n_sessions" in request.args else 50
            offset = int(request.args["offset"]) if "offset" in request.args else 0
            # only sessions with at least 1 message
            subquery = exists().where(MdMessage.session_id == MdSession.session_id)
            sessions = db.session.query(MdSession) \
                .filter(subquery) \
                .filter(MdSession.user_id == user_id) \
                .filter(MdSession.starting_mode == "chat") \
                .filter(MdSession.deleted_by_user == False) \
                .order_by(MdSession.creation_date.desc()) \
                .limit(n_sessions) \
                .offset(offset) \
                .all()

            return {"sessions": [{"title": session.title,
                                  "session_id": session.session_id} for session in sessions]}, 200

        except Exception as e:
            return {"error": f"Error getting sessions : {e}"}, 400

    # edit session (add title)
    def post(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            user_id=None
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                auth = authenticate_function(request.headers['Authorization'])
                if auth[0] is not True:
                    return auth
                user_id = auth[1]
        except KeyError:
            log_error(f"Error updating user summary : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            title = request.json["title"]
            session_id = request.json["session_id"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            # check session exists and has no title yet
            session = db.session.query(MdSession) \
                .filter(MdSession.session_id == session_id) \
                .filter(MdSession.deleted_by_user == False)

            # If request does not come from background process, check that user is owner of session
            if request.headers['Authorization'] != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                session= session.filter(MdSession.user_id == user_id)


            session=session.first()

            if session is None:
                return {"error": f"Invalid session_id: {session_id}"}, 400

            # If request comes from background process, check that session has no title yet
            if request.headers['Authorization'] == os.environ["MOJODEX_BACKGROUND_SECRET"]:
                if session.title is not None:
                    return {"error": f"Session already has a title"}, 400

            # update session title
            session.title = title
            db.session.commit()

            if request.headers['Authorization'] == os.environ["MOJODEX_BACKGROUND_SECRET"]:
                server_socket.emit('session_title', {"title": title, "session_id": session_id},  to=session_id)

            return {"session_id": session_id}, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"Error updating session title : {e}")
            return {"error": f"Error updating session title : {e}"}, 400


    def delete(self, user_id):
        try:
            timestamp = request.args["datetime"]
            session_id = request.args["session_id"]
        except KeyError as e:
            log_error(f"Error deleting session : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        try:
            # check session for this user exists
            session = db.session.query(MdSession) \
            .join(MdUser, MdUser.user_id == MdSession.user_id) \
            .filter(MdSession.session_id == session_id) \
            .filter(MdSession.deleted_by_user == False) \
            .filter(MdUser.user_id == user_id) \
            .first()
            if session is None:
                return {"error": "Session not found for this user"}, 404

            # delete session
            session.deleted_by_user = True
            db.session.commit()

            return {"session_id": session_id}, 200

        except Exception as e:
            log_error(f"Error deleting session : {e}")
            db.session.rollback()
            return {"error": f"Error deleting session : {e}"}, 500