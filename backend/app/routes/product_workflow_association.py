import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities import MdProductWorkflow, MdProduct, MdWorkflow, MdPurchase, MdUserWorkflow


class ProductWorkflowAssociation(Resource):
    active_status = "active"

    # Route to create a new product_workflow_association
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
            workflow_pk = request.json["workflow_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # Check if product_pk exists
            product = db.session.query(MdProduct).filter(MdProduct.product_pk == product_pk).first()
            if product is None:
                return {"error": f"Product pk {product_pk} does not exist"}, 400

            # Check if workflow_pk exists
            workflow = db.session.query(MdWorkflow).filter(MdWorkflow.workflow_pk == workflow_pk).first()
            if workflow is None:
                return {"error": f"Workflow pk {workflow_pk} does not exist"}, 400

            # Check if product_workflow_association already exists
            product_workflow_association = db.session.query(MdProductWorkflow)\
                .filter(MdProductWorkflow.product_fk == product_pk, MdProductWorkflow.workflow_fk == workflow_pk).first()
            if product_workflow_association is not None:
                return {"error": f"Product workflow association already exists"}, 400

            # Create product_workflow_association
            product_workflow_association = MdProductWorkflow(product_fk=product_pk, workflow_fk=workflow_pk)
            db.session.add(product_workflow_association)
            db.session.flush()

            # Enable user workflows to all users which active purchase is linked to this product
            # Get all active purchases linked to this product
            purchases = db.session.query(MdPurchase)\
                .filter(MdPurchase.product_fk == product_pk, MdPurchase.active == True).all()

            for purchase in purchases:
                # if workflow not already in user_workflow, add it, else, enable it
                user_workflow = db.session.query(MdUserWorkflow) \
                    .filter(MdUserWorkflow.user_id == purchase.user_id) \
                    .filter(MdUserWorkflow.workflow_fk == workflow.workflow_pk).first()

                if not user_workflow:
                    user_workflow = MdUserWorkflow(
                        user_id=purchase.user_id,
                        workflow_fk=workflow.workflow_pk
                    )
                    db.session.add(user_workflow)
                else:
                    user_workflow.enabled = True
                db.session.flush()


            db.session.commit()
            return {"product_workflow_association_pk": product_workflow_association.product_workflow_pk}, 200
        except Exception as e:
            return {"error": f"Error while creating product_workflow_association: {e}"}, 500
