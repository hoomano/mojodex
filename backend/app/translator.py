
from mojodex_core.llm_engine.mpt import MPT


class Translator:
    translation_prompt = "instructions/translation.mpt"

    def translate(self, text, user_id, language="english"):
        try:
            translate_mpt = MPT(Translator.translation_prompt,
                                text=text, language=language)
            responses = translate_mpt.run(
                user_id=user_id, temperature=0, max_tokens=4000)
            return responses[0]
        except Exception as e:
            raise Exception(f"Translator :: translate :: {e}")
