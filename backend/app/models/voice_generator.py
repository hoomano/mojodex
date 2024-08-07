import os
import json
import re

from azure.cognitiveservices.speech import SpeechConfig, SpeechSynthesizer
from azure.cognitiveservices.speech.audio import AudioOutputConfig

from mojodex_core.logging_handler import log_error

from mojodex_core.llm_engine.mpt import MPT

# TODO: should be a mojodex_core service?
class VoiceGenerator:
    get_language_mpt_filename = "instructions/get_language.mpt"

    # masculine voices
    available_voices_file = "mojodex_core/speech_synthesizer_available_voices.json"
    selected_voices = {'en': "en-US-RogerNeural", 'fr': "fr-FR-AlainNeural"}

    emojis_list = re.compile("["
                      u"\U00002700-\U000027BF"  # Dingbats
                      u"\U0001F600-\U0001F64F"  # Emoticons
                      u"\U00002600-\U000026FF"  # Miscellaneous Symbols
                      u"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols And Pictographs
                      u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                      u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                      u"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
                      "]+", re.UNICODE)

    def __init__(self):
        try:
            if os.environ.get("SPEECH_KEY") is None:
                raise Exception("SPEECH_KEY is not defined")
            if os.environ.get("SPEECH_REGION") is None:
                raise Exception("SPEECH_REGION is not defined")
            self.speech_config = SpeechConfig(subscription=os.environ["SPEECH_KEY"], region=os.environ["SPEECH_REGION"])
        except Exception as e:
            raise Exception(f"VoiceGenerator: {e}")


    def _get_language(self, text, user_id, user_task_execution_pk, task_name_for_system):
        try:
            get_language_mpt = MPT(VoiceGenerator.get_language_mpt_filename, text=text)

            response = get_language_mpt.run(user_id=user_id, temperature=0, max_tokens=10,
                                                             user_task_execution_pk=user_task_execution_pk,
                                                             task_name_for_system=task_name_for_system)
            return response.strip().lower()
        except Exception as e:
            raise Exception(f"_get_language: {e}")



    def text_to_speech(self, text, language_code, user_id, output_filename, user_task_execution_pk=None, task_name_for_system=None):
        try:
            if language_code is None:
                # Note: this is a patch: language code should not be None, we need to find in which case this happens
                language_code = self._get_language(text, user_id, user_task_execution_pk=user_task_execution_pk, task_name_for_system=task_name_for_system)
                log_error(f"VoiceGenerator :: text_to_speech :: language_code is None - user_id: {user_id}")
            self.speech_config.speech_synthesis_language = language_code
            # For en and fr we selected the voice we wanted, for other language, let's take the first male voice available
            if language_code in VoiceGenerator.selected_voices:
                self.speech_config.speech_synthesis_voice_name = VoiceGenerator.selected_voices[language_code]
            else:
                with open(VoiceGenerator.available_voices_file, 'r') as f:
                    available_voices = json.load(f)
                voice = next(
                    (v for v in available_voices if
                     v['Locale'].startswith(f'{language_code}-') and v['Gender'] == 'Male'), None)
                self.speech_config.speech_synthesis_voice_name = voice['ShortName']
            synthesizer = SpeechSynthesizer(speech_config=self.speech_config, audio_config=AudioOutputConfig(filename=output_filename))
            text = re.sub(VoiceGenerator.emojis_list, '', text)
            text=text.replace('*', '')
            synthesizer.speak_text(text)
        except Exception as e:
            raise Exception(f"Error generating voice with language_code: {language_code}: {e}")
