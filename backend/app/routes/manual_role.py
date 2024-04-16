import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities import *
from datetime import datetime
from models.role_manager import RoleManager


class ManualRole(Resource):
    active_status = "active"

    # Route to create manually a new role for a user
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
            # user_id or user_email

            product_pk = request.json["product_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # check if at least one of the two fields is present in request.json
            user_id = request.json.get("user_id")
            user_email = request.json.get("user_email")

            if not user_id and not user_email:
                return {"error": "Missing field user_id or user_email"}, 400


            if user_id is None and user_email is not None:
                user = db.session.query(MdUser).filter(MdUser.email == user_email).first()
                user_id = user.user_id
                
            product = db.session.query(MdProfile).filter(MdProfile.product_pk == product_pk).first()
            role_manager = RoleManager()

            role = MdRole(
                user_id=user_id,
                product_fk=product.product_pk,
                creation_date=datetime.now()
            )

            if product.free == False:
                if "custom_purchase_id" not in request.json or request.json["custom_purchase_id"] is None:
                    return {"error": "Missing field custom_purchase_id"}, 400
                role.custom_role_id = request.json["custom_purchase_id"]

            # If user has no category, associate user's goal and product category
            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            if not user.product_category_fk:
                product_category = db.session.query(MdProfileCategory) \
                    .join(MdProfile, MdProfile.product_category_fk == MdProfileCategory.product_category_pk) \
                    .filter(MdProfile.product_pk == product_pk).first()
                user.product_category_fk = product_category.product_category_pk
                user.goal = product_category.implicit_goal
                db.session.flush()

            db.session.add(role)
            db.session.flush()


            role_manager.activate_role(role)

            db.session.commit()

            return {"purchase_pk": role.role_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating role: {e}"}, 500



    # Route to deactivate manually a role for a user
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
            role_pk = request.json["purchase_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            role = db.session.query(MdRole).filter(MdRole.role_pk == role_pk).first()
            role_manager = RoleManager()
            role_manager.deactivate_role(role)
            db.session.commit()
            return {}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while deactivating role: {e}"}, 500

