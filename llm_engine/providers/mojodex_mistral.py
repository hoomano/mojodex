from langchain_mistralai.chat_models import ChatMistralAI

import logging
import os

from .hub import MISTRAL_TINY, LLMProvider
logging.basicConfig(level=logging.ERROR)

mistral_list = []

## mistral-tiny on Mistral

mistral_api_key = os.environ.get("MISTRAL_API_KEY")

if not mistral_api_key:
    from dotenv import load_dotenv
    load_dotenv()
    mistral_api_key = os.environ.get("MISTRAL_API_KEY")


if not mistral_api_key:
    logging.info("OpenAI environment variables not found")

try:
    model = ChatMistralAI(mistral_api_key=mistral_api_key)
    mistral_list.append(LLMProvider(MISTRAL_TINY, model))
except Exception as e:
        logging.error(f"🔴 Error initializing mistral-tiny on Mistral : {e}")

