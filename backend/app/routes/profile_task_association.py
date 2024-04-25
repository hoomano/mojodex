import os

from routes.product_task_association import ProductTaskAssociation
from flask import request
from flask_restful import Resource
from app import db


class ProfileTaskAssociation(Resource):
    # A ProfileTaskAssociation is exactly the same thing as a ProductTaskAssociation and points to the same resource in DB
    # Those routes are created only to allow for a /profile_task_association endpoint instead of /product_task_association
    # which makes more sense in the context of someone pre-affecting user's account for a company 
    # (in comparison to users being autonomous in their product choices at onboarding)

    def __init__(self):
        self.product_task_association_resource = ProductTaskAssociation()

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
            profile_pk = request.json["profile_pk"]
            task_pk = request.json["task_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            profile_task_pk = self.product_task_association_resource.associate_product_tasks(profile_pk, task_pk)
            return {"profile_task_association_pk": profile_task_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating profile_task_association: {e}"}, 400
        