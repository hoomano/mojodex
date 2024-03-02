from langchain_openai import AzureChatOpenAI
from  .hub import LLMProvider
from core import GPT4_TURBO

import logging
import os
logging.basicConfig(level=logging.ERROR)

azure_list = []

## GPT4 Turbo on Azure OpenAI

api_key = os.environ.get("GPT4_TURBO_AZURE_OPENAI_KEY")
api_base = os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_BASE")
api_version = os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_VERSION")
deployment_id = os.environ.get("GPT4_TURBO_AZURE_OPENAI_DEPLOYMENT_ID")


# if not in env try loading environment variables from .env file
if not all([api_base, api_key, api_version, deployment_id]):
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.environ.get("GPT4_TURBO_AZURE_OPENAI_KEY")
    api_base = os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_BASE")
    api_version = os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_VERSION")
    deployment_id = os.environ.get("GPT4_TURBO_AZURE_OPENAI_DEPLOYMENT_ID")

# if still not found raise exception
if not all([api_base, api_key, api_version, deployment_id]):
    logging.info("GPT4 Turbo on Azure OpenAI environment variables not found")

try:
    model = AzureChatOpenAI(
        api_key=api_key,
        azure_endpoint=api_base,
        api_version=api_version,
        deployment_name=deployment_id,
        model_name='gpt-4-1106-preview',
    )
    azure_list.append(LLMProvider(GPT4_TURBO, model))
except Exception as e:
    logging.error(f"🔴 Error initializing GPT4 Turbo on Azure : {e}")



