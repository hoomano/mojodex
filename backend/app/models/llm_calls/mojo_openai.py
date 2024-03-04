from openai import OpenAI, AzureOpenAI
import logging
import tiktoken


class MojoOpenAI:
    def __init__(self, api_key, api_base, api_version, model, api_type='azure', max_retries=3):
        """
        :param api_key: API key to call openAI
        :param api_base: Endpoint to call openAI
        :param api_version: Version of the API to user
        :param model: Model to use (deployment_id for azure)
        :param api_type: 'azure' or 'openai'
        :param max_retries: max_retries for openAI calls on rateLimit errors, unavailable... (default 3)
        """
        try:
            self.model = model
            self.max_retries = max_retries
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=self.model,
                api_key=api_key,
                max_retries=self.max_retries
            ) if api_type == 'azure' else OpenAI(api_key=api_key)

            # DEBUG was too verbose and applied to openai
            logging.basicConfig(level=logging.WARNING)
        except Exception as e:
            raise Exception(f"🔴 Error initializing MojoOpenAI __init__  : {e}")


    # calculate the number of tokens in a given string
    def num_tokens_from_string(self, string):
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding("p50k_base")
        num_tokens = len(encoding.encode(string))
        return num_tokens


    def num_tokens_from_messages(self, messages):
        # Working for models gpt-4, gpt-3.5-turbo, text-embedding-ada-002
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """Returns the number of tokens used by a list of messages.
        Code inspired from : https://platform.openai.com/docs/guides/chat/introduction - 04-12-2023"""
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            num_tokens = 0
            for message in messages:
                num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
                for key, value in message.items():
                    num_tokens += len(encoding.encode(value))
                    if key == "name":  # if there's a name, the role is omitted
                        num_tokens += -1  # role is always required and always 1 token
            num_tokens += 2  # every reply is primed with <im_start>assistant
            return num_tokens
        except Exception as e:
            raise Exception(f"🔴 Error in num_tokens_from_messages : {e}")


    def openAIChatCompletion(self, messages, user_uuid, temperature, max_tokens, frequency_penalty=0,
                             presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                             n_additional_calls_if_finish_reason_is_length=0, assistant_response="", n_calls=0):
        """
        OpenAI chat completion
        :param messages: List of messages composing the conversation, each message is a dict with keys "role" and "content"
        :param user_uuid: Compulsory for openAI to track harmful content. If a user tries to pass the openAI moderation, we will receive an email with this id and we can go back to him to remove his access.
        :param temperature: The higher the temperature, the crazier the text
        :param max_tokens: The maximum number of tokens to generate
        :param frequency_penalty: The higher this is, the less likely the model is to repeat the same line verbatim (default 0)
        :param presence_penalty: The higher this is, the more likely the model is to talk about something that was mentioned in the prompt (default 0)
        :param stream: If True, will stream the completion
        :param stream_callback: If stream is True, will call this function with the completion as parameter
        :param json_format: If True, will return a json object
        :param n_additional_calls_if_finish_reason_is_length: If the finish reason is "length", will relaunch the function, instructing the assistant to continue its response
        :param assistant_response: Assistant response to add to the completion
        :param n_calls: Number of calls to the function
        :return: List of n generated messages
        """
        completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            user=user_uuid,
            stream=stream,
            response_format={"type": "json_object"} if json_format else None
        )
        if stream:
            complete_text = ""
            finish_reason = None
            for stream_chunk in completion:
                choice = stream_chunk.choices[0]
                partial_token = choice.delta
                finish_reason = choice.finish_reason
                if partial_token.content:
                    complete_text += partial_token.content
                    if stream_callback is not None:
                        try:
                            stream_callback(complete_text)
                        except Exception as e:
                            logging.error(f"🔴 Error in streamCallback: {e}")

            response = complete_text
        else:
            response = completion.choices[0].message.content
            finish_reason = completion.choices[0].finish_reason

        if finish_reason == "length" and n_calls < n_additional_calls_if_finish_reason_is_length:
            # recall the function with assistant_message + user_message
            messages = messages + [{'role': 'assistant', 'content': response},
                                   {'role': 'user', 'content': 'Continue'}]
            return self.openAIChatCompletion(messages, user_uuid, temperature, max_tokens,
                                             frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                             stream=stream, stream_callback=stream_callback, json_format=json_format,
                                             assistant_response=assistant_response + " " + response,
                                             n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length,
                                             n_calls=n_calls + 1)
        return [assistant_response + " " + response] # [] is a legacy from the previous version that could return several completions. Need complete refacto to remove.

    def openAIEmbedding(self, text):
        """
        :param text: Text to embed
        :return: Embedding
        """
        embedding = self.client.embeddings.create(
            input=text,
            model=self.model
        )
        return embedding.data[0].embedding
