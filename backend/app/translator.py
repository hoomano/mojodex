from jinja2 import Template

from mojodex_backend_openai import MojodexBackendOpenAI

from azure_openai_conf import AzureOpenAIConf


class Translator:
    translation_prompt = "/data/prompts/resources/translation.txt"

    translator = MojodexBackendOpenAI(AzureOpenAIConf.azure_gpt4_turbo_conf, "GET_LANGUAGE",
                               AzureOpenAIConf.azure_gpt4_32_conf)

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
