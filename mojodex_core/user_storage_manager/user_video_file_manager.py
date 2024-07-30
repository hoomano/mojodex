
import os

from mojodex_core.user_storage_manager.user_storage_manager import UserStorageManager


class UserVideoFileManager(UserStorageManager):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UserVideoFileManager, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def get_videos_storage_path(self, user_id, session_id):
        try:
            session_storage = self._get_session_storage(user_id, session_id)

            videos_storage = os.path.join(session_storage, "videos")

            if not os.path.exists(videos_storage):
                os.makedirs(videos_storage)

            return videos_storage
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_videos_storage_path: {e}")

    def store_video_file(self, file, filename, user_id, session_id):
        try:
            videos_storage = self.get_videos_storage_path(user_id, session_id)
            video_file_path = os.path.join(videos_storage, filename)
            file.save(video_file_path)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: store_video_file: {e}")

    def get_video_file_path(self, video_name, user_id, session_id):
        return os.path.join(self.get_videos_storage_path(user_id, session_id), video_name)
    
    def get_video_file_from_form_storage_path(self, video_name, user_id, session_id):
        return os.path.join(self.get_videos_storage_path(user_id, session_id), video_name)
    