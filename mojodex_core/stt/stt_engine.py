from abc import ABC, abstractmethod
from pydub import AudioSegment


class SttEngine(ABC):

          
    def __get_audio_file_duration(self, audio_file_path):
        try:
            audio = AudioSegment.from_file(audio_file_path)
            duration = audio.duration_seconds
            return duration
        except Exception as e:
            raise Exception(f"__get_audio_file_duration:  {e}")

    @abstractmethod
    def transcribe(self, filepath, user_id, user_task_execution_pk, task_name_for_system):
        raise NotImplementedError("transcribe method is not implemented")
    
    
    def get_transcript_and_file_duraction(self, audio_file_path, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            file_duration = self.__get_audio_file_duration(audio_file_path)

            # transcription_text = self.transcribe(audio_file, vocab, file_duration, user_id, user_task_execution_pk, task_name_for_system)
            transcription_text = self.transcribe(audio_file_path, user_id, user_task_execution_pk, task_name_for_system)
            return transcription_text, file_duration
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: get_transcript_and_file_duraction: {e}")