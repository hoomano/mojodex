import base64
from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM
from mojodex_core.logging_handler import MojodexCoreLogger, log_error

from math import ceil
from typing import List

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager
from PIL import Image
import os

from mojodex_core.llm_engine.mpt import MPT

mojo_openai_logger = MojodexCoreLogger("mojo_openai_logger")


class VisionMessagesData:
    def __init__(self, role: str, text: str, images_path: List[str]):
        self.role = role
        self.text = text
        self.images_path = images_path


class OpenAIVisionLLM(OpenAILLM):
    available_vision_models = ["gpt-4o-vision", "gpt-4-vision-preview"]

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def __init__(self, llm_conf, llm_backup_conf=None, max_retries=3):
        super().__init__(llm_conf, llm_backup_conf, max_retries)

    def _image_resize(self, width, height):
        try:
            # images are first scaled to fit within a 2048 x 2048 square
            max_size = 2048
            aspect_ratio = width / height
            if max(width, height) > max_size:
                if aspect_ratio > 1:
                    width, height = max_size, int(max_size / aspect_ratio)
                else:
                    width, height = int(max_size * aspect_ratio), max_size

            # Then, they are scaled such that the shortest side of the image is 768px long
            shortest_side = 768
            if min(width, height) > shortest_side:
                if aspect_ratio > 1:
                    width, height = int((shortest_side / height) * width), shortest_side
                else:
                    width, height = shortest_side, int((shortest_side / width) * height)

            return width, height
        except Exception as e:
            raise Exception(f"_image_resize : {e}")

    def num_tokens_from_image(self, image_path: str):
        try:
            with Image.open(image_path) as img:
                original_width, original_height = img.size

            # According to https://platform.openai.com/docs/guides/vision
            resized_width, resized_height = self._image_resize(original_width, original_height)
            # Finally, we count how many 512px squares the image consists of
            tile_size = 512
            w = ceil(resized_width / tile_size)
            h = ceil(resized_height / tile_size)
            # Each of those squares costs 170 tokens. Another 85 tokens are always added to the final total.
            base_tokens, tile_tokens = 85, 170
            total = base_tokens + tile_tokens * h * w
            return total
        except Exception as e:
            raise Exception(f"num_tokens_from_image : {e}")

    @staticmethod
    def get_image_message_url_prefix(image_name):
        try:
            extension = image_name.split(".")[-1].lower()
            # check if extension is allowed
            if extension not in OpenAIVisionLLM.ALLOWED_EXTENSIONS:
                raise Exception(f"Image extension not allowed: {extension}")
            return 'data:image/' + extension
        except Exception as e:
            raise Exception(f"_get_image_message_url_prefix :: {e}")

    def get_encoded_image(self, image_path):
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"_get_encoded_image :: {e}")

    def recursive_invoke(self, messages_data: List[VisionMessagesData], user_id: str, temperature: float,
                          max_tokens: int, label: str,
                          stream: bool = False, stream_callback=None, user_task_execution_pk: int = None,
                          task_name_for_system: str = None, frequency_penalty: float = 0, presence_penalty: float = 0,
                          n_additional_calls_if_finish_reason_is_length: int = 0, **kwargs):

        try:
            n_tokens_prompt = 0
            n_tokens_conversation = 0
            messages = []
            for index in range(0, len(messages_data)):

                message_data = messages_data[index]
                message = {"role": message_data.role, 'content': [
                    {"type": "text", "text": message_data.text}
                ]
                           }
                new_messages = [message]

                n_text_tokens = self.num_tokens_from_text_messages([message])

                n_image_tokens = 0
                for image_path in message_data.images_path:
                    encoded_image = self.get_encoded_image(image_path)
                    image_data = {"type": "image_url",
                                  "image_url": {
                                      "url": f"{OpenAIVisionLLM.get_image_message_url_prefix(image_path)};base64,{encoded_image}"}
                                  }
                    # if message's role is "system", we can't add image to the message so we will add a user message with the image
                    if message_data.role == "system":
                        new_messages.append({"role": "user", 'content': [image_data]})
                    else:
                        message['content'].append(image_data)
                    n_image_tokens += self.num_tokens_from_image(image_path)

                messages += new_messages

                if index == 0:
                    n_tokens_prompt += n_text_tokens + n_image_tokens
                else:
                    n_tokens_conversation += n_text_tokens + n_image_tokens

            response = self._call_completion_with_rate_limit_management(messages, user_id, temperature, max_tokens,
                                                                         frequency_penalty, presence_penalty,
                                                                         stream, stream_callback,
                                                                         n_additional_calls_if_finish_reason_is_length,
                                                                         **kwargs)

            if response is None:
                return None

            n_tokens_response = self.num_tokens_from_text_messages([{'role': 'assistant', 'content': response[0]}])

            self.tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, n_tokens_conversation,
                                                        n_tokens_response,
                                                        self.name, label, user_task_execution_pk, task_name_for_system)
            self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                                    "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                    "messages": messages, "responses": response}, task_name_for_system, "chat",
                                   label=label)
            return response
        except Exception as e:
            raise Exception(f"recursive_invoke: {e}")
