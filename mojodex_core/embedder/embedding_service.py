import configparser
import os
from mojodex_core.embedder.embedding_engine import EmbeddingEngine
from mojodex_core.embedder.openai_embedding import OpenAIEmbedding
from mojodex_core.logging_handler import MojodexCoreLogger

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
        Initialize the EmbeddingService engine based on the environment variable.
        There is a single embedding engine for the whole system.
        """
        if not self.__class__._initialized:
            try:
                self.logger = MojodexCoreLogger(self.__class__.__name__)
                self._load_conf()

                # Let's choose the first available engine
                self.embedding_engine: EmbeddingEngine = self._build_engine(self.available_embedding_engines[0])
            except Exception as e:
                raise Exception(f"{self.__class__.__name__} : __init__ :: {e}")
            self.__class__._initialized = True

    def _load_conf(self):
        """
        Loads the configuration file for the embedding engines.
        """
        try:
            conf_file = os.path.join(os.path.dirname(__file__), self.embedding_conf_filename)
            self.config_parser = configparser.ConfigParser()
            self.config_parser.read(conf_file)
        except Exception as e:
            raise Exception(f"_load_conf :: {e}")

    @property
    def available_embedding_engines(self):
        """
        Returns the list of available embedding engines from the configuration file.
        """
        try:
            return self.config_parser.sections()
        except Exception as e:
            raise Exception(f"available_embedding_engines :: {e}")

    def _get_engine_conf(self, engine_section):
        """
        Returns the configuration for a given engine section.
        """
        try:
            return dict(self.config_parser[engine_section])
        except Exception as e:
            raise Exception(f"_get_engine_conf :: {e}")

    def _build_engine(self, engine_section):
        """
        Returns an instance of the embedding engine based on the engine section.
        """
        try:
            engine_conf = self._get_engine_conf(engine_section)
            provider_name, model_name = engine_section.split('/')
            if model_name is None or provider_name is None:
                raise Exception(f"In config file {self.embedding_conf_filename} section [{engine_section}] provider_name or model_name is missing")
              
            
            if provider_name == "openai":
                api_key = engine_conf["openai_api_key"]
                engine = OpenAIEmbedding(model_name, api_key, provider_name)
            elif provider_name == "azure":
                api_key = engine_conf["ada_embedding_azure_openai_key"]
                api_type = provider_name
                api_base = engine_conf["ada_embedding_azure_openai_api_base"]
                api_version = engine_conf["ada_embedding_azure_openai_api_version"]
                deployment_id = engine_conf["ada_embedding_azure_openai_deployment_id"]
                engine = OpenAIEmbedding(model_name, api_key, api_type, deployment=deployment_id, api_base=api_base, api_version=api_version)
            else:
                raise Exception(f"provider_name {provider_name} is not supported")

            return engine
        except Exception as e:
            raise Exception(f"_build_engine :: {e}")
        

    def embed(self, text, user_id, label, user_task_execution_pk=None, task_name_for_system=None, retries=5, **kwargs):
        try:
            return self.embedding_engine.embed(text, user_id, label, user_task_execution_pk, task_name_for_system, retries, **kwargs)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : embed :: {e}")
        
    @property
    def tokenizer(self):
        try:
            return self.embedding_engine.tokenizer
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} : tokenizer :: {e}")