from mojodex_core.costs_manager.whisper_costs_manager import WhisperCostsManager
from openai import OpenAI, AzureOpenAI
import tiktoken
from mojodex_core.logging_handler import log_error
from mojodex_core.stt.stt_engine import SttEngine


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

    def _transcript(self, audio_file, vocab, file_duration, user_id, user_task_execution_pk=None, task_name_for_system=None):
        try:
            # check size of vocab tokens
            n_tokens_vocab = self._num_tokens_from_string(vocab)
            if n_tokens_vocab > 244: # from whisper doc: https://platform.openai.com/docs/guides/speech-to-text/prompting
                log_error(f"{self.__class__.__name__} : _transcript : user_id {user_id} vocab too long: {n_tokens_vocab} tokens ", notify_admin=True)
                vocab = ""

            transcription = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                prompt=vocab
            )

            whisper_costs_manager.on_seconds_counted(user_id=user_id, n_seconds=file_duration,
                                                    user_task_execution_pk=user_task_execution_pk,
                                                    task_name_for_system=task_name_for_system, mode=self.model)
            return transcription.text
        except Exception as e:
            raise Exception(f"{self.__class__.__name__} :: _transcript:  {e}")

