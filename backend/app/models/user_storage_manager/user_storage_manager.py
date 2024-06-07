from abc import ABC, abstractmethod
import os
class UserStorageManager(ABC):
    sessions_storage = "/data/users"

    def _get_user_storage(self, user_id):
        try:
            user_storage = os.path.join(self.sessions_storage, user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage)
            return user_storage
        except Exception as e:
            raise Exception(f"_get_user_storage: {e}")

    def _get_session_storage(self, user_id, session_id):
        try:
            user_storage = self._get_user_storage(user_id)
            session_storage = os.path.join(user_storage, session_id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage)
            return session_storage
        except Exception as e:
            raise Exception(f"_get_session_storage: {e}")