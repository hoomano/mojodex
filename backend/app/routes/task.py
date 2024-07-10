import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.entities.instruct_task import InstructTask
from mojodex_core.entities.task_predefined_action_association import TaskPredefinedActionAssociation
from mojodex_core.entities.workflow import Workflow
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import *
from sqlalchemy import func
from sqlalchemy.orm.attributes import flag_modified
from mojodex_core.steps_library import steps_class
from mojodex_core.entities.task import Task as TaskEntity

class Task(Resource):

    available_json_inputs_types = "text_area", "image", "drop_down_list", 'multiple_images'

    # Route to create a new task
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
            log_error(f"Error creating new task : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            task_type = request.json["task_type"]
            if task_type not in ["instruct", "workflow"]:
                return {"error": f"task_type must be 'instruct' or 'workflow'"}, 400
            if task_type == "instruct":
                final_instruction = request.json["final_instruction"]
                output_format_instruction_title = request.json["output_format_instruction_title"]
                output_format_instruction_draft = request.json["output_format_instruction_draft"]
                infos_to_extract = request.json["infos_to_extract"]
            else:
                final_instruction = None
                output_format_instruction_title = None
                output_format_instruction_draft = None
                infos_to_extract = None

            platforms = request.json["platforms"]
            name_for_system = request.json["name_for_system"]
            definition_for_system = request.json["definition_for_system"]
            icon = request.json["icon"]
            task_displayed_data = request.json["task_displayed_data"]
            predefined_actions = request.json["predefined_actions"] if "predefined_actions" in request.json else []
            output_type = request.json["output_type"].strip().lower()
            result_chat_enabled = request.json.get("result_chat_enabled", True)
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:

            ### COMMON FOR BOTH TASK TYPES

            # ensure there is no space and no upper case in name_for system
            if " " in name_for_system:
                return {"error": f"name_for_system must not contain spaces but underscores. Example : 'answer_to_prospect'"}, 400
            if name_for_system != name_for_system.lower():
                return {"error": f"name_for_system must be in lower case and use underscores. Example : 'answer_to_prospect'"}, 400
            # ensure output_type is in md_text_type
            db_output_type = db.session.query(MdTextType.text_type_pk).filter(MdTextType.name == output_type).first()
            if not db_output_type:
                # add text_type to md_text_type
                text_type = MdTextType(name=output_type)
                db.session.add(text_type)
                db.session.flush()
                db.session.refresh(text_type)
                output_type_pk = text_type.text_type_pk
            else:
                output_type_pk = db_output_type[0]

            # ensure that display_data is a list
            if not isinstance(task_displayed_data, list):
                return {"error": f"task_displayed_data must be a list of dict specifying the corresponding language_code"}, 400
            else:
                for translation in task_displayed_data:
                    if "language_code" not in translation:
                        return {"error": f"language_code undefined, specify the corresponding language_code"}, 400
                    language_code = translation["language_code"]

                    if "name_for_user" not in translation:
                        return {"error": f"name_for_user missing for language_code '{language_code}'"}, 400

                    if "definition_for_user" not in translation:
                        return {"error": f"definition_for_user missing for language_code '{language_code}'"}, 400
                    
                    if "json_input" not in translation:
                        return {"error": f"json_input missing for language_code '{language_code}'"}, 400
                    else:
                        json_input = translation["json_input"]
                        # ensure json_input is a list
                        if not isinstance(json_input, list):
                            return {"error": f"json_input for language_code '{language_code}' must be a list of dict"}, 400

                        # ensure each item in json_input contains at least "input_name", "type" "description_for_user", and "description_for_system"
                        for item in json_input:
                            if not isinstance(item, dict):
                                return {"error": f"json_input for language_code '{language_code}' must be a list of dict"}, 400
                            if "input_name" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'input_name'"}, 400
                            if "type" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'type'"}, 400
                            if item["type"] not in self.available_json_inputs_types:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'type' in {self.available_json_inputs_types}"}, 400
                            if "description_for_user" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'description_for_user'"}, 400
                            if "description_for_system" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'description_for_system'"}, 400

            # ensure that predefined_actions is a list
            if not isinstance(predefined_actions, list):
                return {"error": f"predefined_actions must be a list of dict"}, 400
            else:
                for predefined_action in predefined_actions:
                    if not isinstance(predefined_action, dict):
                        return {"error": f"each predefined_action must be a dict"}, 400
                    if "task_pk" not in predefined_action:
                        return {"error": f"each predefined_action must contain 'task_pk'"}, 400
                    if "displayed_data" not in predefined_action:
                        return {"error": f"each predefined_action must contain 'displayed_data'"}, 400
                    else:
                        displayed_data = predefined_action["displayed_data"]
                        # ensure displayed_data is a list
                        if not isinstance(displayed_data, list):
                            return {"error": f"'displayed_data' for task_pk : {predefined_action['task_pk']} must be a list containing data for each language"}, 400

                        for item in displayed_data:
                            # check there is key 'language_code' in each item
                            if "language_code" not in item:
                                return {"error": f"each item in displayed_data must contain 'language_code'"}, 400
                            # check the is key "data" in each item
                            if "data" not in item:
                                return {"error": f"each item in displayed_data must contain 'data'"}, 400
                            # check item["data"] is a dict
                            if not isinstance(item["data"], dict):
                                return {"error": f"each item in displayed_data must contain 'data' as a dict"}, 400
                            # check item["data"] contains "name"
                            if "name" not in item["data"]:
                                return {"error": f"each item in displayed_data must contain at least key 'name'"}, 400
                            
            # ensure platform is a list
            if not isinstance(platforms, list):
                return {"error": f"'platforms' must be a list"}, 400
            # get platform_pk of each platform based on platform name
            platform_pks = []
            for platform_name in platforms:
                md_platform = db.session.query(MdPlatform).filter(MdPlatform.name == platform_name).first()
                if md_platform is None:
                    return {"error": f"Platform '{platform_name}' is an invalid platform"}, 400
                else: 
                    platform_pks.append(md_platform.platform_pk)


            # SPECIFIC TO INSTRUCT TASKS
            if task_type == "instruct":

                # ensure infos_to_extract is a list
                if not isinstance(infos_to_extract, list):
                    return {"error": f"infos_to_extract must be a list of dict"}, 400

                # ensure each item in infos_to_extract contains at least "input_name", "description"
                for item in infos_to_extract:
                    if not isinstance(item, dict):
                        return {"error": f"infos_to_extract must be a list of dict"}, 400
                    if "info_name" not in item:
                        return {"error": f"infos_to_extract must contain 'info_name'"}, 400
                    if "description" not in item:
                        return {"error": f"infos_to_extract must contain 'description'"}, 400


            task = MdTask(
                type=task_type,
                name_for_system=name_for_system,
                definition_for_system=definition_for_system,
                final_instruction=final_instruction,
                output_format_instruction_title=output_format_instruction_title,
                output_format_instruction_draft=output_format_instruction_draft,
                infos_to_extract=infos_to_extract,
                icon=icon,
                output_text_type_fk=output_type_pk,
                result_chat_enabled=result_chat_enabled
                )

            db.session.add(task)
            db.session.flush()
            db.session.refresh(task)

            # add task_displayed_data
            for translation in task_displayed_data:

                # SAVE TRANSLATIONS
                task_displayed_data = MdTaskDisplayedData(
                    task_fk=task.task_pk,
                    language_code=translation["language_code"],
                    name_for_user=translation["name_for_user"],
                    definition_for_user=translation["definition_for_user"],
                    json_input=translation["json_input"]
                )
                db.session.add(task_displayed_data)
                db.session.flush()
                db.session.refresh(task_displayed_data)

            # associate predefined_actions
            for predefined_action in predefined_actions:

                predefined_action_fk = predefined_action["task_pk"]
                displayed_data = predefined_action["displayed_data"]

                # TASK - ACTION ASSOCIATION
                task_predefined_action_association = TaskPredefinedActionAssociation(
                        task_fk=task.task_pk,
                        predefined_action_fk=predefined_action_fk
                    )
                db.session.add(task_predefined_action_association)
                db.session.flush()
                db.session.refresh(task_predefined_action_association)

                # SAVE TRANSLATIONS
                for displayed_data_in_language in displayed_data:
                    language_code = displayed_data_in_language["language_code"]
                    data = displayed_data_in_language["data"]
                    predefined_action_displayed_data = MdPredefinedActionDisplayedData(
                        task_predefined_action_association_fk=task_predefined_action_association.task_predefined_action_association_pk,
                        language_code=language_code,
                        displayed_data=data
                    )
                    db.session.add(predefined_action_displayed_data)
                    db.session.flush()
                    db.session.refresh(predefined_action_displayed_data)

            # add task_platform_association
            for platform_pk in platform_pks:
                task_platform_association = MdTaskPlatformAssociation(
                    task_fk=task.task_pk, 
                    platform_fk=platform_pk
                )
                db.session.add(task_platform_association)

            # SPECIFIC TO WORKFLOW TASKS
            if task_type == "workflow":
                steps = request.json["steps"]
                # ensure steps is a list
                if not isinstance(steps, list):
                    return {"error": "Steps must be a list of string"}, 400

                for step_index in range(len(steps)):
                    step = steps[step_index]
                    # check step is a dict
                    if not isinstance(step, dict):
                        return {"error": "Step must be a dict"}, 400
                    if "name_for_system" not in step:
                        return {"error": "Step must contain 'name_for_system'"}, 400
                    if "definition_for_system" not in step:
                        return {"error": "Step must contain 'definition_for_system'"}, 400
                    step_name_for_system = step["name_for_system"]
                    step_definition_for_system = step["definition_for_system"]
                    # ensure key exists in steps_class
                    if step_name_for_system not in steps_class:
                        return {"error": f"Step {step_name_for_system} not found in steps library"}, 400

                    db_step = MdWorkflowStep(
                        name_for_system=step_name_for_system,
                        definition_for_system=step_definition_for_system,
                        task_fk=task.task_pk,
                        rank=step_index + 1,
                        review_chat_enabled=step.get("review_chat_enabled", False)
                    )
                    db.session.add(db_step)
                    db.session.flush()

                    if "step_displayed_data" not in step:
                        return {"error": f"Step {step_name_for_system} must contain 'step_displayed_data'"}, 400
                    step_displayed_data = step["step_displayed_data"]

                    # check content of step_displayed_data
                    if not isinstance(step_displayed_data, list):
                        return {
                            "error": f"Step_displayed_data for step {step_name_for_system} must be a list of dict"}, 400
                    for translation in step_displayed_data:
                        if not isinstance(translation, dict):
                            return {
                                "error": f"Step_displayed_data for step {step_name_for_system} must be a list of dict"}, 400
                        if "language_code" not in translation:
                            return {
                                "error": f"Step_displayed_data for step {step_name_for_system} must contain 'language_code'"}, 400
                        step_language_code = translation["language_code"]
                        if "name_for_user" not in translation:
                            return {
                                "error": f"Step_displayed_data for step {step_name_for_system} - language {step_language_code} must contain 'name_for_user'"}, 400
                        step_name_for_user = translation["name_for_user"]
                        if "definition_for_user" not in translation:
                            return {
                                "error": f"Step_displayed_data for step {step_name_for_system} - language {step_language_code} must contain 'definition_for_user'"}, 400
                        step_definition_for_user = translation["definition_for_user"]

                        # add step_displayed_data to db
                        db_step_displayed_data = MdWorkflowStepDisplayedData(
                            workflow_step_fk=db_step.workflow_step_pk,
                            language_code=step_language_code,
                            name_for_user=step_name_for_user,
                            definition_for_user=step_definition_for_user
                        )
                        db.session.add(db_step_displayed_data)
                        db.session.flush()


            db.session.commit()
            return {"task_pk": task.task_pk}, 200
        except Exception as e:
            log_error(f"Error creating task : {e}")
            db.session.rollback()
            return {"error": f"Error creating task : {e}"}, 500


    # Route to edit any field of a task
    def post(self):
        if not request.is_json:
            return {"error": "Request must be JSON"}, 400

        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error editing task : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.json["datetime"]
            task_pk = request.json["task_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            task: TaskEntity = db.session.query(TaskEntity).filter(TaskEntity.task_pk == task_pk).first()
            if task is None:
                return {"error": f"Task with pk {task_pk} not found"}, 404

            # Recover all task - platform associations
            if "platforms" in request.json:
                platforms = request.json["platforms"]
                if not isinstance(platforms, list):
                    return {"error": f"'platforms' must be a list"}, 400

                # get pltform_pk of each platform based on platform name
                platform_pks = []
                for platform_name in platforms:
                    md_platform = db.session.query(MdPlatform).filter(MdPlatform.name == platform_name).first()
                    if md_platform is None:
                        return {"error": f"Platform '{platform_name}' is an invalid platform"}, 400
                    else: 
                        platform_pks.append(md_platform.platform_pk)

                # modify task_platform_association
                task_platform_associations = db.session.query(MdTaskPlatformAssociation).filter(MdTaskPlatformAssociation.task_fk == task_pk).all()
                for task_platform_association in task_platform_associations:
                    # remove the platform association from db if it is not in the platforms list passed
                    if task_platform_association.platform_fk not in platform_pks:
                        db.session.delete(task_platform_association)
                        db.session.flush()
                    # else remove from platform_pks the platform that is already in task_platform_associations and it was passed in platforms
                    else:
                        platform_pks.remove(task_platform_association.platform_fk)
                
                # add task_platform_association for the platforms that are not already in task_platform_associations and were passed in platforms
                for platform_pk in platform_pks:
                    task_platform_association = MdTaskPlatformAssociation(
                        task_fk=task.task_pk, 
                        platform_fk=platform_pk
                    )
                    db.session.add(task_platform_association)
                    db.session.flush()

            if "task_displayed_data" in request.json:
                task_displayed_data = request.json["task_displayed_data"]
                if not isinstance(task_displayed_data, list):
                    return {"error": f"task_displayed_data must be a list of dict specifying the corresponding language_code"}, 400
                else:
                    for translation in task_displayed_data:
                        if not isinstance(translation, dict):
                            return {
                                "error": f"displayed_data must be a list of dict specifying the corresponding language_code"}, 400
                        if "language_code" not in translation:
                            return {"error": f"Missing language_code in displayed_data"}, 400
                        language_code = translation["language_code"]
                        # check translation["json_input"]
                        json_input = translation["json_input"]
                        # ensure json_input is a list
                        if not isinstance(json_input, list):
                            return {"error": f"json_input for language_code '{language_code}' must be a list of dict"}, 400

                        # ensure each item in json_input contains at least "input_name", "type" "description_for_user", and "description_for_system"
                        for item in json_input:
                            if not isinstance(item, dict):
                                return {"error": f"json_input for language_code '{language_code}' must be a list of dict"}, 400
                            if "input_name" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'input_name'"}, 400
                            if "type" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'type'"}, 400
                            if item["type"] not in self.available_json_inputs_types:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'type' in {self.available_json_inputs_types}"}, 400
                            if "description_for_user" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'description_for_user'"}, 400
                            if "description_for_system" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'description_for_system'"}, 400

                        try:
                            task_translation = db.session.query(MdTaskDisplayedData).filter(MdTaskDisplayedData.task_fk == task_pk, MdTaskDisplayedData.language_code == language_code).first()

                            if not task_translation:
                                task_translation = MdTaskDisplayedData(
                                    task_fk=task.task_pk,
                                    language_code=language_code,
                                    name_for_user=translation["name_for_user"],
                                    definition_for_user=translation["definition_for_user"],
                                    json_input=translation["json_input"],
                                )

                                db.session.add(task_translation)
                                db.session.flush()

                            else:
                                task_translation.language_code = translation["language_code"]
                                task_translation.name_for_user = translation["name_for_user"]
                                task_translation.definition_for_user = translation["definition_for_user"]
                                
                                task_translation.json_input = translation["json_input"]
                                flag_modified(task_translation, "json_input")

                        except KeyError as e:
                            return {"error": f"Missing field {e} for language_code '{language_code}'"}, 400

            if "predefined_actions" in request.json: 
   
                # Recover predefined_actions associations that are requested to be modified
                predefined_actions = request.json["predefined_actions"]

                # Modify the predefined_actions_associations on db or create new ones if they don't exist
                for predefined_action in predefined_actions:
                    predefined_action_fk = predefined_action["task_pk"]
                    displayed_data_list: list = predefined_action["displayed_data"]

                    # Try to find existing predefined_action_association
                    task_predefined_action_association = next((predefined_action_association for predefined_action_association in task.predefined_actions_association if predefined_action_association.predefined_action_fk == predefined_action_fk), None)

                    # if predefined_action not in task.predefined_actions_associations, create it
                    if task_predefined_action_association is None:
                        task_predefined_action_association = TaskPredefinedActionAssociation(
                            task_fk=task_pk,
                            predefined_action_fk=predefined_action_fk
                        )
                        
                        db.session.add(task_predefined_action_association)
                        db.session.flush()
                        db.session.refresh(task_predefined_action_association)
                   
                    
                    for displayed_data in displayed_data_list:
                        language_code = displayed_data["language_code"]
                        data = displayed_data["data"]
                        # ensure that displayed data has "name" key
                        if "name" not in data: 
                            return {"error": f"The predefined_action with task_pk : '{predefined_action_fk}' and language_code '{language_code}' must contain 'name'"}, 400
                        
                        # Try to find existing displayed_data
                        displayed_data_object = next((display_data for display_data in task_predefined_action_association.display_data if display_data.language_code == language_code), None)
                        if displayed_data_object is None:
                            displayed_data_object = MdPredefinedActionDisplayedData(
                                task_predefined_action_association_fk=task_predefined_action_association.task_predefined_action_association_pk,
                                language_code=language_code,
                                displayed_data=data
                            )
                            db.session.add(displayed_data_object)
                        else:
                            displayed_data_object.displayed_data = data
                        db.session.flush()

            if "name_for_system" in request.json:
                name_for_system = request.json["name_for_system"]
                # ensure there is no space and no upper case in name_for system
                if " " in name_for_system:
                    return {
                        "error": f"name_for_system must not contain spaces but underscores. Example : 'answer_to_prospect'"}, 400
                if name_for_system != name_for_system.lower():
                    return {
                        "error": f"name_for_system must be in lower case and use underscores. Example : 'answer_to_prospect'"}, 400
                task.name_for_system = name_for_system
            if "definition_for_system" in request.json:
                task.definition_for_system = request.json["definition_for_system"]
            if "final_instruction" in request.json:
                task.final_instruction = request.json["final_instruction"]
            if "output_format_instruction_title" in request.json:
                task.output_format_instruction_title = request.json["output_format_instruction_title"]
            if "output_format_instruction_draft" in request.json:
                task.output_format_instruction_draft = request.json["output_format_instruction_draft"]
            if "infos_to_extract" in request.json:
                task.infos_to_extract = request.json["infos_to_extract"]
                flag_modified(task, "infos_to_extract")
            if "icon" in request.json:
                task.icon = request.json["icon"]
            if "output_type" in request.json:
                output_type = request.json["output_type"].strip().lower()
                # ensure output_type is in enum
                output_type_pk = db.session.query(MdTextType.text_type_pk).filter(MdTextType.name == output_type).first()[0]
                if not output_type_pk:
                    return {"error": f"output_type must be in {db.session.query(MdTextType).all()}"}, 400
                task.output_text_type_fk = output_type_pk
                db.session.flush()
            if "result_chat_enabled" in request.json:
                task.result_chat_enabled = request.json["result_chat_enabled"]

            # TODO: add "STEPS" modification

            db.session.commit()
            return {"task_pk": task.task_pk}, 200
        except Exception as e:
            log_error(f"Error editing task : {e}")
            db.session.rollback()
            return {"error": f"Error editing task : {e}"}, 500

  
    # Route to get json of a task
    def get(self):
        try:
            secret = request.headers['Authorization']
            if secret != os.environ["BACKOFFICE_SECRET"]:
                return {"error": "Authentication error : Wrong secret"}, 403
        except KeyError:
            log_error(f"Error getting task jons : Missing Authorization secret in headers")
            return {"error": f"Missing Authorization secret in headers"}, 403

        # data
        try:
            timestamp = request.args["datetime"]
            task_pk = request.args["task_pk"]
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            task: TaskEntity= db.session.query(TaskEntity)\
                .filter(MdTask.task_pk == task_pk)\
                .first()
            if task is None:
                return {"error": f"Task with pk {task_pk} not found"}, 404
            
            task = db.session.query(Workflow if task.type == "workflow" else InstructTask).get(task_pk)
            
            return task.to_json(), 200

        except Exception as e:
            log_error(f"Error getting task json : {e}")
            db.session.rollback()
            return {"error": f"Error getting task json : {e}"}, 500