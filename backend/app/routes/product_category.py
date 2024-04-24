import os

from flask import request
from flask_restful import Resource
from app import db, authenticate
from mojodex_core.entities import MdProductCategory, MdProduct, MdProductCategoryDisplayedData, MdUser
from sqlalchemy import func

class ProductCategory(Resource):

    def __init__(self):
        ProductCategory.method_decorators = [authenticate(methods=["GET"])]

    
    def create_product_category(self, product_category_label: str, displayed_data: list, emoji: str, implicit_goal: str, visible: bool):
        try:
            # Check if name already exists
            product_category = db.session.query(MdProductCategory).filter(MdProductCategory.label == product_category_label).first()
            if product_category is not None:
                raise Exception(f"Product category label {product_category_label} already exists")

            # ensure that display_data is a list
            if not isinstance(displayed_data, list):
                raise Exception(f"displayed_data must be a list of dict specifying the corresponding language_code")
            else:
                for translation in displayed_data:
                    if not isinstance(translation, dict):
                        raise Exception(f"displayed_data must be a list of dict specifying the corresponding language_code")
                    if "language_code" not in translation:
                        raise Exception(f"Missing language_code in displayed_data")
                    if "name_for_user" not in translation:
                        raise Exception(f"Missing name_for_user in displayed_data")
                    if "description_for_user" not in translation:
                        raise Exception(f"Missing description_for_user in displayed_data")

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
            return product_category.product_category_pk
        except Exception as e:
            db.session.rollback()
            raise Exception(f"create_product_category:: {e}")
            


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
            product_category_pk = self.create_product_category(product_category_label, displayed_data, emoji, implicit_goal, visible)
            return {"product_category_pk": product_category_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while creating product category: {e}"}, 500


    def update_product_category(self, product_category_pk: int, updated_data: dict):
        try:
            # Check if product category exists
            product_category = db.session.query(MdProductCategory).filter(MdProductCategory.product_category_pk == product_category_pk).first()
            if product_category is None:
                raise Exception(f"Product category pk {product_category_pk} does not exist")

            # Update product category
            if 'visible' in updated_data:
                # A purchase can't be turned visible if it doesn't have a free trial associated = product free + n_days_validity not null
                if updated_data["visible"] is True and product_category.visible is False:
                    product = db.session.query(MdProduct) \
                        .filter(MdProduct.product_category_fk == product_category_pk) \
                        .filter(MdProduct.free == True) \
                        .filter(MdProduct.n_days_validity.isnot(None)) \
                        .first()
                    if product is None:
                        raise Exception(f"Product category pk {product_category_pk} should have a limited free product associated to become visible")
                product_category.visible = updated_data["visible"]
            if 'label' in updated_data:
                # ensure label is unique
                product_category_with_same_label = db.session.query(MdProductCategory)\
                    .filter(MdProductCategory.label == updated_data["label"])\
                    .filter(MdProductCategory.product_category_pk != product_category_pk)\
                    .first()
                if product_category_with_same_label is not None:
                    raise Exception(f"Product category label {updated_data['label']} already exists")
                product_category.label = updated_data["label"]

            if 'emoji' in updated_data:
                product_category.emoji = updated_data["emoji"]

            if 'displayed_data' in updated_data:
                displayed_data = updated_data["displayed_data"]
                # ensure that display_data is a list
                if not isinstance(displayed_data, list):
                    raise Exception(f"displayed_data must be a list of dict specifying the corresponding language_code")
                else:
                    for translation in displayed_data:
                        if not isinstance(translation, dict):
                            raise Exception(f"displayed_data must be a list of dict specifying the corresponding language_code")
                        if "language_code" not in translation:
                            raise Exception(f"Missing language_code in displayed_data")
                        language_code = translation["language_code"]
                        # Check if translation already exists
                        product_category_displayed_data = db.session.query(MdProductCategoryDisplayedData)\
                            .filter(MdProductCategoryDisplayedData.product_category_fk == product_category_pk)\
                            .filter(MdProductCategoryDisplayedData.language_code == language_code)\
                            .first()
                        if product_category_displayed_data is None:
                            # ensure there is a name_for_user and a description_for_user and create the product category displayed data
                            if "name_for_user" not in translation:
                                raise Exception(f"Missing name_for_user in displayed_data for language_code {language_code}")
                            if "description_for_user" not in translation:
                                raise Exception(f"Missing description_for_user in displayed_data for language_code {language_code}")
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
        except Exception as e:
            db.session.rollback()
            raise Exception(f"update_product_category:: {e}")

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
            self.update_product_category(product_category_pk, request.json)
            return {"product_category_pk": product_category_pk}, 200
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



