import os

from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.entities import MdProfileCategory, MdProfile, MdProfileCategoryDisplayedData, MdUser
from sqlalchemy import func

#####
#THIS FILE IS TEMPORARY
# It will bridge the gap during transition from 0.4.10 to 0.4.11 => "product" to "profile"
#### TO BE REMOVED AFTER 0.4.11 RELEASE => Replaced by ProfileCategory

class ProductCategory(Resource):

    def __init__(self):
        ProductCategory.method_decorators = [authenticate(methods=["GET"])]

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



