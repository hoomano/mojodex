import os
from mojodex_core.db import db_session
from mojodex_core.entities import MdUserVocabulary
from mojodex_core.costs_manager.whisper_costs_manager import WhisperCostsManager


from openai import OpenAI, AzureOpenAI
import tiktoken

from pydub import AudioSegment
from mojodex_core.logging_handler import  log_error

whisper_costs_manager = WhisperCostsManager()

class OpenAISTT:
    
    dataset_dir = "/data/prompts_dataset"

    def __init__(self, stt_conf, label='openai_stt'):
        try:
            api_key = stt_conf["api_key"]
            api_base = stt_conf["api_base"]
            api_version = stt_conf["api_version"]
            api_type = stt_conf["api_type"]
            model = stt_conf["deployment_id"]
            self.label = label
            # if dataset_dir does not exist, create it
            if not os.path.exists(self.dataset_dir):
                os.mkdir(self.dataset_dir)
            if not os.path.exists(os.path.join(self.dataset_dir, "chat")):
                os.mkdir(os.path.join(self.dataset_dir, "chat"))
            if not os.path.exists(os.path.join(self.dataset_dir, "chat", self.label)):
                os.mkdir(os.path.join(self.dataset_dir, "chat", self.label))

            self.model = model
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=self.model,
                api_key=api_key,
            ) if api_type == 'azure' else OpenAI(api_key=api_key)

            self.label = label
            self.model = model
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=self.model,
                api_key=api_key,
            ) if api_type == 'azure' else OpenAI(api_key=api_key)
        except Exception as e:
            log_error(f"Error in OpenAISTT __init__: {e}", notify_admin=False)


    def __get_audio_file_duration(self, audio_file_path):
        try:
            audio = AudioSegment.from_file(audio_file_path)
            duration = audio.duration_seconds
            return duration
        except Exception as e:
            raise Exception(f"__get_audio_file_duration:  {e}")


    def __get_user_vocabulary(self, user_id):
        try:
            user_vocabulary = db_session.session.query(MdUserVocabulary).filter(MdUserVocabulary.user_id == user_id).order_by(
                MdUserVocabulary.creation_date.desc()).limit(100).all()
            return ", ".join([v.word for v in user_vocabulary]) if user_vocabulary else ""
        except Exception as e:
            raise Exception(f"__get_user_vocabulary:  {e}")


    # calculate the number of tokens in a given string
    def _num_tokens_from_string(self, string):
        # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.get_encoding("p50k_base")
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def transcript(self, audio_file_path, user_id, user_task_execution_pk=None, task_name_for_system=None):
        file_duration = self.__get_audio_file_duration(audio_file_path)

        audio_file = open(audio_file_path, "rb")
        try:
            vocab = self.__get_user_vocabulary(user_id)
            # check size of vocab tokens
            n_tokens_vocab = self._num_tokens_from_string(vocab)
            if n_tokens_vocab > 244: # from whisper doc: https://platform.openai.com/docs/guides/speech-to-text/prompting
                raise Exception(f"vocab too long: {n_tokens_vocab} tokens")
        except Exception as e:
            log_error(f"Error in OpenAISTT transcript: __get_user_vocabulary: user_id {user_id} - {e} ", notify_admin=True)
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

