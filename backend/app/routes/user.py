
import os
import random
from jinja2 import Template
import requests
from models.login_providers.google_login_manager import GoogleLoginManager
from models.login_providers.apple_login_manager import AppleLoginManager
from flask import request
from flask_restful import Resource
from app import db, mojo_mail_client
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
import hashlib
import string
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from bs4 import BeautifulSoup
from models.purchase_manager import PurchaseManager

from mojodex_core.mail import send_admin_email
from packaging import version

def generate_user_id(name):
    random_string = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    clear_string = f"{random_string}_mojodex_{name}_{datetime.now().isoformat()}"
    encoded_string = hashlib.md5(clear_string.encode())
    return encoded_string.hexdigest()


def generate_token(user_id):
    payload = {
        'iat': datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(days=180),
        'sub': user_id + os.environ['TOKEN_SECRET_SPLITTER'] + ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=10)) + datetime.utcnow().isoformat()
    }
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=os.environ["ENCODING_ALGORITHM"])


class User(Resource):
    users_directory = "/data/users"

    general_backend_error_message = "Oops, something weird has happened. We'll help you by email!"
    wrong_email_or_password_error_message = "Wrong email or password."
    error_user_not_registered_with_password="User is not registered with password."
    error_email_already_exists = "Email already exists."
    change_temporary_password_mails_dir = "/mojodex_core/mails_templates/change_temporary_password"

    def __init__(self):
        self.purchase_manager = PurchaseManager()



    def register_user(self, email, app_version, language_code='en', name=None, password=None, google_id=None, microsoft_id=None, apple_id=None):
        # create user
        user_id = generate_user_id(email)

        user = MdUser(user_id=user_id, name=name,
                      email=email,
                      password=generate_password_hash(password) if password else None,
                      google_id=google_id, microsoft_id=microsoft_id, apple_id=apple_id,
                      language_code=language_code,
                      creation_date=datetime.now())

        db.session.add(user)
        db.session.flush()

        try:
            message = f"New user registered : \nuser_id: {user_id} \nemail: {email} \nname: {name} \napp_version: {app_version}"
            send_admin_email(subject="🎉 New user registered",
                             recipients=PurchaseManager.purchases_email_receivers,
                             text=message)
        except Exception as e:
            log_error(f"Error sending mail : {e}")

        return user


    # login route used by nextJS backend when user is authenticated on front side and need authentication on backend side
    def post(self):
        if not request.is_json:
            log_error(f"Error logging user : Request must be JSON", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400
        email=None
        try:
            timestamp = request.json["datetime"]
            email = request.json["email"]
            login_method = request.json["login_method"]
            app_version = version.parse(request.json["version"]) if "version" in request.json else version.parse("0.0.0")
            # ensure there is at least a password or a token
            if "password" not in request.json and "google_token" not in request.json and "microsoft_token" not in request.json and "apple_token" not in request.json and "apple_authorization_code" not in request.json:
                log_error(f"Error logging user {email} : Missing password or google_token or microsoft_token or apple_token or apple_authorization_code", notify_admin=True)
                return {"error": User.general_backend_error_message}, 400

        except KeyError as e:
            log_error(f"Error logging user {email}: Missing field {e}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400
        try:
            password, microsoft_id, google_id, apple_id, name = None, None, None, None, None

            if login_method == "email_password":
                try:
                    password = request.json["password"]
                except KeyError as e:
                    log_error(f"Error logging user {email}: Missing field : password", notify_admin=True)
                    return {"error": User.general_backend_error_message}, 400
            elif login_method == "microsoft":
                try:
                    microsoft_token = request.json["microsoft_token"]
                except KeyError as e:
                    log_error(f"Error logging user {email}: Missing field : microsoft_token", notify_admin=True)
                    return {"error": User.general_backend_error_message}, 400

                uri = f"{os.environ['MICROSOFT_AD_API_URI']}/me"
                headers = {'Authorization': f"Bearer {microsoft_token}"}
                internal_request = requests.get(uri, headers=headers)

                if internal_request.status_code != 200:
                    log_error(f"Error logging user {email}: Wrong microsoft token  : {internal_request.json()}", notify_admin=True)
                    return {"error": User.general_backend_error_message}, 400

                microsoft_id = internal_request.json()["id"]
                name = internal_request.json()["displayName"]

            elif login_method == "google":
                try:
                    google_token = request.json["google_token"]
                    google_id, name, email = GoogleLoginManager().login(token=google_token)
                except KeyError as e:
                    log_error(f"Error logging user {email}: Missing field : google_token", notify_admin=True)
                    return {"error": User.general_backend_error_message}, 400
                except Exception as e:
                    log_error(f"Error logging user {email}: Wrong google_token", notify_admin=True)
                    return {"error": User.general_backend_error_message}, 400
            elif login_method == "apple":
                try:
                    apple_token = request.json["apple_token"] if "apple_token" in request.json else None
                    apple_authorization_code = request.json["apple_authorization_code"] if "apple_authorization_code" in request.json else None
                    apple_id, name, email = AppleLoginManager().login(authorization_code=apple_authorization_code, token=apple_token)
                except Exception as e:
                    log_error(f"Error login user {email} with apple: {e}", notify_admin=True)
                    return {"error": User.general_backend_error_message}, 400
            else:
                log_error(f"Error logging user {email}: Login method {login_method} not supported", notify_admin=True)
                return {"error": User.general_backend_error_message}, 400

            # check email is in db
            user = db.session.query(MdUser).filter(MdUser.email == email).first()
            if user is None:
                if "login_method" in request.json and password is not None:
                    return {"error": User.wrong_email_or_password_error_message}, 400

                user = self.register_user(email, app_version=app_version, name=name, google_id=google_id,
                                          microsoft_id=microsoft_id)

                # create a directory in users_dir
                os.mkdir(os.path.join(self.users_directory, user.user_id))

            else:
                if password is not None:
                    if user.password is None:
                        log_error(f"Error logging user : user {user.user_id} is not registered with password")
                        return {"error": User.error_user_not_registered_with_password}, 400
                    if not check_password_hash(user.password, password):
                        log_error(f"Error logging user {user.user_id} : Wrong password")
                        return {"error": User.wrong_email_or_password_error_message}, 400
                elif microsoft_id is not None:
                    if user.microsoft_id is None:
                        user.microsoft_id = microsoft_id
                    elif user.microsoft_id != microsoft_id:
                        log_error(f"Error logging user {email}: Wrong microsoft_id", notify_admin=True)
                        return {"error": User.general_backend_error_message}, 400
                elif google_id is not None:
                    if user.google_id is None:
                        user.google_id = google_id
                    elif user.google_id != google_id:
                        log_error(f"Error logging user {email}: Wrong google_id", notify_admin=True)
                        return {"error": User.general_backend_error_message}, 400
                elif apple_id is not None:
                    if user.apple_id is None:
                        user.apple_id = apple_id
                    elif user.apple_id != apple_id:
                        log_error(f"Error logging user {email}: Wrong apple_id", notify_admin=True)
                        return {"error": User.general_backend_error_message}, 400
            if name is not None:
                user.name = name
            token = generate_token(user.user_id)

            db.session.commit()
            return {"token": token, "language_code": user.language_code,
                    "name": user.name,
                    "terms_and_conditions_agreed": user.terms_and_conditions_accepted is not None,
                    "company_fk": user.company_fk}, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error logging user {email}: {e}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400

    # Route used to register a new user with email and password
    def put(self):
        if not request.is_json:
            log_error(f"Error logging user : Request must be JSON", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400
        email = None
        try:
            timestamp = request.json["datetime"]
            email = request.json["email"]
            name = request.json["name"]
            password = request.json["password"]
            language_code = request.json["language_code"] if "language_code" in request.json else "en"
            app_version = version.parse(request.json["version"]) if "version" in request.json else version.parse("0.0.0")
            skip_user_validation = request.json["skip_user_validation"] if "skip_user_validation" in request.json else False
        except KeyError as e:
            log_error(f"Error logging user {email}: Missing field {e}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400

        try:
            # check email is not in db
            user = db.session.query(MdUser).filter(MdUser.email == email).first()
            if user is not None:
                return {"error": User.error_email_already_exists}, 400

            user = self.register_user(email, app_version=app_version, password=password, name=name, language_code=language_code)
            if skip_user_validation:
                user.onboarding_presented = datetime.now()
                user.terms_and_conditions_accepted = datetime.now()
               
            # create a directory in users_dir
            os.mkdir(os.path.join(self.users_directory, user.user_id))


            token = generate_token(user.user_id)
            db.session.flush()

            if skip_user_validation:
                try:
                    self.send_email_to_change_password(user)
                except Exception as e:
                    log_error(f"Error sending reset password email to {email}: {e} - request.json: {request.json}", notify_admin=True)
                    return {"error": f"Account creation aborted: could not send reset password email to user: {e}"}, 400


            db.session.commit()
            return {"token": token, "language_code": user.language_code,
                    "name": user.name,
                    "terms_and_conditions_agreed": user.terms_and_conditions_accepted is not None,
                    "company_fk": user.company_fk
                    }, 200

        except Exception as e:
            db.session.rollback()
            log_error(f"Error registering user {email} : {e}", notify_admin=True)
            return {"error": User.general_backend_error_message}, 400

    def send_email_to_change_password(self, user):
        from routes.password import generate_reset_password_token
        # send reset password email to change temporary password
        token = generate_reset_password_token(user.user_id)

        email_file = os.path.join(self.change_temporary_password_mails_dir, user.language_code + ".html")

        # check if email file exists
        if not os.path.isfile(email_file):
            email_file = os.path.join(self.change_temporary_password_mails_dir, "en.html")

        with open(email_file, "r") as f:
            email_content = f.read()

        try:
            soup = BeautifulSoup(email_content, 'html.parser')
            subject = soup.head.title.string
            if not subject:
                raise Exception("No subject found")
        except Exception as e:
            log_error(f"Error parsing temporary password email {email_file} : {e}", notify_admin=True)
            subject = "Welcome to Mojodex"

        
        template = Template(email_content)
        mail = template.render(username=user.name, 
                               reset_password_link=f'{os.environ["MOJODEX_WEBAPP_URI"]}/auth/reset-password?token={token}',
                               mojodex_webapp_url=os.environ["MOJODEX_WEBAPP_URI"])
    
        mojo_mail_client.send_email(subject=subject,
                                    recipients=[user.email],
                                    html_body=mail)
                
                