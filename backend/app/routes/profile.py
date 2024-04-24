import os

from routes.product import Product
from flask import request
from flask_restful import Resource
from app import db

class Profile(Resource):
    
    # A profile is exactly the same thing as a profile and points to the same resource in DB
    # Those routes are created only to allow for a /profile endpoint instead of /product
    # which makes more sense in the context of someone pre-affecting user's account for a company 
    # (in comparison to users being autonomous in their product choices at onboarding)


    def __init__(self):
        self.product_resource = Product()
    
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
            product_label = request.json["product_label"]
            displayed_data = request.json["displayed_data"]
            product_category_pk = request.json["product_category_pk"]
            product_stripe_id = request.json["product_stripe_id"] if "product_stripe_id" in request.json else None
            product_apple_id = request.json["product_apple_id"] if "product_apple_id" in request.json else None
            is_free = request.json["is_free"]
            n_days_validity = request.json["n_days_validity"]
            n_tasks_limit = request.json["n_tasks_limit"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            product_pk=self.product_resource.create_new_product(product_label, displayed_data, product_category_pk, product_stripe_id, product_apple_id, is_free, n_days_validity, n_tasks_limit)
            return {"product_pk": product_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating profile: {e}"}, 500


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