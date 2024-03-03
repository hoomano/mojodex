import os
from datetime import datetime

from flask import request
from flask_restful import Resource
from app import db, log_error, mojo_mail_client, push_notification_sender
from mojodex_core.entities import *



class Event(Resource):
    # add mojo_message template


    # adding new event
    def put(self):
        if not request.is_json:
            return {"error": "Invalid request"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["MOJODEX_BACKGROUND_SECRET"]:
                log_error(f"Error creating new event : Authentication error : Wrong secret")
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error creating new event : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp=request.json["datetime"]
            user_id=request.json["user_id"]
            message=request.json["message"]
            event_type = request.json["event_type"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:

            if "notification" in event_type:
                data = request.json["data"]
                notification_title, notification_body = request.json['message']['title'], request.json['message']['body']

                success = push_notification_sender.send_notification_to_user(user_id, notification_title, notification_body,
                                                                        data)
                if success:
                    # add notification to db
                    notification_event = MdEvent(creation_date=datetime.now(), event_type=event_type,
                                           user_id=user_id,
                                           message=message)
                    db.session.add(notification_event)
                    db.session.commit()
                    db.session.refresh(notification_event)
                    return {"event_pk": notification_event.event_pk}, 200
                else:
                    log_error(f"Mojo tried to send a notification to user {user_id} but failed either because "
                              "the user has no device or because the notification failed to be sent on every devices.",
                              )
                    return {"error": f"Mojo tried to send a notification to user {user_id} but failed either because the user has no device or because the notification failed to be sent on every devices."}, 500
            elif "email" in event_type:
                subject, body, email = request.json['message']['subject'], request.json['message']['body'], request.json['message']['email']
                mojo_mail_client.send_mail(subject=subject,
                                           recipients=[email],
                                           html=body)
                # add notification to db
                email_event = MdEvent(creation_date=datetime.now(), event_type=event_type,
                                       user_id=user_id,
                                       message=message)
                db.session.add(email_event)
                db.session.commit()
                return {"event_pk": email_event.event_pk}, 200

        except Exception as e:
            log_error(f"Error creating new event : {e}", notify_admin=True)
            return {"error": f"Error creating new event : {e}"}, 500