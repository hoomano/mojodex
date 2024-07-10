from abc import ABC, abstractmethod
from mojodex_core.db import with_db_session
from mojodex_core.entities.db_base_entities import MdUserVocabulary
from pydub import AudioSegment
from mojodex_core.logging_handler import log_error


class SttEngine(ABC):

    @with_db_session
    def __get_user_vocabulary(self, user_id, db_session):
        try:
            user_vocabulary = db_session.query(MdUserVocabulary).filter(MdUserVocabulary.user_id == user_id).order_by(
                MdUserVocabulary.creation_date.desc()).limit(50).all()
            return ", ".join([v.word for v in user_vocabulary]) if user_vocabulary else ""
        except Exception as e:
            raise Exception(f"__get_user_vocabulary:  {e}")
          
    def __get_audio_file_duration(self, audio_file_path):
        try:
            audio = AudioSegment.from_file(audio_file_path)
            duration = audio.duration_seconds
            return duration
        except Exception as e:
            raise Exception(f"__get_audio_file_duration:  {e}")

    @abstractmethod
    def _transcript(self, audio_file, vocab, file_duration, user_id, user_task_execution_pk=None, task_name_for_system=None):
        raise NotImplementedError("transcript method is not implemented")
    
    
    def get_transcript_and_file_duraction(self, audio_file_path, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            file_duration = self.__get_audio_file_duration(audio_file_path)

            audio_file = open(audio_file_path, "rb")
            try:
                vocab = self.__get_user_vocabulary(user_id)
            except Exception as e:
                log_error(f"{self.__class__.__name__} : get_transcript_and_file_duraction : user_id {user_id} - {e} ", notify_admin=True)
                vocab = ""

            transcription_text = self._transcript(audio_file, vocab, file_duration, user_id, user_task_execution_pk, task_name_for_system)
            return transcription_text, file_duration
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_transcript_and_file_duraction: {e}")