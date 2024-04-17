import os
from datetime import datetime

from bs4 import BeautifulSoup
from flask import request
from flask_restful import Resource
from app import authenticate, db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import MdRole, MdProfile, MdProfileCategory, MdUser, MdEvent
from models.role_manager import RoleManager

from mojodex_core.mail import send_admin_email
from sqlalchemy import or_

from mojodex_core.mail import mojo_mail_client

#####
# THIS FILE IS TEMPORARY
# It will bridge the gap during transition from 0.4.10 to 0.4.11 => "product" to "profile"
#### TO BE REMOVED AFTER 0.4.11 RELEASE => Replaced by FreeProfileAssociation

class FreeProductAssociation(Resource):
    welcome_email_dir = "/data/mails/welcome"

    def __init__(self):
        FreeProductAssociation.method_decorators = [authenticate()]

    def put(self, user_id):
        error_message = "Error associating free profile"
        if not request.is_json:
            log_error(f"{error_message}: Request must be JSON", notify_admin=True)
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            profile_category_pk = request.json["product_category_pk"]
        except KeyError as e:
            log_error(f"{error_message} - request.json: {request.json}: Missing field {e}", notify_admin=True)
            return {"error": f"Missing field {e}"}, 400

        try:
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if user is None:
                log_error(f"{error_message} user_id {user_id} does not exist", notify_admin=True)
                return {"error": f"user_id {user_id} does not exist"}, 400

            # Check user never had any role (even expired)
            user_free_role = db.session.query(MdRole)\
                .filter(MdRole.user_id == user_id)\
                .first()
            if user_free_role is not None:
                log_error(f"{error_message} user_id {user_id} asked for a free plan but already had a role", notify_admin=True)
                return {"error": f"user_id {user_id} already had a role"}, 400

            # Check profile_category exists
            profile_category = db.session.query(MdProfileCategory).filter(MdProfileCategory.profile_category_pk == profile_category_pk).first()
            if profile_category is None:
                log_error(f"{error_message} user_id {user_id} - profile_category_pk {profile_category_pk} does not exist", notify_admin=True)
                return {"error": f"profile_category_pk {profile_category_pk} does not exist"}, 400

            # Associate category to user
            user.profile_category_fk = profile_category_pk
            # Associate category goal to user
            user.goal = profile_category.implicit_goal


            # Find limited free profile associated with profile_category
            profile = db.session.query(MdProfile)\
                .filter(MdProfile.profile_category_fk == profile_category_pk)\
                .filter(MdProfile.free == True) \
                .filter(or_(MdProfile.n_days_validity.isnot(None), MdProfile.n_tasks_limit.isnot(None))) \
                .first()

            if profile is None:
                log_error(f"{error_message} user_id: {user_id} email: {user.email} - profile_category_pk {profile_category_pk} has no limited free profile associated", notify_admin=True)
                return {"error": f"profile_category_pk {profile_category_pk} has no limited free profile associated"}, 400

            # Create role
            role = MdRole(
                user_id=user_id,
                profile_fk=profile.profile_pk,
                creation_date=datetime.now()
            )
            db.session.add(role)
            db.session.flush()

            # Activate role
            role_manager = RoleManager()
            role_manager.activate_role(role)

            db.session.commit()

            try:
                message = f"Free profile {profile.label} associated for user user_id: {user_id} email: {user.email}"
                send_admin_email(subject="Free profile associated",
                                 recipients=RoleManager.roles_email_receivers,
                                 text=message)
            except Exception as e:
                log_error(f"Error sending mail : {e}")

            current_roles = role_manager.check_user_active_purchases(user_id)
            purchasable_profiles = role_manager.get_available_products(user_id)

            try:
                # Now, let's send a welcome email to the user !
                email_language = user.language_code if user.language_code else "en"
                category = profile_category.label
                email_file = os.path.join(self.welcome_email_dir, email_language, category + ".html")

                # check if email file exists
                if not os.path.isfile(email_file):
                    # change language to en
                    email_language = "en"
                    email_file = os.path.join(self.welcome_email_dir, email_language, category + ".html")

                with open(email_file, "r") as f:
                    email_content = f.read()

                try:
                    soup = BeautifulSoup(email_content, 'html.parser')
                    subject = soup.head.title.string
                    if not subject:
                        raise Exception("No subject found")
                except Exception as e:
                    log_error(f"Error parsing welcome email {email_file} : {e}", notify_admin=True)
                    subject = "Welcome to Mojodex"

                if mojo_mail_client:
                    mojo_mail_client.send_mail(subject=subject,
                                               recipients=[user.email],
                                               html=email_content)
                    # add notification to db
                    email_event = MdEvent(creation_date=datetime.now(), event_type='welcome_email',
                                          user_id=user_id,
                                          message={"subject": subject, "body": email_content, "email": user.email})
                    db.session.add(email_event)
                db.session.commit()

            except Exception as e:
                log_error(f"Error sending welcome email : {e}", notify_admin=True)


            return {
                "purchasable_products": purchasable_profiles,
                "current_purchases": current_roles
            }, 200
        except Exception as e:
            db.session.rollback()
            log_error(f"{error_message} - request.json: {request.json}: {e}", notify_admin=True)
            return {"error": f"{error_message} : {e}"}, 400
