import os

from routes.product_category import ProductCategory
from flask import request
from flask_restful import Resource
from app import db

class ProfileCategory(Resource):

    # A profileCategory is exactly the same thing as a productCategory and points to the same resource in DB
    # Those routes are created only to allow for a /profile_category endpoint instead of /product_category
    # which makes more sense in the context of someone pre-affecting user's account for a company 
    # (in comparison to users being autonomous in their product choices at onboarding)

    def __init__(self):
        self.product_category_resource = ProductCategory()

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
            product_category_label = request.json["label"]
            displayed_data = request.json["displayed_data"]
            emoji = request.json["emoji"]
            implicit_goal = request.json["implicit_goal"]
            visible = request.json["visible"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            profile_category_pk = self.product_category_resource.create_product_category(product_category_label, displayed_data, emoji, implicit_goal, visible)
            return {"profile_category_pk": profile_category_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating product category: {e}"}, 500


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
            profile_category_pk = request.json["profile_category_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            self.product_category_resource.update_product_category(profile_category_pk, request.json)
            return {"profile_category_pk": profile_category_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while updating profile category: {e}"}, 500
