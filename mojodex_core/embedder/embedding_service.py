import configparser
import os
from mojodex_core.embedder.embedding_provider import EmbeddingProvider
from mojodex_core.embedder.openai_embedding import OpenAIEmbedding
from mojodex_core.logging_handler import MojodexCoreLogger
from mojodex_core.stt.openai_stt import OpenAISTT
from mojodex_core.openai_conf import OpenAIConf
from mojodex_core.user_storage_manager.user_audio_file_manager import UserAudioFileManager


class EmbeddingService:
    """
    EmbeddingService class for using embedding in the Mojodex system.
    """
    embedding_conf_filename = "embedding_models.conf"
    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingService, cls).__new__(
                cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance


    def __init__(self):
        """
        Initialize the EmbeddingService provider based on the environment variable."""
        if not self.__class__._initialized:
            try:
                self.logger = MojodexCoreLogger(self.__class__.__name__)
                self._load_conf()

                # Let's choose the first available provider
                self.embedding_provider: EmbeddingProvider = self._build_provider(self.available_embedding_providers[0])
            except Exception as e:
                raise Exception(f"{self.__class__.__name__} : __init__ :: {e}")
            self.__class__._initialized = True

    def _load_conf(self):
        try:
            conf_file = os.path.join(os.path.dirname(__file__), self.embedding_conf_filename)
            self.config_parser = configparser.ConfigParser()
            self.config_parser.read(conf_file)
        except Exception as e:
            raise Exception(f"_load_conf :: {e}")

    @property
    def available_embedding_providers(self):
        try:
            return self.config_parser.sections()
        except Exception as e:
            raise Exception(f"available_embedding_providers :: {e}")

    def _get_provider_conf(self, provider_section):
        try:
            return dict(self.config_parser[provider_section])
        except Exception as e:
            raise Exception(f"_get_provider_conf :: {e}")

    def _build_provider(self, provider_section):
        try:
            provider_conf = self._get_provider_conf(provider_section)
            provider_name, model_name = provider_section.split('/')
            if model_name is None or provider_name is None:
                self.logger.error(
                    f"_build_provider() >> in config file {self.embedding_conf_filename} section [{provider_section}] provider_name or model_name is missing")
                return None
            
            provider = None
            conf = None

            if provider_name == "openai":
                conf = {
                    "api_key": provider_conf["openai_api_key"],
                    "api_type": provider_name,
                    "model_name": model_name
                }
                provider = OpenAIEmbedding(conf)
            elif provider_name == "azure":
                conf = {
                    "api_key": provider_conf["ada_embedding_azure_openai_key"],
                    "api_base": provider_conf["ada_embedding_azure_openai_api_base"],
                    "api_type": provider_name,
                    "api_version": provider_conf["ada_embedding_azure_openai_api_version"],
                    "deployment_id": provider_conf["ada_embedding_azure_openai_deployment_id"] if not provider_conf["ada_embedding_azure_openai_deployment_id"] is None else OpenAIEmbedding.default_embedding_model,
                    "model_name": model_name
                }
                provider = OpenAIEmbedding(conf)
            else:
                self.logger.error(f"_build_provider() >> provider_name {provider_name} is not supported")
                return None

            return provider
        except Exception as e:
            self.logger.error(f"_build_provider :: {e}")
            return None

    def embed(self, text, user_id, label, user_task_execution_pk, task_name_for_system, retries=5):
        try:
            return self.embedding_provider.embed(text, user_id, label, user_task_execution_pk, task_name_for_system, retries)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : embed :: {e}")
        
    @property
    def tokenizer(self):
        try:
            return self.embedding_provider.tokenizer
        except Exception as e:
            raise Exception(f"tokenizer :: {e}")