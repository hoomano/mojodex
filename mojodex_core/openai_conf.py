import os


# TODO: move to /llm.conf
class OpenAIConf:


    whisper_conf = {
        "api_key": os.environ.get("WHISPER_AZURE_OPENAI_KEY",  os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("WHISPER_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("STT_API_PROVIDER"),
        "api_version": os.environ.get("WHISPER_AZURE_VERSION"),
        "deployment_id": os.environ.get("WHISPER_AZURE_OPENAI_DEPLOYMENT_ID", "whisper-1")
    }