import os
from mojodex_core.user_storage_manager.user_storage_manager import UserStorageManager


class UserImagesFileManager(UserStorageManager):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UserImagesFileManager, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance


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
