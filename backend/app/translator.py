
from app import llm, llm_conf, llm_backup_conf
from mojodex_core.llm_engine.mpt import MPT


class Translator:
    translation_prompt = "instructions/translation.mpt"

    translator = llm(llm_conf, label="GET_LANGUAGE",
                     llm_backup_conf=llm_backup_conf)

    def translate(self, text, user_id, language="english"):
        try:
            translate_mpt = MPT(Translator.translation_prompt,
                                text=text, language=language)
            responses = Translator.translator.invoke_from_mpt(
                translate_mpt, user_id, temperature=0, max_tokens=4000)
            return responses[0]
        except Exception as e:
            raise Exception(f"Translator :: translate :: {e}")
