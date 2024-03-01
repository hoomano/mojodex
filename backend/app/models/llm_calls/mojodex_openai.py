import json
import logging
import os
import time

import openai
from pydub import AudioSegment
from app import tokens_costs_manager, whisper_costs_manager, log_error, db
from db_models import MdUserVocabulary

from models.llm_calls.mojo_openai import MojoOpenAI


class MojodexOpenAI(MojoOpenAI):
    dataset_dir = "/data/prompts_dataset"

    def __init__(self, azure_conf, label, azure_conf_backup_rate_limit_exceeded=None, max_retries=0):
        api_key = azure_conf["api_key"]
        api_base = azure_conf["api_base"]
        api_version = azure_conf["api_version"]
        api_type = azure_conf["api_type"]
        model = azure_conf["deployment_id"]
        self.label = label
        # if dataset_dir does not exist, create it
        if not os.path.exists(self.dataset_dir):
            os.mkdir(self.dataset_dir)
        if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
            os.mkdir(os.path.join(self.dataset_dir, "chat"))
        if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
            os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))
        super().__init__(api_key, api_base, api_version, model, api_type=api_type, max_retries=max_retries)
        if azure_conf_backup_rate_limit_exceeded:
            self.backup_engine = MojoOpenAI(azure_conf_backup_rate_limit_exceeded["api_key"],
                                            azure_conf_backup_rate_limit_exceeded["api_base"],
                                            azure_conf_backup_rate_limit_exceeded["api_version"],
                                            azure_conf_backup_rate_limit_exceeded["deployment_id"],
                                            api_type=api_type, max_retries=2)
        else:
            self.backup_engine = None


    def __write_in_dataset(self, json_data, task_name_for_system, type):
        try:
            # write data in MojodexOpenAI.dataset_dir/label/task_name_for_system.json
            directory = f"{self.dataset_dir}/{type}/{self.label}/{task_name_for_system}"
            if not os.path.exists(directory):
                os.mkdir(directory)
            filename = len(os.listdir(directory)) + 1
            with open(os.path.join(directory, f"{filename}.json"), "w") as f:
                json.dump(json_data, f)
        except Exception as e:
            log_error(f"Error in Mojodex OpenAI __write_in_dataset: {e}", notify_admin=True)

    def chat(self, messages, user_id, temperature, max_tokens,
                frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
                user_task_execution_pk=None, task_name_for_system=None):
        return self.recursive_chat(messages, user_id, temperature, max_tokens,
                                    frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                    stream=stream, stream_callback=stream_callback, json_format=json_format,
                                    user_task_execution_pk=user_task_execution_pk,
                                    task_name_for_system=task_name_for_system,
                                    n_additional_calls_if_finish_reason_is_length=0)

    def recursive_chat(self, messages, user_id, temperature, max_tokens,
             frequency_penalty=0, presence_penalty=0, stream=False, stream_callback=None, json_format=False,
             user_task_execution_pk=None, task_name_for_system=None, n_additional_calls_if_finish_reason_is_length=0):
        try:

            # check complete number of tokens in prompt
            n_tokens_prompt = self.num_tokens_from_messages(messages[:1])
            n_tokens_conversation = self.num_tokens_from_messages(messages[1:])

            try:
                responses = super().openAIChatCompletion(messages, user_id, temperature, max_tokens,
                                                         frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                                         json_format=json_format, stream=stream,
                                                         stream_callback=stream_callback, n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length)
            except openai.RateLimitError:
                # try to use backup engine
                if self.backup_engine:
                    responses = self.backup_engine.openAIChatCompletion(messages, user_id, temperature, max_tokens,
                                                         frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                                         stream=stream,
                                                         stream_callback=stream_callback)
                else:
                    raise Exception("Rate limit exceeded and no backup engine available")
            n_tokens_response = 0
            for response in responses:
                n_tokens_response += self.num_tokens_from_messages([{'role': 'assistant', 'content': response}])

            tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, n_tokens_conversation, n_tokens_response,
                                                   self.model, self.label, user_task_execution_pk, task_name_for_system)
            self.__write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
                                        "frequency_penalty": frequency_penalty, "presence_penalty": presence_penalty,
                                        "messages": messages, "responses": responses}, task_name_for_system, "chat")
            return responses
        except Exception as e:
            log_error(f"Error in Mojodex OpenAI chat for user_id: {user_id} - user_task_execution_pk: {user_task_execution_pk} - task_name_for_system: {task_name_for_system}: {e}", notify_admin=True)
            raise Exception(f"🔴 Error in Mojodex OpenAI chat: {e} - model: {self.model}")


    def embed(self, text, user_id, user_task_execution_pk, task_name_for_system, retries=5):
        try:
            try:
                n_tokens_prompt = self.num_tokens_from_string(text)
            except Exception as e:
                n_tokens_prompt = 0
            responses = super().openAIEmbedding(text)
            tokens_costs_manager.on_tokens_counted(user_id, n_tokens_prompt, 0, 0,
                                                   self.model, self.label, user_task_execution_pk, task_name_for_system)
            return responses
        except openai.RateLimitError as e:
            # wait for 2 seconds and retry, it's embed so not urgent
            if retries==0:
                raise Exception(f"🔴 Error in Mojodex OpenAI embed, rate limit exceeded despite all retries: {e}")
            time.sleep(2)
            return self.embed(text, user_id, user_task_execution_pk, task_name_for_system, retries=retries-1)
        except Exception as e:
            raise Exception(f"🔴 Error in Mojodex OpenAI embed: {e}")

    def __get_audio_file_duration(self, audio_file_path):
        try:
            audio = AudioSegment.from_file(audio_file_path)
            duration = audio.duration_seconds
            return duration
        except Exception as e:
            raise Exception(f"__get_audio_file_duration:  {e}")


    def __get_user_vocabulary(self, user_id):
        try:
            user_vocabulary = db.session.query(MdUserVocabulary).filter(MdUserVocabulary.user_id == user_id).order_by(
                MdUserVocabulary.creation_date.desc()).limit(100).all()
            return ", ".join([v.word for v in user_vocabulary]) if user_vocabulary else ""
        except Exception as e:
            raise Exception(f"__get_user_vocabulary:  {e}")


    def transcript(self, audio_file_path, user_id, user_task_execution_pk=None, task_name_for_system=None):
        file_duration = self.__get_audio_file_duration(audio_file_path)

        audio_file = open(audio_file_path, "rb")
        try:
            vocab = self.__get_user_vocabulary(user_id)
            # check size of vocab tokens
            n_tokens_vocab = self.num_tokens_from_string(vocab)
            if n_tokens_vocab > 244: # from whisper doc: https://platform.openai.com/docs/guides/speech-to-text/prompting
                raise Exception(f"vocab too long: {n_tokens_vocab} tokens")
        except Exception as e:
            log_error(f"Error in Mojodex OpenAI transcript: __get_user_vocabulary: user_id {user_id} - {e} ", notify_admin=True)
            vocab = ""

        transcription = self.client.audio.transcriptions.create(
            model=self.model,
            file=audio_file,
            prompt=vocab
        )
        transcription_text = transcription.text

        whisper_costs_manager.on_seconds_counted(user_id=user_id, n_seconds=file_duration,
                                                 user_task_execution_pk=user_task_execution_pk,
                                                 task_name_for_system=task_name_for_system, mode=self.label)
        return transcription_text, file_duration
