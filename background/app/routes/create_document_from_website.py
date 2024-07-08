from flask import request
from flask_restful import Resource
from mojodex_core.documents.website_parser import WebsiteParser
from app import executor

class CreateDocumentFromWebsite(Resource):


    def post(self):
        try:
            timestamp = request.json['datetime']
            website_url = request.json["website_url"]
            user_id = request.json["user_id"]
        except Exception:
            return {"error": "invalid inputs"}, 400

        try:
            executor.submit(WebsiteParser().create_document_from_website, user_id, website_url)

            return {"success": "ok"}, 200
        except Exception as e:
            return {"error": f"Error parsing website : {e}"}, 404