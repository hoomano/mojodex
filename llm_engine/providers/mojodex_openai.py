from langchain_openai import ChatOpenAI
import logging
import os

from .hub import GPT4_TURBO, LLMProvider

logging.basicConfig(level=logging.ERROR)

openai_list = []

## GPT4 Turbo on OpenAI

openai_api_key = os.environ.get("OPENAI_API_KEY")

if not openai_api_key:
    from dotenv import load_dotenv
    load_dotenv()
    openai_api_key = os.environ.get("OPENAI_API_KEY")


if not openai_api_key:
    logging.info("OpenAI environment variables not found")

try:
    model = ChatOpenAI(openai_api_key=openai_api_key)
    openai_list.append(LLMProvider(GPT4_TURBO, model))
except Exception as e:
        logging.error(f"🔴 Error initializing GPT4 on OpenAI : {e}")

