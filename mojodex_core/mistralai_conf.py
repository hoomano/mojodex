import os

# TODO: move to /llm.conf
class MistralAIConf:

    mistral_medium_conf = {
        "api_key": os.environ.get("MISTRAL_API_KEY"),
        "api_model": "mistral-medium",
    }

    azure_mistral_large_conf = {
        "api_key": os.environ.get("MISTRAL_AZURE_API_KEY"),
        "endpoint": os.environ.get("MISTRAL_AZURE_API_BASE"),
        "api_model": "mistral-large",
    }

    mistral_large_conf = {
        "api_key": os.environ.get("MISTRAL_API_KEY"),
        "api_model": "mistral-large",
    }