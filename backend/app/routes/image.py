import glob
import os
import time

from flask import request
from flask_restful import Resource
from models.session.session import Session as SessionModel
from app import db, authenticate
from mojodex_core.logging_handler import log_error
from mojodex_core.entities import *
from flask import send_file
from packaging import version
from models.user_images_file_manager import UserImagesFileManager

class Image(Resource):
    def __init__(self):
        Image.method_decorators = [authenticate()]
        self.user_image_file_manager = UserImagesFileManager()

    def get(self, user_id):

        try:
            timestamp = request.args["datetime"]
            filename = request.args["filename"]
            session_id = request.args["session_id"]
        except KeyError as e:
            log_error(f"Error getting image : Missing field {e}")
            return {"error": f"Missing field {e}"}, 400

        # Logic
        try:
            images_storage = self.user_image_file_manager.get_images_storage_path(user_id, session_id)
            file_pattern = os.path.join(images_storage, filename)
            matching_files = glob.glob(file_pattern)
            if len(matching_files) == 0:
                log_error(f"Error getting image : No matching file for file {file_pattern}")
                return {"error": f"No matching file for file {file_pattern}"}, 400
            image_file = matching_files[0]
                
            if not os.path.isfile(image_file):
                log_error(f"Error getting image : Image file {image_file} does not exist")
                return {"error": f"Image file {image_file} does not exist"}, 400

            response = send_file(image_file, conditional=True)
            response.headers.add('Accept-Ranges', 'bytes')
            return response
        except Exception as e:
            db.session.rollback()
            log_error(f"Error getting image : {e}")
            return {"error": f"{e}"}, 400
