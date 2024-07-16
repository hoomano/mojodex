import configparser
import os
from mojodex_core.logging_handler import MojodexCoreLogger
from mojodex_core.stt.openai_stt import OpenAISTT
from mojodex_core.stt.stt_engine import SttEngine
from mojodex_core.user_storage_manager.user_audio_file_manager import UserAudioFileManager


class STTService:
    """
    Speech-to-Text (STT) class for using STT in the Mojodex system.
    """
    stt_conf_filename = "stt_models.conf"
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
            try:
                self.logger = MojodexCoreLogger(self.__class__.__name__)
                self._load_conf()
                
                # Let's choose the first available engine
                self.stt_engine: SttEngine = self._build_engine(self.available_stt_engines[0]) if len(self.available_stt_engines) > 0 else None
                
            except Exception as e:
                raise Exception(f"{self.__class__.__name__} : __init__ :: {e}") 
            self.__class__._initialized = True

    def _load_conf(self):
        """
        Loads the configuration file for the stt engines.
        """
        try:
            conf_file = os.path.join(os.path.dirname(__file__), self.stt_conf_filename)
            self.config_parser = configparser.ConfigParser()
            self.config_parser.read(conf_file)
        except Exception as e:
            raise Exception(f"_load_conf :: {e}")


    @property
    def available_stt_engines(self):
        """
        Returns the list of available stt engines from the configuration file.
        """
        try:
            return self.config_parser.sections()
        except Exception as e:
            raise Exception(f"available_embedding_engines :: {e}")
        
    @property
    def is_stt_configured(self):
        return self.stt_engine is not None
    
    def _get_engine_conf(self, engine_section):
        """
        Returns the configuration for a given engine section.
        """
        try:
            return dict(self.config_parser[engine_section])
        except Exception as e:
            raise Exception(f"_get_provider_conf :: {e}")
    
    def _build_engine(self, engine_section):
        """
        Returns an instance of the stt engine based on the engine section.
        """
        try:
            engine_conf = self._get_engine_conf(engine_section)
            provider_name, model_name = engine_section.split('/')
            if model_name is None or provider_name is None:
                raise Exception(f"In config file {self.stt_conf_filename} section [{engine_section}] provider_name or model_name is missing")
              
            if provider_name == "openai":
                api_key = engine_conf["openai_api_key"]
                engine = OpenAISTT(model_name, api_key, provider_name)
            elif provider_name == "azure":
                api_key = engine_conf["whisper_azure_openai_key"]
                api_type = provider_name
                api_base = engine_conf["whisper_azure_openai_api_base"]
                api_version = engine_conf["whisper_azure_version"]
                deployment_id = engine_conf["whisper_azure_openai_deployment_id"]
                engine = OpenAISTT(model_name, api_key, api_type, deployment_id=deployment_id, api_base=api_base, api_version=api_version)
            else:
                raise Exception(f"provider_name {provider_name} is not supported")

            return engine
        except Exception as e:
            raise Exception(f"_build_engine :: {e}")


    def transcribe(self, filepath, user_id, user_task_execution_pk, task_name_for_system):
        try:
            if not self.is_stt_configured:
                raise Exception("STT engine is not configured")
            if filepath is None:
                raise Exception("filepath is None")
            transcription = self.stt_engine.transcribe(filepath, user_id, user_task_execution_pk, task_name_for_system)
            return transcription
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: transcribe: {e}")
