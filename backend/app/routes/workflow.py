from flask import request
from flask_restful import Resource
from app import db, log_error
from mojodex_core.entities import *
from models.workflows.steps_library import steps_class

class Workflow(Resource):

    def put(self):
        """Create new workflow"""
        try:
            timestamp = request.json['datetime']
            name = request.json['name']
            steps = request.json['steps']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            db_workflow = MdWorkflow(
                name=name
            )
            db.session.add(db_workflow)
            db.session.flush()

            # ensure steps is a list
            if not isinstance(steps, list):
                return {"error": "Steps should be a list of string"}, 400

            for step in steps:
                # check step is a string
                if not isinstance(step, str):
                    return {"error": "Step should be a string"}, 400
                # check if step exists in db
                db_step = db.session.query(MdWorkflowStep)\
                    .filter(MdWorkflowStep.name == step)\
                    .filter(MdWorkflowStep.workflow_fk == db_workflow.workflow_pk)\
                    .first()
                if not db_step:
                    # ensure key exists in steps_class 
                    if not step in steps_class:
                        return {"error": f"Step {step} not found in steps library"}, 400
                    db_step = MdWorkflowStep(
                        name=step,
                        workflow_fk=db_workflow.workflow_pk
                    )
                    db.session.add(db_step)
                    db.session.flush()

            db.session.commit()
            return {"workflow_pk": db_workflow.workflow_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(e)
            return {"error": f"Error while creating workflow: {e}"}, 500


