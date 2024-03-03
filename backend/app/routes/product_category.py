import os

from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.entities import MdProductCategory, MdProduct, MdProductCategoryDisplayedData, MdUser
from sqlalchemy import func

class ProductCategory(Resource):

    def __init__(self):
        ProductCategory.method_decorators = [authenticate(methods=["GET"])]

    # Route to create a new product category
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
            product_category_label = request.json["label"]
            displayed_data = request.json["displayed_data"]
            emoji = request.json["emoji"]
            implicit_goal = request.json["implicit_goal"]
            visible = request.json["visible"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if name already exists
            product_category = db.session.query(MdProductCategory).filter(MdProductCategory.label == product_category_label).first()
            if product_category is not None:
                return {"error": f"Product category label {product_category_label} already exists"}, 400

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

            # Create product category
            product_category = MdProductCategory(label=product_category_label,
                                                emoji=emoji,
                                                implicit_goal=implicit_goal, visible=visible)
            db.session.add(product_category)
            db.session.flush()
            db.session.refresh(product_category)

            for translation in displayed_data:
                language_code = translation["language_code"]
                name_for_user = translation["name_for_user"]
                description_for_user = translation["description_for_user"]
                # Create the product category displayed data
                product_category_displayed_data = MdProductCategoryDisplayedData(
                    product_category_fk=product_category.product_category_pk,
                    language_code=language_code,
                    name_for_user=name_for_user,
                    description_for_user=description_for_user
                )
                db.session.add(product_category_displayed_data)
                db.session.flush()

            db.session.commit()
            return {"product_category_pk": product_category.product_category_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating product category: {e}"}, 500

    # Route to update a product category
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
            product_category_pk = request.json["product_category_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if product category exists
            product_category = db.session.query(MdProductCategory).filter(MdProductCategory.product_category_pk == product_category_pk).first()
            if product_category is None:
                return {"error": f"Product category pk {product_category_pk} does not exist"}, 400

            # Update product category
            if 'visible' in request.json:
                # A purchase can't be turned visible if it doesn't have a free trial associated = product free + n_days_validity not null
                if request.json["visible"] is True and product_category.visible is False:
                    product = db.session.query(MdProduct) \
                        .filter(MdProduct.product_category_fk == product_category_pk) \
                        .filter(MdProduct.free == True) \
                        .filter(MdProduct.n_days_validity.isnot(None)) \
                        .first()
                    if product is None:
                        return {"error": f"Product category pk {product_category_pk} should have a limited free product associated to become visible"}, 400
                product_category.visible = request.json["visible"]
            if 'label' in request.json:
                # ensure label is unique
                product_category_with_same_label = db.session.query(MdProductCategory)\
                    .filter(MdProductCategory.label == request.json["label"])\
                    .filter(MdProductCategory.product_category_pk != product_category_pk)\
                    .first()
                if product_category_with_same_label is not None:
                    return {"error": f"Product category label {request.json['label']} already exists"}, 400
                product_category.label = request.json["label"]

            if 'emoji' in request.json:
                product_category.emoji = request.json["emoji"]

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
                        product_category_displayed_data = db.session.query(MdProductCategoryDisplayedData)\
                            .filter(MdProductCategoryDisplayedData.product_category_fk == product_category_pk)\
                            .filter(MdProductCategoryDisplayedData.language_code == language_code)\
                            .first()
                        if product_category_displayed_data is None:
                            # ensure there is a name_for_user and a description_for_user and create the product category displayed data
                            if "name_for_user" not in translation:
                                return {"error": f"Missing name_for_user in displayed_data for language_code {language_code}"}, 400
                            if "description_for_user" not in translation:
                                return {"error": f"Missing description_for_user in displayed_data for language_code {language_code}"}, 400
                            name_for_user = translation["name_for_user"]
                            description_for_user = translation["description_for_user"]
                            product_category_displayed_data = MdProductCategoryDisplayedData(
                                product_category_fk=product_category_pk,
                                language_code=language_code,
                                name_for_user=name_for_user,
                                description_for_user=description_for_user
                            )
                            db.session.add(product_category_displayed_data)
                            db.session.flush()
                        else:
                            if "name_for_user" in translation:
                                product_category_displayed_data.name_for_user = translation["name_for_user"]
                            if "description_for_user" in translation:
                                product_category_displayed_data.description_for_user = translation["description_for_user"]
                            db.session.flush()


            db.session.commit()
            return {"product_category_pk": product_category.product_category_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while updating product category: {e}"}, 500

    # Route to get all visible product categories
    def get(self, user_id):

        try:
            datetime = request.args["datetime"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            user_language_code = db.session.query(MdUser.language_code).filter(MdUser.user_id == user_id).first()[0]
            product_categories = (
                db.session.query(
                    MdProductCategory.product_category_pk,
                    MdProductCategory.emoji,
                    func.json_object_agg(
                        MdProductCategoryDisplayedData.language_code,
                        func.json_build_object(
                            "name_for_user", 
                            MdProductCategoryDisplayedData.name_for_user,
                            "description_for_user", 
                            MdProductCategoryDisplayedData.description_for_user
                        )
                    ).label("displayed_data")
                )
                .join(
                    MdProductCategory,
                    MdProductCategory.product_category_pk == MdProductCategoryDisplayedData.product_category_fk
                )
                .filter(MdProductCategory.visible == True)
                .group_by(
                    MdProductCategory.product_category_pk,
                    MdProductCategoryDisplayedData.product_category_fk
                )
                .all())

            return {"product_categories": [{
                "product_category_pk": product_category.product_category_pk,
                "emoji": product_category.emoji,
                "name": product_category.displayed_data[user_language_code]["name_for_user"]
                    if user_language_code in product_category.displayed_data 
                    else product_category.displayed_data["en"]["name_for_user"],
                "description": product_category.displayed_data[user_language_code]["description_for_user"]
                    if user_language_code in product_category.displayed_data
                    else product_category.displayed_data["en"]["description_for_user"]
            } for product_category in product_categories]}, 200

        except Exception as e:
            return {"error": f"Error while getting product categories: {e}"}, 500



