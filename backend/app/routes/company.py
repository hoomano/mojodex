import os
import requests
from flask import request
from flask_restful import Resource
from app import db
from mojodex_core.authentication import authenticate
from mojodex_core.documents.website_parser import WebsiteParser
from mojodex_core.logging_handler import log_error
from mojodex_core.entities.db_base_entities import MdCompany, MdUser
from mojodex_core.json_loader import json_decode_retry
from mojodex_core.logging_handler import on_json_error
from mojodex_core.llm_engine.mpt import MPT
from datetime import datetime

class Company(Resource):
    correct_company_info_mpt_filename = "instructions/correct_company_infos.mpt"
    extract_website_info_mpt_filename = "instructions/extract_company_infos_from_webpage.mpt"

    error_invalid_url = "The url is not valid"
    general_backend_error_message = "Oops, something weird has happened. We'll help you by email!"

    def __init__(self):
        Company.method_decorators = [authenticate()]


    @json_decode_retry(retries=3, required_keys=['name', 'description', 'emoji'], on_json_error=on_json_error)
    def update_user_company_description(self, user_id, company, company_description, correct, feedback):

        correct_company_info_mpt = MPT(Company.correct_company_info_mpt_filename,
                                       company=company, company_description=company_description, correct=correct,
                                       feedback=feedback)

        response = correct_company_info_mpt.run(user_id=user_id, temperature=0, max_tokens=500,
                                                 json_format=True)

        return response
    
    @json_decode_retry(retries=3, required_keys=["name", "description", "emoji"], on_json_error=on_json_error)
    def _extract_company_info_from_website(self, user_id, website_url, webpage_text):
        try:
            website_info_mpt = MPT(
                self.extract_website_info_mpt_filename, url=website_url, text_content=webpage_text)

            response = website_info_mpt.run(user_id=user_id,
                                             temperature=0, max_tokens=1000,
                                             json_format=True)

            return response
        except Exception as e:
            raise Exception(f"__scrap_webpage: {e}")


    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error creating Company : Request must be JSON",
                      notify_admin=True)
            return {"error": Company.general_backend_error_message}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            website_url = request.json["website_url"].lower()
        except KeyError as e:
            log_error(f"Error creating Company for user {user_id}: Missing field {e} - request.json: {request.json}",
                      notify_admin=True)
            return {"error": Company.general_backend_error_message}, 400

        try:
            website_url = website_url[:-1] if website_url[-1] == "/" else website_url
            try:
                website_url = WebsiteParser().check_url_validity(website_url)
            except Exception:
                return {"error": Company.error_invalid_url}, 400
            # 1. maybe website already exists in DB
            company = db.session.query(MdCompany).filter(
                MdCompany.website == website_url).first()
            webpage_text = WebsiteParser().get_webpage_text(website_url)
            company_infos = self._extract_company_info_from_website(user_id, website_url, webpage_text)
            name, description, emoji = company_infos["name"], company_infos["description"], company_infos["emoji"]
            if not company:
                # 2. Else, let's parse website to create company
                company = MdCompany(name=name, emoji=emoji, website=website_url,
                                    creation_date=datetime.now())
                db.session.add(company)
                db.session.flush()
                db.session.refresh(company)

            user = db.session.query(MdUser).filter(
                MdUser.user_id == user_id).first()
            user.company_fk = company.company_pk
            user.company_description = description
            db.session.commit()

            
            # call background backend /parse_website to create document from company's website  
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/create_document_from_website"
            pload = {'datetime': datetime.now().isoformat(), 'website_url': website_url, "user_id": user_id,
                        "company_pk": company.company_pk}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(
                    f"Error while calling background parse_website : {internal_request.json()}")


            return {"company_pk": company.company_pk,
                    "company_emoji": company.emoji,
                    "company_name": company.name,
                    "company_description": user.company_description}, 200

        except Exception as e:
            log_error(f"Error creating Company for user {user_id} - request.json: {request.json}: {e}",
                      notify_admin=True)
            db.session.rollback()
            return {"error": Company.general_backend_error_message}, 500

    def post(self, user_id):
        if not request.is_json:
            log_error(f"Error updating company : Request must be JSON",
                      notify_admin=True)
            return {"error": Company.general_backend_error_message}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            feedback = request.json["feedback"].strip(
            ) if "feedback" in request.json else None
            correct = request.json["correct"] if "correct" in request.json else None
        except KeyError as e:
            log_error(f"Error updating company for user {user_id} : Missing field {e} - request.json: {request.json}",
                      notify_admin=True)
            return {"error": Company.general_backend_error_message}, 400

        try:
            company = db.session.query(MdCompany) \
                .join(MdUser, MdUser.company_fk == MdCompany.company_pk) \
                .filter(MdUser.user_id == user_id) \
                .first()

            user = db.session.query(MdUser).filter(
                MdUser.user_id == user_id).first()

            if feedback and feedback.strip() != "":
                infos = self.update_user_company_description(user_id, company, user.company_description, correct,
                                                             feedback)
                name, description, emoji = infos["name"], infos["description"], infos["emoji"]
                company.emoji = emoji
                company.name = name
                user.company_description = description
                db.session.commit()
            return {"company_pk": company.company_pk,
                    "company_emoji": company.emoji,
                    "company_name": company.name,
                    "company_description": user.company_description}, 200
        except Exception as e:
            log_error(
                f"Error updating company for user {user_id} - request.json: {request.json}: {e}")
            db.session.rollback()
            return {"error": Company.general_backend_error_message}, 500
