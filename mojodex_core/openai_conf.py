import os


# TODO: move to /llm.conf
class OpenAIConf:

    conf_embedding = {
        "api_key": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_KEY", os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("EMBEDDING_API_PROVIDER"),
        "api_version": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_DEPLOYMENT_ID", "text-embedding-ada-002")
    }

    whisper_conf = {
        "api_key": os.environ.get("WHISPER_AZURE_OPENAI_KEY",  os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("WHISPER_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("STT_API_PROVIDER"),
        "api_version": os.environ.get("WHISPER_AZURE_VERSION"),
        "deployment_id": os.environ.get("WHISPER_AZURE_OPENAI_DEPLOYMENT_ID", "whisper-1")
    }