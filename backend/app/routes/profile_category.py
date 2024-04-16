import os

from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.entities import MdProfileCategory, MdProfile, MdProfileCategoryDisplayedData, MdUser
from sqlalchemy import func

class ProfileCategory(Resource):

    def __init__(self):
        ProfileCategory.method_decorators = [authenticate(methods=["GET"])]

    # Route to create a new profile category
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
            profile_category_label = request.json["label"]
            displayed_data = request.json["displayed_data"]
            emoji = request.json["emoji"]
            implicit_goal = request.json["implicit_goal"]
            visible = request.json["visible"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if name already exists
            profile_category = db.session.query(MdProfileCategory).filter(MdProfileCategory.label == profile_category_label).first()
            if profile_category is not None:
                return {"error": f"Profile category label {profile_category_label} already exists"}, 400

            # ensure that display_data is a list
            if not isinstance(displayed_data, list):
                return {
                    "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400
            else:
                for translation in displayed_data:
                    if not isinstance(translation, dict):
                        return {
                            "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400
                    if "language_code" not in translation:
                        return {"error": f"Missing language_code in displayed_data"}, 400
                    if "name_for_user" not in translation:
                        return {"error": f"Missing name_for_user in displayed_data"}, 400
                    if "description_for_user" not in translation:
                        return {"error": f"Missing description_for_user in displayed_data"}, 400

            # Create profile category
            profile_category = MdProfileCategory(label=profile_category_label,
                                                emoji=emoji,
                                                implicit_goal=implicit_goal, visible=visible)
            db.session.add(profile_category)
            db.session.flush()
            db.session.refresh(profile_category)

            for translation in displayed_data:
                language_code = translation["language_code"]
                name_for_user = translation["name_for_user"]
                description_for_user = translation["description_for_user"]
                # Create the profile category displayed data
                profile_category_displayed_data = MdProfileCategoryDisplayedData(
                    profile_category_fk=profile_category.profile_category_pk,
                    language_code=language_code,
                    name_for_user=name_for_user,
                    description_for_user=description_for_user
                )
                db.session.add(profile_category_displayed_data)
                db.session.flush()

            db.session.commit()
            return {"product_category_pk": profile_category.profile_category_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating profile category: {e}"}, 500

    # Route to update a profile category
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
            profile_category_pk = request.json["product_category_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if profile category exists
            profile_category = db.session.query(MdProfileCategory).filter(MdProfileCategory.profile_category_pk == profile_category_pk).first()
            if profile_category is None:
                return {"error": f"Profile category pk {profile_category_pk} does not exist"}, 400

            # Update profile category
            if 'visible' in request.json:
                # A role can't be turned visible if it doesn't have a free trial associated = profile free + n_days_validity not null
                if request.json["visible"] is True and profile_category.visible is False:
                    profile = db.session.query(MdProfile) \
                        .filter(MdProfile.profile_category_fk == profile_category_pk) \
                        .filter(MdProfile.free == True) \
                        .filter(MdProfile.n_days_validity.isnot(None)) \
                        .first()
                    if profile is None:
                        return {"error": f"Profile category pk {profile_category_pk} should have a limited free profile associated to become visible"}, 400
                profile_category.visible = request.json["visible"]
            if 'label' in request.json:
                # ensure label is unique
                profile_category_with_same_label = db.session.query(MdProfileCategory)\
                    .filter(MdProfileCategory.label == request.json["label"])\
                    .filter(MdProfileCategory.profile_category_pk != profile_category_pk)\
                    .first()
                if profile_category_with_same_label is not None:
                    return {"error": f"Profile category label {request.json['label']} already exists"}, 400
                profile_category.label = request.json["label"]

            if 'emoji' in request.json:
                profile_category.emoji = request.json["emoji"]

            if 'displayed_data' in request.json:
                displayed_data = request.json["displayed_data"]
                # ensure that display_data is a list
                if not isinstance(displayed_data, list):
                    return {
                        "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400
                else:
                    for translation in displayed_data:
                        if not isinstance(translation, dict):
                            return {
                                "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400
                        if "language_code" not in translation:
                            return {"error": f"Missing language_code in displayed_data"}, 400
                        language_code = translation["language_code"]
                        # Check if translation already exists
                        profile_category_displayed_data = db.session.query(MdProfileCategoryDisplayedData)\
                            .filter(MdProfileCategoryDisplayedData.profile_category_fk == profile_category_pk)\
                            .filter(MdProfileCategoryDisplayedData.language_code == language_code)\
                            .first()
                        if profile_category_displayed_data is None:
                            # ensure there is a name_for_user and a description_for_user and create the profile category displayed data
                            if "name_for_user" not in translation:
                                return {"error": f"Missing name_for_user in displayed_data for language_code {language_code}"}, 400
                            if "description_for_user" not in translation:
                                return {"error": f"Missing description_for_user in displayed_data for language_code {language_code}"}, 400
                            name_for_user = translation["name_for_user"]
                            description_for_user = translation["description_for_user"]
                            profile_category_displayed_data = MdProfileCategoryDisplayedData(
                                profile_category_fk=profile_category_pk,
                                language_code=language_code,
                                name_for_user=name_for_user,
                                description_for_user=description_for_user
                            )
                            db.session.add(profile_category_displayed_data)
                            db.session.flush()
                        else:
                            if "name_for_user" in translation:
                                profile_category_displayed_data.name_for_user = translation["name_for_user"]
                            if "description_for_user" in translation:
                                profile_category_displayed_data.description_for_user = translation["description_for_user"]
                            db.session.flush()


            db.session.commit()
            return {"product_category_pk": profile_category.profile_category_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while updating profile category: {e}"}, 500

    # Route to get all visible profile categories
    def get(self, user_id):

        try:
            datetime = request.args["datetime"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()[0]
            profile_categories = (
                db.session.query(
                    MdProfileCategory.profile_category_pk,
                    MdProfileCategory.emoji,
                    func.json_object_agg(
                        MdProfileCategoryDisplayedData.language_code,
                        func.json_build_object(
                            "name_for_user", 
                            MdProfileCategoryDisplayedData.name_for_user,
                            "description_for_user", 
                            MdProfileCategoryDisplayedData.description_for_user
                        )
                    ).label("displayed_data")
                )
                .join(
                    MdProfileCategory,
                    MdProfileCategory.profile_category_pk == MdProfileCategoryDisplayedData.profile_category_fk
                )
                .filter(MdProfileCategory.visible == True)
                .group_by(
                    MdProfileCategory.profile_category_pk,
                    MdProfileCategoryDisplayedData.profile_category_fk
                )
                .all())

            return {"product_categories": [{
                "product_category_pk": profile_category.profile_category_pk,
                "emoji": profile_category.emoji,
                "name": profile_category.displayed_data[user_language_code]["name_for_user"]
                    if user_language_code in profile_category.displayed_data 
                    else profile_category.displayed_data["en"]["name_for_user"],
                "description": profile_category.displayed_data[user_language_code]["description_for_user"]
                    if user_language_code in profile_category.displayed_data
                    else profile_category.displayed_data["en"]["description_for_user"]
            } for profile_category in profile_categories]}, 200

        except Exception as e:
            return {"error": f"Error while getting profile categories: {e}"}, 500



