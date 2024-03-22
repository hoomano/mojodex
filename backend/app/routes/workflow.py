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
            icon = request.json['icon']
            description = request.json['description']
            steps = request.json['steps']
            json_inputs_spec = request.json['json_inputs_spec']
        except KeyError as e:
            return {"error": f"Missing parameter : {e}"}, 400
        
        try:
            # ensure json_inputs_spec is a list and each elements are dict
            if not isinstance(json_inputs_spec, list):
                return {"error": "json_inputs_spec should be a list of dict"}, 400
            for item in json_inputs_spec:
                if not isinstance(item, dict):
                    return {"error": "json_inputs_spec should be a list of dict"}, 400
                    

            db_workflow = MdWorkflow(
                name=name,
                icon=icon,
                description=description,
                json_inputs_spec=json_inputs_spec
            )
            db.session.add(db_workflow)
            db.session.flush()

            # ensure steps is a list
            if not isinstance(steps, list):
                return {"error": "Steps should be a list of string"}, 400


            for step_index in range(len(steps)):
                step = steps[step_index]
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
                        workflow_fk=db_workflow.workflow_pk,
                        rank=step_index+1
                    )
                    db.session.add(db_step)
                    db.session.flush()

            db.session.commit()
            return {"workflow_pk": db_workflow.workflow_pk}, 200
        except Exception as e:
            db.session.rollback()
            log_error(e)
            return {"error": f"Error while creating workflow: {e}"}, 500


