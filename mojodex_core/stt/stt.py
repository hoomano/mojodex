import os
from mojodex_core.stt.openai_stt import OpenAISTT
from mojodex_core.openai_conf import OpenAIConf
from mojodex_core.user_storage_manager.user_audio_file_manager import UserAudioFileManager


class STTService:
    """
    Speech-to-Text (STT) class for using STT in the Mojodex system.
    """

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(STTService, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance


    def __init__(self):
        """
        Initialize the STT engine based on the environment variable STT_ENGINE."""
        if not self.__class__._initialized:
            # Setup the stt engine
            stt_engine = os.environ.get("STT_ENGINE", "whisper")
            if stt_engine == "whisper":
                self._stt_provider = OpenAISTT(OpenAIConf.whisper_conf, label="whisper-azure")
            self.__class__._initialized = True


    @property
    def is_stt_configured(self):
        return self._stt_provider is not None

    def extract_text_and_duration(self, file, extension, user_id, session_id, message_type, message_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            if not self.is_stt_configured:
                raise Exception("STT engine is not configured")
            if file is not None:
                audio_file_path = UserAudioFileManager().store_audio_file(
                    file, extension, user_id, session_id, message_type, message_id)
            else:
                audio_file_path = UserAudioFileManager().find_file_from_message_id(user_id, session_id, message_type, message_id)

            transcription, file_duration = self._stt_provider.transcript(audio_file_path, user_id,
                                                               user_task_execution_pk=user_task_execution_pk,
                                                               task_name_for_system=task_name_for_system)

            return transcription, file_duration
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: extract_text_and_duration: {e}")

