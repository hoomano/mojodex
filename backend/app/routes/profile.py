import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities import *

class Profile(Resource):
    active_status = "active"

    # Route to create a new profile
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
            profile_label = request.json["profile_label"]
            displayed_data = request.json["displayed_data"]
            profile_category_pk = request.json["profile_category_pk"]
            product_stripe_id = request.json["product_stripe_id"] if "product_stripe_id" in request.json else None
            product_apple_id = request.json["product_apple_id"] if "product_apple_id" in request.json else None
            is_free = request.json["is_free"]
            n_days_validity = request.json["n_days_validity"]
            n_tasks_limit = request.json["n_tasks_limit"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if label already exists
            profile = db.session.query(MdProfile).filter(MdProfile.label == profile_label).first()
            if profile is not None:
                return {"error": f"Profile label {profile_label} already exists"}, 400

            # Check if stripe_id already exists
            if product_stripe_id:
                profile = db.session.query(MdProfile).filter(MdProfile.product_stripe_id == product_stripe_id).first()
                if profile is not None:
                    return {"error": f"Product stripe_id {product_stripe_id} already exists"}, 400


            # ensure it exists in db
            profile_category = db.session.query(MdProfileCategory).filter(MdProfileCategory.profile_category_pk == profile_category_pk).first()
            if profile_category is None:
                return {"error": f"Profile category {profile_category_pk} does not exist"}, 400

            # ensure that display_data is a list
            if not isinstance(displayed_data, list):
                return {
                    "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400

            for translation in displayed_data:
                if not isinstance(translation, dict):
                    return {"error": f"Each translation must be a dict specifying language_code and profile name"}, 400

                if "language_code" not in translation:
                    return {"error": f"Missing language_code in translation"}, 400
                if "name" not in translation:
                    return {"error": f"Missing name in translation"}, 400


            profile = MdProfile(
                label=profile_label,
                product_stripe_id=product_stripe_id,
                product_apple_id=product_apple_id, 
                status=Profile.active_status,
                profile_category_fk=profile_category_pk,
                free=is_free,
                n_days_validity=n_days_validity,
                n_tasks_limit=n_tasks_limit
            )
            db.session.add(profile)
            db.session.flush()
            db.session.refresh(profile)

            # Create profile displayed data
            for translation in displayed_data:
                language_code = translation["language_code"]
                profile_name = translation["name"]
                profile_displayed_data = MdProfileDisplayedData(
                    profile_fk=profile.profile_pk,
                    language_code=language_code,
                    name=profile_name
                )
                db.session.add(profile_displayed_data)

            db.session.commit()
            return {"profile_pk": profile.profile_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating profile: {e}"}, 500


    # Route to edit a profile
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
            profile_pk = request.json["profile_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if profile exists
            profile = db.session.query(MdProfile).filter(MdProfile.profile_pk == profile_pk).first()
            if profile is None:
                return {"error": f"Profile {profile_pk} does not exists"}, 400

            if "label" in request.json:
                profile_label = request.json["label"]
                # Update profile label
                profile.label = profile_label

            if "profile_category_fk" in request.json:
                profile_category_fk = request.json["profile_category_fk"]
                # Check if profile category exists
                profile_category = db.session.query(MdProfileCategory).filter(MdProfileCategory.profile_category_pk == profile_category_fk).first()
                if profile_category is None:
                    return {"error": f"Profile category {profile_category_fk} does not exists"}, 400
                # Update profile category
                profile.profile_category_fk = profile_category_fk

            if "displayed_data" in request.json:
                displayed_data = request.json["displayed_data"]
                # ensure that display_data is a list
                if not isinstance(displayed_data, list):
                    return {
                        "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400
                for translation in displayed_data:
                    if not isinstance(translation, dict):
                        return {
                            "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400
                    if "language_code" not in translation:
                        return {"error": f"Missing language_code in displayed_data"}, 400
                    language_code = translation["language_code"]
                    if "name" not in translation:
                        return {"error": f"Missing name in displayed_data for language_code: {language_code}"}, 400

                    # Check if profile displayed data exists for this language_code
                    profile_displayed_data = db.session.query(MdProfileDisplayedData)\
                        .filter(MdProfileDisplayedData.profile_fk == profile_pk)\
                        .filter(MdProfileDisplayedData.language_code == language_code)\
                        .first()
                    if profile_displayed_data is None:
                        # Create profile displayed data
                        profile_displayed_data = MdProfileDisplayedData(
                            profile_fk=profile_pk,
                            language_code=language_code,
                            name=translation["name"]
                        )
                        db.session.add(profile_displayed_data)
                        db.session.flush()
                    else:
                        # Update profile displayed data
                        profile_displayed_data.name = translation["name"]
                        db.session.flush()

            if "product_stripe_id" in request.json:
                product_stripe_id = request.json["product_stripe_id"]
                # Check if stripe_id already exists
                if product_stripe_id is not None:
                    other_profile = db.session.query(MdProfile)\
                        .filter(MdProfile.product_stripe_id == product_stripe_id)\
                        .filter(MdProfile.profile_pk != profile_pk)\
                        .first()
                    if other_profile is not None:
                        return {"error": f"Product stripe_id {product_stripe_id} already exists"}, 400
                # Update product stripe_id
                profile.product_stripe_id = product_stripe_id

            if "product_apple_id" in request.json:
                product_apple_id = request.json["product_apple_id"]
                # Check if apple_id already exists
                if product_apple_id is not None:
                    other_profile = db.session.query(MdProfile)\
                        .filter(MdProfile.product_apple_id == product_apple_id)\
                        .filter(MdProfile.profile_pk != profile_pk)\
                        .first()
                    if other_profile is not None:
                        return {"error": f"Product apple_id {product_apple_id} already exists"}, 400
                # Update product apple_id
                profile.product_apple_id = product_apple_id

            if "is_free" in request.json:
                is_free = request.json["is_free"]
                # Update profile free
                profile.free = is_free

            if "n_days_validity" in request.json:
                n_days_validity = request.json["n_days_validity"]
                # Update profile n_days_validity
                profile.n_days_validity = n_days_validity

            if "n_tasks_limit" in request.json:
                n_tasks_limit = request.json["n_tasks_limit"]
                # Update profile n_tasks_limit
                profile.n_tasks_limit = n_tasks_limit

            db.session.commit()
            return {"profile_pk": profile_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while updating profile: {e}"}, 500