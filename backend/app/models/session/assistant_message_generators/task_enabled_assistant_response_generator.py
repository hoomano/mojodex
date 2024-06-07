import base64
import json
import os
from datetime import datetime

import requests

from models.session.assistant_message_generators.assistant_response_generator import AssistantResponseGenerator
from abc import ABC, abstractmethod
from app import server_socket, model_loader

from mojodex_core.llm_engine.providers.openai_vision_llm import OpenAIVisionLLM, VisionMessagesData
from mojodex_core.logging_handler import log_error


class TaskEnabledAssistantResponseGenerator(AssistantResponseGenerator, ABC):
    logger_prefix = "TaskEnabledAssistantResponseGenerator :: "

    def __init__(self, prompt_template_path, mojo_message_token_stream_callback,
                 use_message_placeholder, tag_proper_nouns, chat_context, llm_call_temperature):
        try:
            super().__init__(prompt_template_path, chat_context, tag_proper_nouns, llm_call_temperature)
            self.mojo_message_token_stream_callback = mojo_message_token_stream_callback
            self.use_message_placeholder = use_message_placeholder
        except Exception as e:
            raise Exception(f"{self.logger_prefix} __init__ :: {e}")

    # getter for running_task
    @property
    def running_task(self):
        return self.context.state.running_task

    @property
    def running_user_task_execution(self):
        return self.context.state.running_user_task_execution

    @property
    def running_task_displayed_data(self):
        return self.context.state.running_task_displayed_data


    def __give_task_execution_title_and_summary(self, user_task_execution_pk):
        try:
            # call background backend /end_user_task_execution to update user task execution title and summary
            uri = f"{os.environ['BACKGROUND_BACKEND_URI']}/user_task_execution_title_and_summary"
            pload = {'datetime': datetime.now().isoformat(),
                     'user_task_execution_pk': user_task_execution_pk}
            internal_request = requests.post(uri, json=pload)
            if internal_request.status_code != 200:
                log_error(
                    f"Error while calling background user_task_execution_title_and_summary : {internal_request.json()}")
        except Exception as e:
            print(f"🔴 __give_title_and_summary_task_execution :: {e}")

    def generate_message(self, user_task_execution_pk=None, task_name_for_system=None):
        try:
            # call background for title and summary
            if self.running_user_task_execution:
                server_socket.start_background_task(self.__give_task_execution_title_and_summary,
                                                    self.running_user_task_execution.user_task_execution_pk)
            message = super().generate_message(user_task_execution_pk=self.running_user_task_execution.user_task_execution_pk if self.running_user_task_execution else None,
                                               task_name_for_system=self.running_task.name_for_system if self.running_task else None)
            if message and self.running_user_task_execution:
                message['user_task_execution_pk'] = self.running_user_task_execution.user_task_execution_pk
            return message
        except Exception as e:
            raise Exception(f"{self.logger_prefix} generate_message :: {e}")

    def _get_running_user_task_execution_inputs(self):
        try:
            user_task_inputs = [{k: input[k] for k in
                                 ("input_name", "description_for_system", "type", "value")} for input in
                                self.running_user_task_execution.json_input_values if input["value"]]

            if len(user_task_inputs) == 0:
                user_task_inputs = None

            return user_task_inputs
        except Exception as e:
            raise Exception(f"_get_running_user_task_execution_inputs :: {e}")
        
    @property
    def requires_vision_llm(self):
        try:
            if not self.running_user_task_execution:
                return False
            for input in self.running_user_task_execution.json_input_values:
                if input["type"] == "image":
                    return True
                if input["type"] == "multiple_images":
                    return True
            return False
        except Exception as e:
            raise Exception(f"requires_vision_llm :: {e}")


    def _get_input_images_names(self):
        try:
            input_images = []
            for task_input in self.running_user_task_execution.json_input_values:
                if task_input["type"] == "image":
                    input_images.append(task_input["value"])
                elif task_input["type"] == "multiple_images":
                    input_images += task_input["value"]
            return input_images
        except Exception as e:
            raise Exception(f"_get_input_images_paths :: {e}")


    # if requires_vision_llm, override method _generate_message_from_prompt
    def _generate_message_from_prompt(self, prompt, user_task_execution_pk=None, task_name_for_system=None):
        try:
            if not self.requires_vision_llm:
                return super()._generate_message_from_prompt(prompt, user_task_execution_pk=self.running_user_task_execution.user_task_execution_pk if self.running_user_task_execution else None,
                                                             task_name_for_system=self.running_task.name_for_system if self.running_task else None)

            from models.user_images_file_manager import UserImagesFileManager
            self.user_image_file_manager = UserImagesFileManager()
            conversation_list = self.context.state.get_conversation_as_list(self.context.session_id)
            input_images = self._get_input_images_names()
            print(f"🟠 input_images: {input_images}")
            user_id = self.context.user_id
            session_id = self.context.state.running_user_task_execution.session_id
            initial_system_message_data = [VisionMessagesData(role="system", text=prompt, images_path=[self.user_image_file_manager.get_image_file_path(image, user_id, session_id) for image in input_images])]
            conversation_messages_data = [VisionMessagesData(role=message["role"], text=message["content"], images_path=[]) for message in conversation_list]
            messages_data = initial_system_message_data + conversation_messages_data
            responses = model_loader.main_vision_llm.invoke(messages_data, self.context.user_id,
                                                        temperature=0,
                                                        max_tokens=4000,
                                                        label="CHAT",
                                                        stream=True, stream_callback=self._token_callback)
            return responses[0].strip() if responses else None
        except Exception as e:
            raise Exception(f"_generate_message_from_prompt:: {e}")

    def _token_callback(self, partial_text):
        partial_text = partial_text.strip()
        if not partial_text.lower().startswith("<"):
           self._stream_no_tag_text(partial_text)
        else:
            self._stream_task_tokens(partial_text)

    def _stream_no_tag_text(self, partial_text):
        if self.mojo_message_token_stream_callback:
            self.mojo_message_token_stream_callback(partial_text)

    @abstractmethod
    def _stream_task_tokens(self, partial_text):
        raise NotImplementedError