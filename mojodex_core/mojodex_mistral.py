import json
import logging
import os

logging.basicConfig(level=logging.INFO)

from mojodex_core.logging_handler import log_error

from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage


# Make sure to have the MISTRAL_API_KEY environment variable set in your .env file
mistral_medium_conf = {
    "api_key": os.environ.get("MISTRAL_API_KEY"),
    "api_model": "mistral-medium",
}
azure_mistral_large_conf = {
    "api_key": os.environ.get("MISTRAL_AZURE_API_KEY"),
    "endpoint": os.environ.get("MISTRAL_AZURE_API_BASE"),
    "api_model": "mistral-large",
}


class MojodexMistralAI():
    dataset_dir = "/data/prompts_dataset"

    def __init__(self, mistral_conf, label):
        self.api_key = mistral_conf["api_key"]
        self.model = mistral_conf["api_model"]
        self.endpoint = mistral_conf.get("endpoint") if mistral_conf.get("endpoint") else "https://api.mistral.ai"
        self.label = label

        self.client = MistralClient(
            api_key=self.api_key,
            endpoint=azure_mistral_large_conf["endpoint"],
            )

        # if dataset_dir does not exist, create it
        if not os.path.exists(self.dataset_dir):
            os.mkdir(self.dataset_dir)
        if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
            os.mkdir(os.path.join(self.dataset_dir, "chat"))
        if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
            os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))


    def __write_in_dataset(self, json_data, task_name_for_system, type):
        try:
            # write data in MojodexMistralAI.dataset_dir/label/task_name_for_system.json
            directory = f"{self.dataset_dir}/{type}/{self.label}/{task_name_for_system}"
            if not os.path.exists(directory):
                os.mkdir(directory)
            filename = len(os.listdir(directory)) + 1
            with open(os.path.join(directory, f"{filename}.json"), "w") as f:
                json.dump(json_data, f)
        except Exception as e:
            log_error(f"Error in Mojodex Mistral __write_in_dataset: {e}", notify_admin=False)

    def chat(self, messages, user_id, temperature, max_tokens, n_responses=1,
             frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
             user_task_execution_pk=None, task_name_for_system=None):
        try:

            responses=[]

            try:                
                # ensure if stream is true, n_responses = 1
                if stream and n_responses != 1:
                    n_responses = 1
                    logging.warning("n_responses must be 1 if stream is True")

                

                # Convert messages into Mistral ChatMessages
                if len(messages) == 1:
                    messages = [ChatMessage(role='user', content=messages[0]['content'])]
                else:
                    messages = [ChatMessage(role=message['role'], content=message['content']) for message in messages]
                
                logging.info(f"messages={messages}")

                stream_response = self.client.chat_stream(model=self.model, messages=messages, temperature=temperature, max_tokens=max_tokens)
            
                if stream:
                    complete_text = ""
                    for chunk in stream_response:
                        partial_token = chunk.choices[0].delta.content
                        complete_text += partial_token if partial_token else ""
                        if stream_callback is not None:
                            try:
                                stream_callback(complete_text)
                            except Exception as e:
                                logging.error(f"🔴 Error in streamCallback : {e}")
                responses = [complete_text] #[content.text for content in stream_response.choices]

            except Exception as e:
                log_error(f"💨❌: Error in Mojodex Mistral chat: {e}")
                
 
            self.__write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": n_responses,
                                        "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                        "messages": [{'role': message.role, 'content': message.content} for message in messages], "responses": responses, "model_config": self.model}, task_name_for_system, "chat")
            return responses
        except Exception as e:
            log_error(f"Error in Mojodex Mistral AI chat for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=False)
            raise Exception(f"🔴 Error in Mojodex OpenAI chat: {e} - model: {self.model}")

