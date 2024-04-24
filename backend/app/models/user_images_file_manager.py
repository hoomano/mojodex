import base64
import os
from models.session.session import Session as SessionModel

from mojodex_backend_logger import MojodexBackendLogger



class UserImagesFileManager:
    logger_prefix = "UserImagesFileManager::"

    def __init__(self):
        try:
            self.logger = MojodexBackendLogger(
                f"{UserImagesFileManager.logger_prefix}")
        except Exception as e:
            raise Exception(f"Error in initializing UserImagesFileManager: {e}")


    def __get_images_storage_path(self, user_id, session_id):
        try:
            user_storage = os.path.join(SessionModel.sessions_storage, user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage)
            session_storage = os.path.join(user_storage, session_id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage)

            images_storage = os.path.join(session_storage, "images")
            
            if not os.path.exists(images_storage):
                os.makedirs(images_storage)

            return images_storage
        except Exception as e:
            raise Exception(f"Error in getting images file path: {e}")

    def store_image_file(self, file, filename, user_id, session_id):
        try:
            # check file is correct
            
            images_storage = self.__get_images_storage_path(user_id, session_id)
            image_file_path = os.path.join(images_storage, filename)
            file.save(image_file_path)
        except Exception as e:
            raise Exception(f"Error in saving image file: {e}")

    def get_encoded_image(self, image_name, user_id, session_id):
        try:
            image_path = os.path.join(self.__get_images_storage_path(user_id, session_id), image_name)
            with open(image_path, "rb") as image_file:
                 return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"_get_encoded_image :: {e}")