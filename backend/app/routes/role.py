import os

from routes.manual_purchase import ManualPurchase
from flask import request
from flask_restful import Resource
from app import db


class Role(Resource):


    # This Role Resource is exactly the same thing as the ManualPurchase resource and points to the same resource in DB
    # Those routes are created only to allow for a /role endpoint instead of /manual_purchase
    # which makes more sense in the context of someone pre-affecting user's account for a company 
    # (in comparison to users being autonomous in their product choices at onboarding)

    def __init__(self):
        self.manual_purchase_resource = ManualPurchase()

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
            profile_pk = request.json["profile_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # check if at least one of the two fields is present in request.json
            user_id = request.json.get("user_id")
            user_email = request.json.get("user_email")
           
            role_pk=self.manual_purchase_resource.create_new_purchase(user_id, user_email, profile_pk)

            return {"role_pk": role_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating role: {e}"}, 400
        
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
            role_pk = request.json["role_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            self.manual_purchase_resource.deactivate_role(role_pk)
            return {}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while deactivating role: {e}"}, 500