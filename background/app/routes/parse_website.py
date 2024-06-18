from flask import request
from flask_restful import Resource
from mojodex_core.entities.db_base_entities import *
from app import db
from models.documents.website_parser import WebsiteParser

from app import executor


class ParseWebsite(Resource):

    def __init__(self):
        self.website_parser = WebsiteParser()

    def post(self):
        try:
            timestamp = request.json['datetime']
            company_pk = request.json['company_pk']
            website_url = request.json["website_url"]
            user_id = request.json["user_id"]
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            company = db.session.query(MdCompany).filter(MdCompany.company_pk == company_pk).first()
            if not company:
                return {"error": "company not found"}, 404

            def turn_website_to_document(website_parser, company_name, user_id, website_url):
                try:
                    website_parser.create_website_document( user_id, website_url, company_name)
                except Exception as err:
                    print("🔴" + str(err))

            executor.submit(turn_website_to_document, self.website_parser, company.name, user_id, website_url)

            return {"success": "ok"}, 200
        except Exception as e:
            return {"error": f"Error parsing website : {e}"}, 404