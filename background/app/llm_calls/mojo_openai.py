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

    def openAICompletion(self, prompt, user_uuid, temperature, max_tokens, n_responses=1, frequency_penalty=0,
                         presence_penalty=0, stop=None, stream=False, stream_callback=None):
        """
        :param prompt: The prompt to give to openAI
        :param user_uuid: Compulsory for openAI to track harmful content. If a user tries to pass the openAI moderation, we will receive an email with this id and we can go back to him to remove his access.
        :param temperature: The higher the temperature, the crazier the text
        :param max_tokens: The maximum number of tokens to generate
        :param n_responses: The number of responses to generate for each prompt (default 1)
        :param frequency_penalty: The higher this is, the less likely the model is to repeat the same line verbatim (default 0)
        :param presence_penalty: The higher this is, the more likely the model is to talk about something that was mentioned in the prompt (default 0)
        :param stop: Token at which text generation is stopped
        :param stream: If True, will stream the completion
        :param stream_callback: If stream is True, will call this function with the completion as parameter
        :return: A list of n contents generated by GPT
        """
        # ensure if stream is true, n_responses = 1
        if stream and n_responses != 1:
            n_responses = 1
            logging.warning("n_responses must be 1 if stream is True")
        completion = self.client.completions.create(
            prompt=prompt,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            n=n_responses,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            stop=stop,
            user=user_uuid,
            stream=stream
        )
        if stream:
            complete_text = ""
            for token in completion:
                partial_token = token.choices[0].text
                complete_text += partial_token
                if stream_callback is not None:
                    try:
                        stream_callback(complete_text)
                    except Exception as e:
                        logging.error(f"🔴 Error in streamCallback : {e}")
            return [complete_text]
        return [content.text for content in completion.choices]

    def openAIChatCompletion(self, messages, user_uuid, temperature, max_tokens, n_responses=1, frequency_penalty=0,
                             presence_penalty=0, stream=False, stream_callback=None, json_format=False):
        """
        OpenAI chat completion
        :param messages: List of messages composing the conversation, each message is a dict with keys "role" and "content"
        :param user_uuid: Compulsory for openAI to track harmful content. If a user tries to pass the openAI moderation, we will receive an email with this id and we can go back to him to remove his access.
        :param temperature: The higher the temperature, the crazier the text
        :param max_tokens: The maximum number of tokens to generate
        :param n_responses: The number of responses to generate for each prompt (default 1)
        :param frequency_penalty: The higher this is, the less likely the model is to repeat the same line verbatim (default 0)
        :param presence_penalty: The higher this is, the more likely the model is to talk about something that was mentioned in the prompt (default 0)
        :param stream: If True, will stream the completion
        :param stream_callback: If stream is True, will call this function with the completion as parameter
        :param json_format: If True, will return a json object
        :return: List of n generated messages
        """
        # ensure if stream is true, n_responses = 1
        if stream and n_responses != 1:
            n_responses = 1
            logging.warning("n_responses must be 1 if stream is True")
        completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            n=n_responses,
            frequency_penalty=frequency_penalty,
            presence_penalty=presence_penalty,
            # Stop Not supported !
            user=user_uuid,
            stream=stream,
            response_format={"type": "json_object"} if json_format else None
        )
        if stream:
            complete_text = ""
            for token in completion:
                choice = token.choices[0]
                partial_token = choice.delta
                if partial_token.content:
                    complete_text += partial_token.content
                    if stream_callback is not None:
                        try:
                            stream_callback(complete_text)
                        except Exception as e:
                            logging.error(f"🔴 Error in streamCallback: {e}")
            return [complete_text]

        return [content.message.content for content in completion.choices]

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
