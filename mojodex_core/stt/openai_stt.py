from mojodex_core.costs_manager.whisper_costs_manager import WhisperCostsManager
from openai import OpenAI, AzureOpenAI
import tiktoken
from mojodex_core.db import with_db_session
from mojodex_core.entities.db_base_entities import MdUserVocabulary
from mojodex_core.logging_handler import log_error
from mojodex_core.stt.stt_engine import SttEngine
from pydub import AudioSegment

from mojodex_core.user_storage_manager.user_audio_file_manager import UserAudioFileManager
import os

whisper_costs_manager = WhisperCostsManager()

class OpenAISTT(SttEngine):

    def __init__(self, model, api_key, api_type, api_base=None, api_version=None, deployment_id=None):
        try:
            self.model = model
            self.client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=api_base,
                azure_deployment=deployment_id,
                api_key=api_key,
            ) if api_type == 'azure' else OpenAI(api_key=api_key)
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: __init__: {e}")

    @with_db_session
    def __get_user_vocabulary(self, user_id, db_session):
        try:
            user_vocabulary = db_session.query(MdUserVocabulary).filter(MdUserVocabulary.user_id == user_id).order_by(
                MdUserVocabulary.creation_date.desc()).limit(50).all()
            return ", ".join([v.word for v in user_vocabulary]) if user_vocabulary else ""
        except Exception as e:
            raise Exception(f"__get_user_vocabulary:  {e}")
        
    # calculate the number of tokens in a given string
    def _num_tokens_from_string(self, string):
        try:
            # https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
            """Returns the number of tokens in a text string."""
            encoding = tiktoken.get_encoding("p50k_base")
            num_tokens = len(encoding.encode(string))
            return num_tokens
        except Exception as e:
            raise Exception(f"_num_tokens_from_string:  {e}")

    def transcribe(self, audio_file_path, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            try:
                vocab = self.__get_user_vocabulary(user_id)
            except Exception as e:
                log_error(f"{self.__class__.__name__} : get_transcript_and_file_duraction : user_id {user_id} - {e} ", notify_admin=True)
                vocab = ""

            # check size of vocab tokens
            n_tokens_vocab = self._num_tokens_from_string(vocab)
            if n_tokens_vocab > 244: # from whisper doc: https://platform.openai.com/docs/guides/speech-to-text/prompting
                log_error(f"{self.__class__.__name__} : transcribe : user_id {user_id} vocab too long: {n_tokens_vocab} tokens ", notify_admin=True)
                vocab = ""

            audio: AudioSegment = AudioSegment.from_file(audio_file_path)
            ten_minutes_in_seconds = 10 * 60

            file_format = audio_file_path.split('.')[-1]
            file_name = audio_file_path.split('/')[-1].split('.')[0]
            audio_file_dir = os.path.dirname(audio_file_path)

            if audio.duration_seconds > ten_minutes_in_seconds:
                # split the file into 10 minutes chunks
                chunks = audio[::ten_minutes_in_seconds * 1000]
                transcriptions = []
                count = 0
                for chunk in chunks:
                    chunk_name = file_name + f"_chunk_{count}." + file_format
                    chunk_file = chunk.export(out_f=os.path.join(audio_file_dir, chunk_name), format=file_format)

                    transcription = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=chunk_file,
                        prompt=vocab
                    )
                    transcriptions.append(transcription.text)
                    count += 1
                transcription = " ".join(transcriptions)

            else:
                with open(audio_file_path, "rb") as audio_file:
                    transcription = self.client.audio.transcriptions.create(
                        model=self.model,
                        file=audio_file,
                        prompt=vocab
                    ).text
                

            whisper_costs_manager.on_seconds_counted(user_id=user_id, n_seconds=audio.duration_seconds,
                                                    user_task_execution_pk=user_task_execution_pk,
                                                    task_name_for_system=task_name_for_system, mode=self.model)
            return transcription
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: transcribe:  {e}")

