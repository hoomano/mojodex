import glob
from pydub import AudioSegment
import os

from mojodex_core.user_storage_manager.user_storage_manager import UserStorageManager


class UserAudioFileManager(UserStorageManager):
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(UserAudioFileManager, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    mojo_messages_audios_storage_dir_name="mojo_messages_audios"
    user_messages_audios_storage_dir_name="user_messages_audios"

    def _m4a_to_mp3(self, filename, directory):
        filepath = os.path.join(directory, filename)
        file_extension_final = 'm4a'
        try:
            track = AudioSegment.from_file(filepath,
                                           file_extension_final)
            mp3_filename = filename.replace(file_extension_final, 'mp3')
            mp3_path = os.path.join(directory, mp3_filename)
            file_handle = track.export(mp3_path, format='mp3', bitrate="192k")
            return mp3_path
        except Exception as e:
            raise Exception(f"_m4a_to_mp3 : ERROR CONVERTING {filepath}: {e}")

    def __get_vocal_chat_audio_storage_path(self, user_id, session_id, message_type):
        try:
            session_storage = self._get_session_storage(user_id, session_id)

            if message_type == "user_message":
                audio_storage = os.path.join(session_storage, self.user_messages_audios_storage_dir_name)
            else:
                raise Exception(f"Unknown message type : {message_type}")

            if not os.path.exists(audio_storage):
                os.makedirs(audio_storage)

            return audio_storage
        except Exception as e:
            raise Exception(f"{self.__class__.__name__}:: __get_audio_storage_path: {e}")

    def _get_audio_file_from_form_storage_path(self, user_id, session_id):
        try:
            session_storage = self._get_session_storage(user_id, session_id)

            audio_file_path = os.path.join(session_storage, "audio_files")

            if not os.path.exists(audio_file_path):
                os.makedirs(audio_file_path)

            return audio_file_path
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _get_audio_file_from_form_storage_path: {e}")


    # Store vocal chat messages
    def store_audio_file_from_vocal_chat(self, file, extension, user_id, session_id, message_type, message_id):
        try:
            audio_storage = self.__get_vocal_chat_audio_storage_path(
                user_id, session_id, message_type)
            message_id = f"{message_id}.{extension}"
            audio_file_path = os.path.join(audio_storage, message_id)

            # save file
            file.save(audio_file_path)

            # if extension is m4a, convert to mp3
            if extension == "m4a":
                audio_file_path = self._m4a_to_mp3(message_id, audio_storage)
                # remove m4a file
                os.remove(os.path.join(audio_storage, message_id))

            return audio_file_path
        except Exception as e:
            raise Exception(f"store_audio_file_from_vocal_chat: {e}")

    # Store audio files from input form
    # files[file_input], filename, user_id, session_id
    def store_audio_file_from_form(self, file, filename, user_id, session_id):
        try:
            audio_storage_path = self._get_audio_file_from_form_storage_path(
                user_id, session_id)
            audio_file_path = os.path.join(audio_storage_path, filename)

            # save file
            file.save(audio_file_path)

            return audio_file_path
        except Exception as e:
            raise Exception(f"store_audio_file_from_form: {e}")

    def get_audio_file_from_form_storage_path(self, filename, user_id, session_id):
        try:
            return os.path.join(self._get_audio_file_from_form_storage_path(user_id, session_id), filename)
        except Exception as e:
            raise Exception(f"get_audio_file_from_form_storage_path: {e}")

    def find_file_from_message_id(self, user_id, session_id, message_type, message_id):
        try:
            # Else case is used to manage user_message management previous error:
            # The audio_transcript has been correctly stored but has not been correctly set into db and sent back to user
            # Therefore, we can find it using its message_id
            audio_storage = self.__get_vocal_chat_audio_storage_path(
                user_id, session_id, message_type)
            # find any file in this path that name without extension is message_id
            search_pattern = os.path.join(
                audio_storage,  f"{message_id}.*")
            # Use glob.glob() to find all matching files, considering any file extension
            matching_files = glob.glob(search_pattern)
            if not matching_files:
                raise Exception(
                    f"Audio file not found for message_id: {message_id}")
            return matching_files[0]
        except Exception as e:
            raise Exception(f"find_file_from_message_id: {e}")
   
    def get_mojo_messages_audio_storage(self, user_id, session_id):
        try:
            session_storage = self._get_session_storage(user_id, session_id)
            mojo_messages_audio_storage = os.path.join(session_storage, self.mojo_messages_audios_storage_dir_name)
            if not os.path.exists(mojo_messages_audio_storage):
                os.makedirs(mojo_messages_audio_storage, exist_ok=True)
            return mojo_messages_audio_storage
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : get_mojo_messages_audio_storage :: {e}")

    def get_user_messages_audio_storage(self, user_id, session_id):
        try:
            session_storage = self._get_session_storage(user_id, session_id)
            user_messages_audio_storage = os.path.join(session_storage, self.user_messages_audios_storage_dir_name)
            if not os.path.exists(user_messages_audio_storage):
                os.makedirs(user_messages_audio_storage, exist_ok=True)
            return user_messages_audio_storage
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : get_user_messages_audio_storage :: {e}")