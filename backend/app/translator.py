from jinja2 import Template

from app import llm, llm_conf, llm_backup_conf

class Translator:
    translation_prompt = "/data/prompts/resources/translation.txt"

    translator = llm(llm_conf, label="GET_LANGUAGE",
                               llm_backup_conf=llm_backup_conf)

    def translate(self, text, user_id, language="english"):
        try:
            with open(Translator.translation_prompt, "r") as f:
                translate_prompt_template = Template(f.read())
                translate_prompt = translate_prompt_template.render(text=text, language=language)
            messages = [{"role": "user", "content": translate_prompt}]

            responses = Translator.translator.chat(messages, user_id, temperature=0, max_tokens=6000)
            return responses[0]
        except Exception as e:
            raise Exception(f"Translator :: translate :: {e}")
