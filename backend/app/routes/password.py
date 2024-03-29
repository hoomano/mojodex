import jwt
from flask_restful import Resource, request
from app import db, mojo_mail_client, log_error
from mojodex_core.entities import *
from jinja2 import Template
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random
import string
import os

from routes.user import User


def generate_reset_password_token(user_id):
    payload = {
        'iat': datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(minutes=10),
        'sub': user_id + os.environ['RESET_PASSWORD_SECRET_KEY'] + ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=10)) + datetime.utcnow().isoformat()
    }
    return jwt.encode(payload, os.environ["RESET_PASSWORD_JWT_SECRET"], algorithm=os.environ["ENCODING_ALGORITHM"])


class Password(Resource):
    reset_password_mail_template_path = "/data/mails/reset_password.html"
    error_expired_reset_link="Link expired"
    error_invalid_reset_link="Invalid link"
    wrong_email_error_message="Email not found"

    # Send link to reset password
    def put(self):
        if not request.is_json:
            log_error("Error sending reset password email: Request must be JSON", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400

        # Inputs
        email=None
        try:
            timestamp = request.json['datetime']
            email = request.json['email']
        except Exception as e:
            log_error(f"Error sending reset password email to {email}: Invalid inputs: {e} - request.json: {request.json}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400

        # Logic
        try:
            user = db.session.query(MdUser).filter(MdUser.email == email).first()
            if user is None:
                return {"error": Password.wrong_email_error_message}, 404

            token = generate_reset_password_token(user.user_id)

            with open(Password.reset_password_mail_template_path, "r") as f:
                template = Template(f.read())
                mail = template.render(username=user.name, reset_password_link=f'{os.environ["MOJODEX_WEBAPP_URI"]}/auth/reset-password?token={token}')
            try:
                mojo_mail_client.send_mail(subject=f"Mojodex reset password",
                                           recipients=[email],
                                           html=mail)
            except Exception as e:
                log_error(f"Error sending reset password email to {email}: {e} - request.json: {request.json}", notify_admin=True)
                return {"error": User.general_backend_error_message}, 409
            return {"message": "Email sent."}, 200
        except Exception as e:
            log_error(f"Error sending reset password email to {email}: {e} - request.json: {request.json}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 409

    # reset password
    def post(self):
        if not request.is_json:
            log_error("Error resetting password: Request must be JSON", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400

        # Authentication
        try:
            token = request.json["Authorization"]
            payload = jwt.decode(token, os.environ["RESET_PASSWORD_JWT_SECRET"],
                                 algorithms=os.environ["ENCODING_ALGORITHM"])
            user_id = payload["sub"].split(os.environ['RESET_PASSWORD_SECRET_KEY'])[0]
        except KeyError:
            log_error(f"Error resetting password: Authorization key required - request.json: {request.json}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 403
        except jwt.ExpiredSignatureError:
            return {"error": Password.error_expired_reset_link}, 403
        except jwt.InvalidTokenError:
            return {"error": Password.error_invalid_reset_link}, 403

        # Inputs
        try:
            timestamp = request.json['datetime']
            new_password = request.json['new_password']
        except Exception as e:
            log_error(f"Error resetting password for user {user_id}: Invalid inputs: {e} - request.json: {request.json}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400

        # Logic
        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if user is None:
                log_error(f"Error resetting password for user {user_id}: User not found. - request.json: {request.json}", notify_admin=True)
                return {"error": User.general_backend_error_message}, 404
            user.password = generate_password_hash(new_password)
            db.session.commit()
            return {"message": "Password updated."}, 200

        except Exception as e:
            log_error(f"Error resetting password for user {user_id}: {e} - request.json: {request.json}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 409

