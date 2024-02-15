import os

from flask import request
from flask_restful import Resource
from app import db
from db_models import *

class Product(Resource):
    active_status = "active"

    # Route to create a new product
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
            # Check if label already exists
            product = db.session.query(MdProduct).filter(MdProduct.label == product_label).first()
            if product is not None:
                return {"error": f"Product label {product_label} already exists"}, 400

            # Check if stripe_id already exists
            if product_stripe_id:
                product = db.session.query(MdProduct).filter(MdProduct.product_stripe_id == product_stripe_id).first()
                if product is not None:
                    return {"error": f"Product stripe_id {product_stripe_id} already exists"}, 400


            # ensure it exists in db
            product_category = db.session.query(MdProductCategory).filter(MdProductCategory.product_category_pk == product_category_pk).first()
            if product_category is None:
                return {"error": f"Product category {product_category_pk} does not exist"}, 400

            # ensure that display_data is a list
            if not isinstance(displayed_data, list):
                return {
                    "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400

            for translation in displayed_data:
                if not isinstance(translation, dict):
                    return {"error": f"Each translation must be a dict specifying language_code and product name"}, 400

                if "language_code" not in translation:
                    return {"error": f"Missing language_code in translation"}, 400
                if "name" not in translation:
                    return {"error": f"Missing name in translation"}, 400


            product = MdProduct(
                label=product_label,
                product_stripe_id=product_stripe_id,
                product_apple_id=product_apple_id, 
                status=Product.active_status,
                product_category_fk=product_category_pk,
                free=is_free,
                n_days_validity=n_days_validity,
                n_tasks_limit=n_tasks_limit
            )
            db.session.add(product)
            db.session.flush()
            db.session.refresh(product)

            # Create product displayed data
            for translation in displayed_data:
                language_code = translation["language_code"]
                product_name = translation["name"]
                product_displayed_data = MdProductDisplayedData(
                    product_fk=product.product_pk,
                    language_code=language_code,
                    name=product_name
                )
                db.session.add(product_displayed_data)

            db.session.commit()
            return {"product_pk": product.product_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating product: {e}"}, 500


    # Route to edit a product
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
            product_pk = request.json["product_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if product exists
            product = db.session.query(MdProduct).filter(MdProduct.product_pk == product_pk).first()
            if product is None:
                return {"error": f"Product {product_pk} does not exists"}, 400

            if "label" in request.json:
                product_label = request.json["label"]
                # Update product label
                product.label = product_label

            if "product_category_fk" in request.json:
                product_category_fk = request.json["product_category_fk"]
                # Check if product category exists
                product_category = db.session.query(MdProductCategory).filter(MdProductCategory.product_category_pk == product_category_fk).first()
                if product_category is None:
                    return {"error": f"Product category {product_category_fk} does not exists"}, 400
                # Update product category
                product.product_category_fk = product_category_fk

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

                    # Check if product displayed data exists for this language_code
                    product_displayed_data = db.session.query(MdProductDisplayedData)\
                        .filter(MdProductDisplayedData.product_fk == product_pk)\
                        .filter(MdProductDisplayedData.language_code == language_code)\
                        .first()
                    if product_displayed_data is None:
                        # Create product displayed data
                        product_displayed_data = MdProductDisplayedData(
                            product_fk=product_pk,
                            language_code=language_code,
                            name=translation["name"]
                        )
                        db.session.add(product_displayed_data)
                        db.session.flush()
                    else:
                        # Update product displayed data
                        product_displayed_data.name = translation["name"]
                        db.session.flush()

            if "product_stripe_id" in request.json:
                product_stripe_id = request.json["product_stripe_id"]
                # Check if stripe_id already exists
                if product_stripe_id is not None:
                    other_product = db.session.query(MdProduct)\
                        .filter(MdProduct.product_stripe_id == product_stripe_id)\
                        .filter(MdProduct.product_pk != product_pk)\
                        .first()
                    if other_product is not None:
                        return {"error": f"Product stripe_id {product_stripe_id} already exists"}, 400
                # Update product stripe_id
                product.product_stripe_id = product_stripe_id

            if "product_apple_id" in request.json:
                product_apple_id = request.json["product_apple_id"]
                # Check if apple_id already exists
                if product_apple_id is not None:
                    other_product = db.session.query(MdProduct)\
                        .filter(MdProduct.product_apple_id == product_apple_id)\
                        .filter(MdProduct.product_pk != product_pk)\
                        .first()
                    if other_product is not None:
                        return {"error": f"Product apple_id {product_apple_id} already exists"}, 400
                # Update product apple_id
                product.product_apple_id = product_apple_id

            if "is_free" in request.json:
                is_free = request.json["is_free"]
                # Update product free
                product.free = is_free

            if "n_days_validity" in request.json:
                n_days_validity = request.json["n_days_validity"]
                # Update product n_days_validity
                product.n_days_validity = n_days_validity

            if "n_tasks_limit" in request.json:
                n_tasks_limit = request.json["n_tasks_limit"]
                # Update product n_tasks_limit
                product.n_tasks_limit = n_tasks_limit

            db.session.commit()
            return {"product_pk": product_pk}, 200
        except Exception as e:
            db.session.rollback()
            return {"error": f"Error while updating product: {e}"}, 500