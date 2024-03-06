import json
import logging
import os
import time

import openai
from pydub import AudioSegment
from mojodex_core.logging_handler import  log_error
from mojodex_core.db import db_session
from mojodex_core.entities import MdUserVocabulary

from llm_api.backend_llm import BackendLLM
from mojodex_core.llm_engine.providers.openai_llm import OpenAILLM

from mojodex_core.costs_manager.tokens_costs_manager import TokensCostsManager
from mojodex_core.llm_engine.providers.openai_embedding import OpenAIEmbeddingProvider
from mojodex_core.costs_manager.whisper_costs_manager import WhisperCostsManager

tokens_costs_manager = TokensCostsManager()
whisper_costs_manager = WhisperCostsManager()

class OpenAIConf:

    gpt4_32_conf = {
        "api_key": os.environ.get("GPT4_AZURE_OPENAI_KEY", os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("GPT4_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("BACKUP_MODEL_API_TYPE"),
        "api_version": os.environ.get("GPT4_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("GPT4_AZURE_OPENAI_DEPLOYMENT_ID", 'gpt-4-32k')
    } if 'BACKUP_MODEL_API_TYPE' in os.environ and 'GPT4_AZURE_OPENAI_KEY' in os.environ else None

    gpt4_turbo_conf = {
        "api_key": os.environ.get("GPT4_TURBO_AZURE_OPENAI_KEY",  os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("LLM_API_PROVIDER"),
        "api_version": os.environ.get("GPT4_TURBO_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("GPT4_TURBO_AZURE_OPENAI_DEPLOYMENT_ID", 'gpt-4-1106-preview')
    }

    conf_embedding = {
        "api_key": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_KEY", os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("EMBEDDING_API_PROVIDER"),
        "api_version": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_API_VERSION"),
        "deployment_id": os.environ.get("ADA_EMBEDDING_AZURE_OPENAI_DEPLOYMENT_ID", "text-embedding-ada-002")
    }

    whisper_conf = {
        "api_key": os.environ.get("WHISPER_AZURE_OPENAI_KEY",  os.environ.get("OPENAI_API_KEY")),
        "api_base": os.environ.get("WHISPER_AZURE_OPENAI_API_BASE"),
        "api_type": os.environ.get("STT_API_PROVIDER"),
        "api_version": os.environ.get("WHISPER_AZURE_VERSION"),
        "deployment_id": os.environ.get("WHISPER_AZURE_OPENAI_DEPLOYMENT_ID", "whisper-1")
    }



class MojodexBackendOpenAI(BackendLLM, OpenAILLM, OpenAIEmbeddingProvider):
    dataset_dir = "/data/prompts_dataset"

    def __init__(self, azure_conf, label='unknown', llm_backup_conf=None, max_retries=0):
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
        BackendLLM.__init__(self, azure_conf, llm_backup_conf=llm_backup_conf, label=label, max_retries=max_retries)
        OpenAILLM.__init__(self, api_key, api_base, api_version, model, api_type=api_type, max_retries=max_retries)

        if llm_backup_conf:
            self.backup_engine = OpenAILLM(llm_backup_conf["api_key"],
                                            llm_backup_conf["api_base"],
                                            llm_backup_conf["api_version"],
                                            llm_backup_conf["deployment_id"],
                                            api_type=api_type, max_retries=2)
        else:
            self.backup_engine = None


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
                responses = super().chatCompletion(messages, user_id, temperature, max_tokens,
                                                         frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
                                                         json_format=json_format, stream=stream,
                                                         stream_callback=stream_callback, n_additional_calls_if_finish_reason_is_length=n_additional_calls_if_finish_reason_is_length)
            except openai.RateLimitError:
                # try to use backup engine
                if self.backup_engine:
                    responses = self.backup_engine.chatCompletion(messages, user_id, temperature, max_tokens,
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
            self._write_in_dataset({"temperature": temperature, "max_tokens": max_tokens, "n_responses": 1,
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
            responses = super().get_embedding(text)
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
            user_vocabulary = db_session.query(MdUserVocabulary).filter(MdUserVocabulary.user_id == user_id).order_by(
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

