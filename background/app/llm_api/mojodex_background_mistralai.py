
from mojodex_core.llm_engine.providers.mistralai_llm import MistralAILLM
from mojodex_core.llm_engine.providers.openai_embedding import OpenAIEmbeddingProvider
import os
from mojodex_core.logging_handler import log_error

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



class MojodexMistralAI(MistralAILLM, OpenAIEmbeddingProvider):
    dataset_dir = "/data/prompts_dataset"

    def __init__(self, mistral_conf, label='unknown', max_retries=0):
        api_key = mistral_conf["api_key"]
        self.model = mistral_conf["api_model"]

        endpoint = mistral_conf.get("endpoint") if mistral_conf.get(
            "endpoint") else None
        api_type= "azure" if mistral_conf.get("endpoint") else "la_plateforme"
        
        self.label = label

        # if dataset_dir does not exist, create it
        if not os.path.exists(self.dataset_dir):
            os.mkdir(self.dataset_dir)
        if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
            os.mkdir(os.path.join(self.dataset_dir, "chat"))
        if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
            os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))
        
        MistralAILLM.__init__(self, api_key, endpoint, self.model,
                              api_type=api_type, max_retries=max_retries)

    
    def invoke(self, messages, user_id, temperature, max_tokens, n_responses=1,
                       frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                       user_task_execution_pk=None, task_name_for_system=None):
        try:

            responses = super().chatCompletion(messages, temperature, max_tokens, n_responses=n_responses,
                                   frequency_penalty=frequency_penalty, presence_penalty=presence_penalty, stream=stream, stream_callback=stream_callback, json_format=json_format)
            try:
                self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": n_responses,
                                     "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                     "messages": [{'role': message.get('role') if message.get('role') else 'unknown', 'content': message.get('content') if message.get('content') else "no_content"} for message in messages], "responses": responses, "model_config": self.model}, task_name_for_system, "chat")
            except e:
                log_error(f"Error while writing in dataset: {e}", notify_admin=False)

            return responses
        except Exception as e:
            log_error(
                f"Error in Mojodex Mistral AI chat for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
            raise Exception(
                f"🔴 Error in Mojodex Mistral AI chat: {e} - model: {self.model}")
