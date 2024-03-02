from providers.hub import LLMProvider, LLMProviderHub, GPT4_TURBO, MISTRAL_TINY, GPT4_32k

# Load the LLM providers for Mojodex
# See .env for the configuration details
# This will automatically load the providers
# if the environment variables are set
providers = LLMProviderHub()
