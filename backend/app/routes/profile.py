import os

from mojodex_core.authentication import authenticate_with_backoffice_secret
from routes.product import Product
from flask import request
from flask_restful import Resource
from app import db

class Profile(Resource):
    
    # A profile is the same thing as a profile and points to the same resource in DB
    # By definition a profile is free and unlimited
    # Those routes are created only to allow for a /profile endpoint instead of /product and simplified endpoint
    # which makes more sense in the context of someone pre-affecting user's account for a company 
    # (in comparison to users being autonomous in their product choices at onboarding)


    def __init__(self):
        Profile.method_decorators = [authenticate_with_backoffice_secret(methods=["PUT", "POST"])]
        self.product_resource = Product()
    
    def put(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            profile_label = request.json["profile_label"]
            displayed_data = request.json["displayed_data"]
            profile_category_pk = request.json["profile_category_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            profile_pk=self.product_resource.create_new_product(profile_label, displayed_data, profile_category_pk, product_stripe_id=None, product_apple_id=None, is_free=True, n_days_validity=None, n_tasks_limit=None)
            return {"profile_pk": profile_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating profile: {e}"}, 500


    def post(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            timestamp = request.json["datetime"]
            profile_pk = request.json["profile_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if product exists
            self.product_resource.update_product(profile_pk, request.json)
            return {"profile_pk": profile_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while updating profile: {e}"}, 500