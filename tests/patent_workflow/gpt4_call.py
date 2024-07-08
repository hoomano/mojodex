import openai
import os

from openai import AzureOpenAI
from jinja2 import Template
os.environ['AZURE_OPENAI_KEY'] = "8c2b58a2776f4cb9908c9ff0f45f7f25"

def call_chat_gpt(messages, json_format=False, max_tokens=2000, temperature=1.0, n=1, frequency_penalty=0, presence_penalty=0):

    client = AzureOpenAI(
        api_version="2023-03-15-preview",
        azure_endpoint="https://dev-france-hoomano.openai.azure.com/",
        azure_deployment='gpt4-turbo',
        api_key="dafa4ead5b194314b5c9b7ddf0a8dd49",
    )

    completion = client.chat.completions.create(
        model='gpt4-turbo',
        messages= messages,
        response_format={"type": "json_object"} if json_format else None,
       max_tokens=max_tokens, temperature=temperature #n=n, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty
    )
    return completion.choices[0].message.content

with open("../patent_translation/patents/EP3301617B1.txt", 'r') as f2:
    patent = f2.read()


def extract_sections_names():
    with open("sections_names.txt", "r") as f:
        prompt = Template(f.read()).render(text=patent)
    messages = [{"role": 'user', 'content': prompt}]
    response = call_chat_gpt(messages,
                             max_tokens=4000, temperature=0, n=1, frequency_penalty=0, presence_penalty=0)
    return response.split("\n")

sections_names = ['DOMAINE TECHNIQUE GENERAL', 'ETAT DE L’ART', 'PRESENTATION DE L’INVENTION', 'DESCRIPTION DETAILLEE', 'Architecture', 'Procédé d’apprentissage sécurisé', 'Procédé de classification sécurisée - première variante', 'Procédé de classification sécurisée - deuxième variante', 'Produit programme d’ordinateur', 'PRESENTATION DES FIGURES', 'Revendications', 'RÉFÉRENCES CITÉES DANS LA DESCRIPTION']

def get_section_text(text, section_name):
    # text after the section name
    return text[:text.find(section_name)]

def extrapolate_not_found_section_name(section_name, text):
    # remove 1 last word from the section_name until found in the text. Useful if section_name is on multiple lines
    words = section_name.split()
    if len(words) == 1:
        return None
    section_name = " ".join(words[:-1])
    n = text.count(section_name)
    if n == 1:
        return section_name
    elif n > 1:
        return None
    else:
        return extrapolate_not_found_section_name(section_name, text)

def extrapolate_multiple_found_section_name(section_name, text):
    # try to add a \n after the section_name
    section_name = section_name + "\n"
    n = text.count(section_name)
    if n == 1:
        return section_name
    else:
        return None


def _validate_section(text, section_name):
    occurrences = text.count(section_name)
    if occurrences == 1:
        return section_name
    elif occurrences > 1:
        return extrapolate_multiple_found_section_name(section_name, text)
    elif occurrences == 0:
        return extrapolate_not_found_section_name(section_name, text)

def validate_sections():
    validated_sections = []
    stripped_sections_names = [section.strip() for section in sections_names if section.strip() != ""]
    # For each section, check if the section title can be found in the patent text
    for section in stripped_sections_names:
        validated_section = _validate_section(patent, section)
        if validated_section:
            #print(f"Section {validated_section} found in patent text")
            validated_sections.append({'name': validated_section, 'appearance': patent.find(validated_section)})
        else:
            pass
            #print(f"Section {section} not found in patent text")
    # order validated_sections by their order of appearance in the patent text
    validated_sections = sorted(validated_sections, key=lambda x: x['appearance'])
    # return the list of validated sections names
    return [section['name'] for section in validated_sections]

sections = validate_sections()
print(len(sections))

def get_sections_text():
    sections_text = []
    remaining_patent = patent
    for section_name in sections:
        sections_text.append(get_section_text(remaining_patent, section_name))
        remaining_patent = remaining_patent[remaining_patent.find(section_name):]
        print(f"👉 remaining patent size: {len(remaining_patent)}")
    sections_text.append(remaining_patent)
    return sections_text

sections_text = get_sections_text()
print(len(sections_text))



