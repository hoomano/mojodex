import os

from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from sqlalchemy import func

from sqlalchemy.orm.attributes import flag_modified

class Task(Resource):

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
            platforms = request.json["platforms"]
            name_for_system = request.json["name_for_system"]
            definition_for_system = request.json["definition_for_system"]
            final_instruction = request.json["final_instruction"]
            output_format_instruction_title = request.json["output_format_instruction_title"]
            output_format_instruction_draft = request.json["output_format_instruction_draft"]
            infos_to_extract = request.json["infos_to_extract"]
            icon = request.json["icon"]
            task_displayed_data = request.json["task_displayed_data"]
            predefined_actions = request.json["predefined_actions"]
            output_type = request.json["output_type"].strip().lower()
        except KeyError as e:
            return {"error": f"Missing field {e}"}, 400

        try:
            # ensure there is no space and no upper case in name_for system
            if " " in name_for_system:
                return {"error": f"name_for_system must not contain spaces but underscores. Example : 'answer_to_prospect'"}, 400
            if name_for_system != name_for_system.lower():
                return {"error": f"name_for_system must be in lower case and use underscores. Example : 'answer_to_prospect'"}, 400
            # ensure output_type is in md_text_type
            output_type_pk = db.session.query(MdTextType.text_type_pk).filter(MdTextType.name == output_type).first()[0]
            if not output_type_pk:
                # add text_type to md_text_type
                text_type = MdTextType(name=output_type)
                db.session.add(text_type)
                db.session.flush()
                db.session.refresh(text_type)
                output_type_pk = text_type.text_type_pk

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
                            if "description_for_user" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'description_for_user'"}, 400
                            if "description_for_system" not in item:
                                return {"error": f"json_input for language_code '{language_code}' must contain 'description_for_system'"}, 400

            # ensure that predefined_actions is a list
            if not isinstance(predefined_actions, list):
                return {"error": f"predefined_actions must be a list of dict"}, 400
            else:
                for item in predefined_actions:
                    if not isinstance(item, dict):
                        return {"error": f"each predefined_action must be a dict"}, 400
                    if "task_pk" not in item:
                        return {"error": f"each predefined_action must contain 'task_pk'"}, 400
                    if "displayed_data" not in item:
                        return {"error": f"each predefined_action must contain 'displayed_data'"}, 400
                    else:
                        displayed_data = item["displayed_data"]
                        # ensure displayed_data is a dict
                        if not isinstance(displayed_data, dict):
                            return {"error": f"'displayed_data' for task_pk : {item['task_pk']} must be a dict where each key is the corresponding language_code"}, 400

                        for language_code in displayed_data:
                            if not isinstance(displayed_data[language_code], dict):
                                return {"error": f"The language_code key : '{language_code}' for the predefined_action with task_pk '{item['task_pk']}' must have a dict as value"}, 400
                            if "name" not in displayed_data[language_code]:
                                return {"error": f"The predefined_action with task_pk : '{item['task_pk']}' and language_code '{language_code}' must contain 'name'"}, 400

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

            # ensure platform is a list
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

            task = MdTask(
                name_for_system=name_for_system,
                definition_for_system=definition_for_system,
                final_instruction=final_instruction,
                output_format_instruction_title=output_format_instruction_title,
                output_format_instruction_draft=output_format_instruction_draft,
                infos_to_extract=infos_to_extract,
                icon=icon,
                output_text_type_fk=output_type_pk
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
            for item in predefined_actions:

                predefined_action_fk = item["task_pk"]
                displayed_data = item["displayed_data"]

                # TASK - ACTION ASSOCIATION
                task_predefined_action_association = MdTaskPredefinedActionAssociation(
                        task_fk=task.task_pk,
                        predefined_action_fk=predefined_action_fk
                    )
                db.session.add(task_predefined_action_association)
                db.session.flush()
                db.session.refresh(task_predefined_action_association)

                # SAVE TRANSLATIONS
                for language_code in displayed_data:
                    predefined_action_displayed_data = MdPredefinedActionDisplayedData(
                        task_predefined_action_association_fk=task_predefined_action_association.task_predefined_action_association_pk,
                        language_code=language_code,
                        displayed_data=displayed_data[language_code]
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
            task = db.session.query(MdTask).filter(MdTask.task_pk == task_pk).first()
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

                predefined_actions_associations = (
                    db.session
                    .query(
                        MdTaskPredefinedActionAssociation.task_predefined_action_association_pk,
                        MdTaskPredefinedActionAssociation.predefined_action_fk,
                        MdPredefinedActionDisplayedData
                        
                    )
                    .join(
                        MdPredefinedActionDisplayedData,
                        MdPredefinedActionDisplayedData.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                    )
                    .filter(MdTaskPredefinedActionAssociation.task_fk == task_pk)
                    .group_by(
                        MdTaskPredefinedActionAssociation.task_predefined_action_association_pk,
                        MdTaskPredefinedActionAssociation.predefined_action_fk,
                        MdPredefinedActionDisplayedData.predefined_action_displayed_data_pk
                    )
                .all())

                # Create a dict where each key is a predefined_action_fk and each value is a dict with 
                # language_code as key and the MdPRedefinedActionDisplayedData object to modify as value
                action_associations = {}
                for action_data in predefined_actions_associations:
                    if action_data["predefined_action_fk"] not in action_associations:
                        action_associations[action_data["predefined_action_fk"]] = {}
                        action_associations[action_data["predefined_action_fk"]]["task_predefined_action_association_pk"] = action_data["task_predefined_action_association_pk"]
                    action_associations[action_data["predefined_action_fk"]][action_data["MdPredefinedActionDisplayedData"].language_code] = action_data["MdPredefinedActionDisplayedData"]
                predefined_actions_associations  = action_associations
                
                # Modify the predefined_actions_associations on db or create new ones if they don't exist
                for item in predefined_actions:
                    predefined_action_fk = item["task_pk"]
                    displayed_data = item["displayed_data"]
                    language_codes = list(displayed_data.keys())

                    if predefined_action_fk not in predefined_actions_associations:
                        task_predefined_action_association = MdTaskPredefinedActionAssociation(
                            task_fk=task_pk,
                            predefined_action_fk=predefined_action_fk
                        )
                        
                        db.session.add(task_predefined_action_association)
                        db.session.flush()
                        db.session.refresh(task_predefined_action_association)

                        # add the new task_predefined_action_association to the predefined_actions_associations dict
                        predefined_actions_associations[predefined_action_fk] = {}

                        task_predefined_action_association_fk = task_predefined_action_association.task_predefined_action_association_pk
                    else :
                        task_predefined_action_association_fk = predefined_actions_associations[predefined_action_fk]["task_predefined_action_association_pk"]
                        
                    
                    for language_code in language_codes:
                        
                        # ensure that displayed data has "name" key
                        if "name" not in displayed_data[language_code] : 
                            return {"error": f"The predefined_action with task_pk : '{predefined_action_fk}' and language_code '{language_code}' must contain 'name'"}, 400
                        
                        if language_code in predefined_actions_associations[predefined_action_fk]:
                            displayed_data_object = predefined_actions_associations[predefined_action_fk][language_code]
                            displayed_data_object.displayed_data = displayed_data[language_code]
                            
                            db.session.add(displayed_data_object)
                            
                        else:

                            new_displayed_data = MdPredefinedActionDisplayedData(
                                task_predefined_action_association_fk=task_predefined_action_association_fk,
                                language_code=language_code,
                                displayed_data=displayed_data[language_code]
                            )
                            db.session.add(new_displayed_data)

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
            result = db.session.query(MdTask, MdTextType)\
                .filter(MdTask.task_pk == task_pk)\
                .join(MdTextType, MdTextType.text_type_pk == MdTask.output_text_type_fk)\
                .first()
            if result is None:
                return {"error": f"Task with pk {task_pk} not found"}, 404
            task, output_type = result

            task_translations = db.session.query(MdTaskDisplayedData).filter(MdTaskDisplayedData.task_fk == task_pk).all()
            task_displayed_data = [
                {
                    "language_code": translation.language_code,
                    "name_for_user": translation.name_for_user,
                    "definition_for_user": translation.definition_for_user,
                    "json_input": translation.json_input
                } for translation in task_translations]

            predefined_actions = (
                db.session
                .query(
                    func.json_build_object(
                        "task_pk",
                        MdTaskPredefinedActionAssociation.predefined_action_fk,
                        "displayed_data",
                        func.json_object_agg(
                            MdPredefinedActionDisplayedData.language_code,
                            MdPredefinedActionDisplayedData.displayed_data
                        )
                    )
                )
                .join(
                    MdPredefinedActionDisplayedData,
                    MdPredefinedActionDisplayedData.task_predefined_action_association_fk == MdTaskPredefinedActionAssociation.task_predefined_action_association_pk
                )
                .filter(
                    MdTaskPredefinedActionAssociation.task_fk == task_pk
                )
                .group_by(
                    MdTaskPredefinedActionAssociation.predefined_action_fk
                )
                .all())

            predefined_actions = [
                action 
                for predefined_action in predefined_actions 
                for action in predefined_action
            ]

            platforms = (
                db.session
                .query(
                    MdPlatform
                )
                .join(
                    MdTaskPlatformAssociation,
                    MdTaskPlatformAssociation.platform_fk == MdPlatform.platform_pk
                )
                .filter(
                    MdTaskPlatformAssociation.task_fk == task_pk
                )
                .all())

            platforms = [platform.name for platform in platforms]

            task_json = {
                "platforms": platforms,
                "predefined_actions": predefined_actions,
                "task_displayed_data": task_displayed_data,
                "name_for_system": task.name_for_system,
                "definition_for_system": task.definition_for_system,
                "final_instruction": task.final_instruction,
                "output_format_instruction_title": task.output_format_instruction_title,
                "output_format_instruction_draft": task.output_format_instruction_draft,
                "output_type": output_type.name,
                "icon": task.icon,
                "infos_to_extract": task.infos_to_extract,
                }

            return task_json, 200

        except Exception as e:
            log_error(f"Error getting task json : {e}")
            db.session.rollback()
            return {"error": f"Error getting task json : {e}"}, 500