import glob
from pydub import AudioSegment
import os
from models.session import Session as SessionModel

from mojodex_backend_logger import MojodexBackendLogger
from azure_openai_conf import AzureOpenAIConf

from models.llm_calls.mojodex_openai import MojodexOpenAI


class UserAudioFileManager:
    logger_prefix = "UserAudioFileManager::"

    def __init__(self):
        try:
            self.logger = MojodexBackendLogger(f"{UserAudioFileManager.logger_prefix}")
            self.mojodex_whisper = MojodexOpenAI(AzureOpenAIConf.azure_whisper_conf, "whisper-azure")
        except Exception as e:
            raise Exception(f"Error in initializing UserAudioFileManager: {e}")

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
            raise Exception(f"ERROR CONVERTING {filepath}: {e}")


    def __get_audio_storage_path(self, user_id, session_id, message_type):
        try:
            user_storage = os.path.join(SessionModel.sessions_storage, user_id)
            if not os.path.exists(user_storage):
                os.makedirs(user_storage)
            session_storage = os.path.join(user_storage, session_id)
            if not os.path.exists(session_storage):
                os.makedirs(session_storage)

            if message_type == "user_message":
                audio_storage = os.path.join(session_storage, "user_messages_audios")
            elif message_type == "process_step_message":
                audio_storage = os.path.join(user_storage, "process_steps_audio")
            elif message_type == "user_followup":
                audio_storage = os.path.join(user_storage, "user_followups_audio")
            else:
                raise Exception(f"Unknown message type : {message_type}")

            if not os.path.exists(audio_storage):
                os.makedirs(audio_storage)

            return audio_storage
        except Exception as e:
            raise Exception(f"Error in getting audio file path: {e}")

    def __store_audio_file(self, file, extension, user_id, session_id, message_type, message_id):
        try:
            audio_storage = self.__get_audio_storage_path(user_id, session_id, message_type)
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
            raise Exception(f"Error in storing audio file: {e}")


    def extract_text_and_duration(self, file, extension, user_id, session_id, message_type, message_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            # backup_calls is for calling openai api in case default mode 'whisper azure'
            if file is not None:
                audio_file_path = self.__store_audio_file(file, extension, user_id, session_id, message_type, message_id)
            else:
                audio_storage = self.__get_audio_storage_path(user_id, session_id, message_type)
                # find any file in this path that name without extension is message_id
                search_pattern = os.path.join(audio_storage,  f"{message_id}.*")
                # Use glob.glob() to find all matching files, considering any file extension
                matching_files = glob.glob(search_pattern)
                if not matching_files:
                    raise Exception(f"Audio file not found for message_id: {message_id}")
                audio_file_path = matching_files[0]

            transcription, file_duration = self.mojodex_whisper.transcript(audio_file_path, user_id,
                                                                                           user_task_execution_pk=user_task_execution_pk,
                                                                                           task_name_for_system=task_name_for_system)

            return transcription, file_duration
        except Exception as e:
            raise Exception(f"Error in transcript speech: {e}")
