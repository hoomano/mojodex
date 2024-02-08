import os


class AzureOpenAIConf:
    openai_conf_file = "/data/openai.conf"

    azure_gpt4_turbo_conf = {
        "api_key": os.environ.get("GPT4_TURBO_AZURE_OPENAI_KEY",  os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("MAIN_MODEL_API_TYPE"),
        "api_version": os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("GPT4_TURBO_AZURE_OPENAI_DEPLOYMENT_ID", 'gpt-4-1106-preview')
    }

    azure_conf_embedding = {
        "api_key": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_KEY", os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("EMBEDDING_API_TYPE"),
        "api_version": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_DEPLOYMENT_ID", "text-embedding-ada-002")
    }
