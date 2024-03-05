import json
import os
from datetime import datetime

import requests
from flask import request
from flask_restful import Resource
from app import db, authenticate, log_error, executor
from mojodex_core.entities import *
from jinja2 import Template

from models.documents.website_parser import WebsiteParser
from mojodex_core.mojodex_openai import MojodexOpenAI

from azure_openai_conf import AzureOpenAIConf
from mojodex_core.json_loader import json_decode_retry
from app import on_json_error


class Company(Resource):
    correct_company_info_prompt = "/data/prompts/company/correct_company_infos.txt"
    company_info_corrector = MojodexOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf,
                                           "CORRECT_COMPANY_INFO_FROM_FEEDBACK",
                                           AzureOpenAIConf.azure_gpt4_32_conf
                                           )

    error_invalid_url = "The url is not valid"
    general_backend_error_message = "Oops, something weird has happened. We'll help you by email!"

    def __init__(self):
        Company.method_decorators = [authenticate()]
        self.website_parser = WebsiteParser()

    @json_decode_retry(retries=3, required_keys=['name', 'description', 'emoji'], on_json_error=on_json_error)
    def update_user_company_description(self, user_id, company, company_description, correct, feedback):
        with open(Company.correct_company_info_prompt, 'r') as f:
            template = Template(f.read())
        prompt = template.render(company=company, company_description=company_description, correct=correct,
                                 feedback=feedback)
        messages = [{"role": "user", "content": prompt}]

        responses = Company.company_info_corrector.chat(messages, user_id, temperature=0, max_tokens=500,
                                                        json_format=True)[0]

        return responses

    def put(self, user_id):
        if not request.is_json:
            log_error(f"Error creating Company : Request must be JSON", notify_admin=True)
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
                website_url = self.website_parser.check_url_validity(website_url)
            except Exception:
                return {"error": Company.error_invalid_url}, 400
            # 1. maybe website already exists in DB
            company = db.session.query(MdCompany).filter(MdCompany.website == website_url).first()
            name, description, emoji = self.website_parser.get_company_name_and_description(user_id, website_url)
            if not company:
                # 2. Else, let's parse website to create company
                company = MdCompany(name=name, emoji=emoji, website=website_url,
                                    creation_date=datetime.now())
                db.session.add(company)
                db.session.flush()
                db.session.refresh(company)

            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()
            user.company_fk = company.company_pk
            user.company_description = description
            db.session.commit()

            def website_to_document(website_url, user_id, company_pk):
                # call background backend /end_user_task_execution to update website
                uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/parse_website"
                pload = {'datetime': datetime.now().isoformat(), 'website_url': website_url, "user_id": user_id,
                         "company_pk": company_pk}
                internal_request = requests.post(uri, json=pload)
                if internal_request.status_code != 200:
                    log_error(f"Error while calling background parse_website : {internal_request.json()}")

            executor.submit(website_to_document, website_url, user_id, company.company_pk)

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
            log_error(f"Error updating company : Request must be JSON", notify_admin=True)
            return {"error": Company.general_backend_error_message}, 400

        # data
        try:
            timestamp = request.json["datetime"]
            feedback = request.json["feedback"].strip() if "feedback" in request.json else None
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

            user = db.session.query(MdUser).filter(MdUser.user_id == user_id).first()

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
            log_error(f"Error updating company for user {user_id} - request.json: {request.json}: {e}")
            db.session.rollback()
            return {"error": Company.general_backend_error_message}, 500
