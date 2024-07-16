import os

from jinja2 import Template
from flask import request
from flask_restful import Resource
from app import db, authenticate, server_socket

from mojodex_core.produced_text_managers.task_produced_text_manager import TaskProducedTextManager
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *

from models.text_edit_action_manager import TextEditActionManager
from sqlalchemy.sql.functions import coalesce
from packaging import version
from datetime import datetime

class TextEditAction(Resource):
    
    base_prompt_files_path = "mojodex_core/prompts/text_edit_actions"
    error_message_text = "Error executing text edit action"

    def __init__(self):
        TextEditAction.method_decorators = [authenticate(methods=["POST"])]

    def put(self):
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating new text_edit_action : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403
        
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400
        
        try:
            timestamp = request.json["datetime"]
            emoji = request.json["emoji"]
            prompt_file_name = request.json["prompt_file_name"]
            text_edit_action_displayed_data = request.json["displayed_data"]
        except Exception as e:
            log_error(f"Error creating new text_edit_action : {e}")
            return {"error": f"Error creating new text_edit_action : {e}"}, 400
        
        try:
            # Check prompt_file_name exists
            text_edit_action_prompt = os.path.join(TextEditAction.base_prompt_files_path, prompt_file_name)
            if not os.path.exists(text_edit_action_prompt):
                return {"error": f"Prompt file not found : {prompt_file_name}"}, 400

            text_edit_action = MdTextEditAction(
                emoji=emoji,
                prompt_file_name=prompt_file_name
            )
            db.session.add(text_edit_action)
            db.session.flush()
            db.session.refresh(text_edit_action)
            text_edit_action_pk = text_edit_action.text_edit_action_pk

            for text_edit_action_displayed_data in text_edit_action_displayed_data:
                text_edit_action_displayed_data = MdTextEditActionDisplayedData(
                    text_edit_action_fk=text_edit_action_pk,
                    language_code=text_edit_action_displayed_data["language_code"],
                    name=text_edit_action_displayed_data["name"],
                    description=text_edit_action_displayed_data["description"]
                )
                db.session.add(text_edit_action_displayed_data)
                db.session.flush()
            
            db.session.commit()
            return {"text_edit_action_pk": text_edit_action_pk}, 200
                
        except Exception as e:
            return {"error": f"Error creating new text_edit_action : {e}"}, 400

    # Executing text edit actions
    def post(self, user_id):
        if not request.is_json:
            log_error(f"{TextEditAction.error_message_text} : Request must be JSON", notify_admin=True)
            return {"error": "Invalid request"}, 400

        try:
            timestamp = request.json["datetime"]
            platform = request.json["platform"]
            produced_text_version_pk = request.json["produced_text_version_pk"]
            text_edit_action_pk = request.json["text_edit_action_pk"]
            message_pk = request.json["message_pk"] if "message_pk" in request.json else None
            app_version = version.parse(request.json["version"]) if "version" in request.json else version.parse("0.0.0")
        except KeyError as e:
            log_error(f"{TextEditAction.error_message_text} : Missing Key: {e}", notify_admin=True)
            return {"error": f"Missing field in body : {e}"}, 400

        try:
            # Get text to edit, and User and Task execution info
            db_values = (
                db.session
                .query(
                    MdProducedTextVersion,
                    MdUserTaskExecution,
                    MdTask,
                    MdUser
                )
                .join(
                    MdProducedText,
                    MdProducedText.produced_text_pk == MdProducedTextVersion.produced_text_fk
                    )
                .join(
                    MdUserTaskExecution,
                    MdUserTaskExecution.user_task_execution_pk == MdProducedText.user_task_execution_fk
                )
                .join(
                    MdUserTask,
                    MdUserTask.user_task_pk == MdUserTaskExecution.user_task_fk
                )
                .join(
                    MdTask,
                    MdTask.task_pk == MdUserTask.task_fk
                )
                .join(
                    MdUser,
                    MdUser.user_id == user_id
                )
                .filter(
                    MdProducedTextVersion.produced_text_version_pk == produced_text_version_pk
                )
            .first())._asdict()

            produced_text_version = db_values["MdProducedTextVersion"]
            user_task_execution = db_values["MdUserTaskExecution"]
            task = db_values["MdTask"]
            user = db_values["MdUser"]

            # Get text edit action base on text_edit_action_pk
            # Subquery for user_language_code
            user_lang_subquery = (
                db.session.query(
                    MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                    MdTextEditActionDisplayedData.name.label("user_lang_name")
                )
                .join(MdUser, MdUser.user_id == user_id)
                .filter(MdTextEditActionDisplayedData.language_code == MdUser.language_code)
                .subquery()
            )

            # Subquery for 'en'
            en_subquery = (
                db.session.query(
                    MdTextEditActionDisplayedData.text_edit_action_fk.label("text_edit_action_fk"),
                    MdTextEditActionDisplayedData.name.label("en_name")
                )
                .filter(MdTextEditActionDisplayedData.language_code == "en")
                .subquery()
            )

            # Main query
            text_edit_actions = (
                db.session.query(
                    MdTextEditAction,
                    coalesce(user_lang_subquery.c.user_lang_name, en_subquery.c.en_name).label("name")
                )
                .outerjoin(user_lang_subquery,
                           MdTextEditAction.text_edit_action_pk == user_lang_subquery.c.text_edit_action_fk)
                .outerjoin(en_subquery, MdTextEditAction.text_edit_action_pk == en_subquery.c.text_edit_action_fk)
                .join(
                    MdTextEditActionTextTypeAssociation,
                    MdTextEditActionTextTypeAssociation.text_edit_action_fk == MdTextEditAction.text_edit_action_pk,
                )
                .filter(MdTextEditAction.text_edit_action_pk == text_edit_action_pk)
            ).first()

            if text_edit_actions is None:
                log_error(f"{TextEditAction.error_message_text} : text_edit_action_pk: {text_edit_action_pk} not found", notify_admin=True)
                return {"error": f"text_edit_action_pk: {text_edit_action_pk} not found"}, 400

            text_edit_action, text_edit_action_name = text_edit_actions

            if message_pk: # it is a retry because previous call had failed
                # Check if the message exists
                message = db.session.query(MdMessage).filter(MdMessage.message_pk == message_pk).first()
                if message is None:
                    log_error(f"{TextEditAction.error_message_text} : message_pk: {message_pk} not found", notify_admin=True)
                    return {"error": f"message_pk: {message_pk} not found"}, 400
            else:
                # Save user message (edit text tag) to db => This is to leave a trace of the user's action on the chat view on frontend
                user_message = {"text" : text_edit_action_name}
                message = MdMessage(
                    session_id=user_task_execution.session_id,
                    sender="user",
                    event_name="user_message",
                    message=user_message,
                    creation_date=datetime.now(),
                    message_date=datetime.now())

                db.session.add(message)
                db.session.flush()
                db.session.refresh(message)
                user_message["message_pk"] = message.message_pk
                message.message = user_message

            

            # Get text edit action full prompt
            text_edit_action_prompt_file_name = text_edit_action.prompt_file_name
            text_edit_action_prompt = os.path.join(TextEditAction.base_prompt_files_path, text_edit_action_prompt_file_name)
            with open(text_edit_action_prompt, "r") as f:
                text_edit_action_prompt = Template(f.read())
                input_prompt = text_edit_action_prompt.render(
                    title=produced_text_version.title,
                    draft=produced_text_version.production,
                    title_start_tag=TaskProducedTextManager.title_tag_manager.start_tag,
                    title_end_tag=TaskProducedTextManager.title_tag_manager.end_tag,
                    draft_start_tag=TaskProducedTextManager.draft_tag_manager.start_tag,
                    draft_end_tag=TaskProducedTextManager.draft_tag_manager.end_tag,
                )

            text_edit_action_manager = TextEditActionManager(
                user_id=user.user_id,
                language=user.language_code,
                task_name_for_system=task.name_for_system,
                session_id=user_task_execution.session_id,
                user_task_execution_pk=user_task_execution.user_task_execution_pk,
                produced_text_fk=produced_text_version.produced_text_fk,
                text_type_fk=produced_text_version.text_type_fk,
                user_message_pk=message.message_pk,
                platform=platform
            )

            # Edit text on a background thread
            server_socket.start_background_task(
                target=text_edit_action_manager.edit_text,
                input_prompt=input_prompt,
                app_version=app_version
            )

            db.session.commit()
            message_pk = message.message_pk
            # Normally, flask_socketio will close db.session automatically after the request is done 
            # (https://flask.palletsprojects.com/en/2.3.x/patterns/sqlalchemy/) "Flask will automatically remove database sessions at the end of the request or when the application shuts down."
            # But if may not the case because of the background task launched in this route, errors like `QueuePool limit of size 5 overflow 10 reached` may happen in the backend logs and cause issues.
            # That's why here we explicitely call `db.session.close()` to close the session manually.
            db.session.close()

            # Return value
            return {"success": f"produced_text_version_pk : {produced_text_version_pk}", "message_pk": message_pk}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"{TextEditAction.error_message_text} : request.json: {request.json}: {e}", notify_admin=True)
            db.session.close()
            return {"error": f"{TextEditAction.error_message_text} : {e}"}, 400