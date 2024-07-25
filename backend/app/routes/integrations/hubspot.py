
import pytz
from flask import request
from flask_restful import Resource
from datetime import datetime, time
from app import db
from mojodex_core.authentication import authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdProducedTextVersion, MdProducedText
import requests
import json
import os

class Hubspot(Resource):
   
    def __init__(self):
        Hubspot.method_decorators = [authenticate()]


    def __search_hubspot(self, search_object, properties, filterGroups, n_search):
        try:
            headers = {
                'authorization': f"Bearer {os.environ['HUBSPOT_ACCESS_TOKEN']}",
                'Content-Type': 'application/json'
                }
            url = f"https://api.hubapi.com/crm/v3/objects/{search_object}/search"

            payload={
                        "limit": n_search,
                        "properties": properties + ["id"],
                        "filterGroups": filterGroups
                    }
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))

            return response.json()["results"] if "results" in response.json() else []

        except Exception as e:
            raise Exception(f"__search_hubspot: {e}")
            
                  

    # Search CRM company / contact or deal on the go from provided search string
    def get(self, user_id):
        error_message = "Error in Hubspot get method"
       
        # data
        try:
            timestamp = request.args["datetime"]
            search_type = request.args["search_type"]
            n_results = int(request.args["n_results"]) if "n_results" in request.args else 10
            # ensure search_type is among ["companies", "contacts", "deals"]
            if search_type not in ["companies", "contacts", "deals"]:
                log_error(f"{error_message} : search_type must be among ['companies', 'contacts', 'deals']")
                return {"error": "search_type must be among ['companies', 'contacts', 'deals']"}, 400
            search_string = request.args["search_string"]
        except KeyError as e:
            log_error(f"{error_message} : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400
        
        try:
            
            
            if search_type == "companies":
                properties = [ "name" ]
                filtersGroup = [
                            {
                                "filters":[
                                    {
                                        "propertyName": "name",
                                        "operator": "CONTAINS_TOKEN",
                                        "value": f"{search_string}*"
                                    }
                                ]
                            }
                        ]
                results = self.__search_hubspot(search_type, properties, filtersGroup, n_results)
               
                companies_list = [{"name": f"{result['properties']['name']}",
                                 "id": result['id']} for result in results]
                return {"results": companies_list}, 200

            if search_type == "contacts":

                properties = [ "firstname", "lastname", "email" ]
                filtersGroup = [
                            {
                                "filters":[
                                    {
                                        "propertyName": "firstname",
                                        "operator": "CONTAINS_TOKEN",
                                        "value": f"{search_string}*"
                                    }
                                ]
                            },
                            {
                                "filters":[
                                {
                                    "propertyName": "lastname",
                                    "operator": "CONTAINS_TOKEN",
                                    "value": f"{search_string}*"
                                }
                            ]
                            }

                        ]

                results = self.__search_hubspot(search_type, properties, filtersGroup, n_results)

                contacts_list = [{"name":f"{result['properties']['firstname']} {result['properties']['lastname']} - {result['properties']['email']}",
                                 "id": result['id']} for result in results]

                return {"results": contacts_list}, 200
            
            if search_type == "deals":

                properties = [ "dealname" ]
                filtersGroup = [
                            {
                                "filters":[
                                    {
                                        "propertyName": "dealname",
                                        "operator": "CONTAINS_TOKEN",
                                        "value": f"{search_string}*"
                                    }
                                ]
                            }
                        ]
                
                results = self.__search_hubspot(search_type, properties, filtersGroup, n_results)

                deals_list = [{"name":f"{result['properties']['dealname']}",
                               "id": result['id']} for result in results]
                return {"results": deals_list}, 200
            
        except Exception as e:
            log_error(f"{error_message} : {str(e)}", notify_admin=True)
            return {"error": f"{error_message} : {str(e)}"}, 500

    def __get_association_type_id(self, engagement_type, associated_object_type):
        try:
            url = f"https://api.hubapi.com/crm/v4/associations/{engagement_type}/{associated_object_type}/labels"
    
            headers = {
            'authorization': f"Bearer {os.environ['HUBSPOT_ACCESS_TOKEN']}",
            'Content-Type': 'application/json'
            }

            response = requests.request("GET", url, headers=headers)
            return response.json()["results"][0]["typeId"]
        except Exception as e:
            raise Exception(f"__get_association_type_id: {e}")
    


    def __create_hubspot_engagement(self, engagement_type, associated_object_type, associated_object_id, text):
        try:
            association_type_id = self.__get_association_type_id(engagement_type, associated_object_type)

            url = f"https://api.hubapi.com/crm/v3/objects/{engagement_type}"

            headers = {
            'authorization': f"Bearer {os.environ['HUBSPOT_ACCESS_TOKEN']}",
            'Content-Type': 'application/json'
            }

            today_date = datetime.now().date()

            # Create a datetime object for midnight
            midnight_utc = datetime.combine(today_date, time(0, 0, 0), tzinfo=pytz.utc)


            payload = {
            "associations": [
                {
                "types": [
                    {
                    "associationCategory": "HUBSPOT_DEFINED",
                    "associationTypeId": association_type_id
                    }
                ],
                "to": {
                    "id": associated_object_id
                }
                }
            ],
            "properties": {
                "hs_note_body": text,
                "hs_timestamp": midnight_utc.isoformat()
            }
            }

            payload = json.dumps(payload)


            response = requests.request("POST", url, headers=headers, data=payload)

            if response.status_code != 201:
                raise Exception(f"__create_hubspot_engagement: {response.text}")

        except Exception as e:
            raise Exception(f"__create_hubspot_engagement: {e}")

    # Route to send as an engagement to Hubspot
    def put(self, user_id):
        error_message = "Error in Hubspot put method"
        if not request.is_json:
            log_error(f"{error_message} : Request must be JSON")
            return {"error": "Request must be JSON"}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            produced_text_version_pk = request.json["produced_text_version_pk"]
            associated_object_id = request.json["associated_object_id"]
            associated_object_type = request.json["associated_object_type"]
            # ensure associated_object_type is among ['companies', 'contacts', 'deals']
            if associated_object_type not in ['companies', 'contacts', 'deals']:
                log_error(f"{error_message} : associated_object_type must be among ['companies', 'contacts', 'deals']")
                return {"error": "associated_object_type must be among ['companies', 'contacts', 'deals']"}, 400
            engagement_type = request.json["engagement_type"]
            # ensure engagement_type is among["notes", "emails", "calls", "meetings"]
            if engagement_type not in ["notes", "emails", "calls", "meetings"]:
                log_error(f"{error_message} : engagement_type must be among ['notes', 'emails', 'calls', 'meetings']")
                return {"error": "engagement_type must be among ['notes', 'emails', 'calls', 'meetings']"}, 400
        except KeyError as e:
            log_error(f"{error_message} : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400
        
        try:
            # check produced_text_version_pk exists for user_id
            produced_text_version = db.session.query(MdProducedTextVersion)\
                .join(MdProducedText, MdProducedTextVersion.produced_text_fk == MdProducedText.produced_text_pk)\
                .filter(MdProducedText.user_id == user_id)\
                .filter(MdProducedTextVersion.produced_text_version_pk == produced_text_version_pk)\
                .first()
            if not produced_text_version:
                log_error(f"{error_message} : produced_text_version_pk {produced_text_version_pk} not found for user_id {user_id}")
                return {"error": f"produced_text_version_pk {produced_text_version_pk} not found for user_id {user_id}"}, 400
            
            title, production = produced_text_version.title, produced_text_version.production
            text = f"{title}\n{production}"

            
            self.__create_hubspot_engagement(engagement_type, associated_object_type, associated_object_id, text)
            return {"message": "Engagement sent to Hubspot"}, 200
        except Exception as e:
            log_error(f"{error_message} : {str(e)}")
            return {"error": f"{error_message} : {str(e)}"}, 500




            
