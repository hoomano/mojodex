import os

from mojodex_backend_logger import MojodexBackendLogger

from models.user_storage_manager.user_storage_manager import UserStorageManager


class UserImagesFileManager(UserStorageManager):

    def __init__(self):
        try:
            self.logger = MojodexBackendLogger(f"{self.__class__.__name__}")
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} __init__ : {e}")

    def get_images_storage_path(self, user_id, session_id):
        try:
            session_storage = self._get_session_storage(user_id, session_id)

            images_storage = os.path.join(session_storage, "images")

            if not os.path.exists(images_storage):
                os.makedirs(images_storage)

            return images_storage
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_images_storage_path: {e}")

    def store_image_file(self, file, filename, user_id, session_id):
        try:
            # check file is correct

            images_storage = self.get_images_storage_path(user_id, session_id)
            image_file_path = os.path.join(images_storage, filename)
            file.save(image_file_path)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: store_image_file: {e}")

    def get_image_file_path(self, image_name, user_id, session_id):
        return os.path.join(self.get_images_storage_path(user_id, session_id), image_name)
