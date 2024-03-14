import os
from mojodex_core.stt.openai_stt import OpenAISTT

from mojodex_core.openai_conf import OpenAIConf


class STT:
    """
    Speech-to-Text (STT) class for using STT in the Mojodex system.
    """

    @staticmethod
    def get_stt():
        """
        Get the Speech-to-Text (STT) engine.

        Returns:
            The STT engine based on the environment variable STT_ENGINE.
        """
        # Setup the stt engine
        stt_engine = os.environ.get("STT_ENGINE", "whisper")
        if stt_engine == "whisper":
            return OpenAISTT, OpenAIConf.whisper_conf
