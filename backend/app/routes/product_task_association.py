import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities.db_base_entities import *


class ProductTaskAssociation(Resource):
    active_status = "active"

    def associate_product_tasks(self, product_pk, task_pk):
        try:
            # Check if product_pk exists
            product = db.session.query(MdProduct).filter(MdProduct.product_pk == product_pk).first()
            if product is None:
                raise Exception(f"Product pk {product_pk} does not exist")

            # Check if task_pk exists
            task = db.session.query(MdTask).filter(MdTask.task_pk == task_pk).first()
            if task is None:
                raise Exception(f"Task pk {task_pk} does not exist")

            # Check if product_task_association already exists
            product_task_association = db.session.query(MdProductTask)\
                .filter(MdProductTask.product_fk == product_pk, MdProductTask.task_fk == task_pk).first()
            if product_task_association is not None:
                raise Exception(f"Product task association already exists")

            # Create product_task_association
            product_task_association = MdProductTask(product_fk=product_pk, task_fk=task_pk)
            db.session.add(product_task_association)
            db.session.flush()

            # Enable user tasks to all users which active purchase is linked to this product
            # Get all active purchases linked to this product
            purchases = db.session.query(MdPurchase)\
                .filter(MdPurchase.product_fk == product_pk, MdPurchase.active == True).all()

            for purchase in purchases:
                # if task not already in user_task, add it, else, enable it
                user_task = db.session.query(MdUserTask) \
                    .filter(MdUserTask.user_id == purchase.user_id) \
                    .filter(MdUserTask.task_fk == task.task_pk).first()

                if not user_task:
                    user_task = MdUserTask(
                        user_id=purchase.user_id,
                        task_fk=task.task_pk
                    )
                    db.session.add(user_task)
                else:
                    user_task.enabled = True
                db.session.flush()


            db.session.commit()
            return product_task_association.product_task_pk
        except Exception as e:
            db.session.rollback()
            raise Exception(f"associate_product_tasks: {e}")


    # Route to create a new product_task_association
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
            product_pk = request.json["product_pk"]
            task_pk = request.json["task_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            product_task_pk = self.associate_product_tasks(product_pk, task_pk)
            return {"product_task_association_pk": product_task_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating product_task_association: {e}"}, 400
