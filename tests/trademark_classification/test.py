import os
from jinja2 import Template
from openai import AzureOpenAI

trademark_name = "Doggy coats"
trademark_activities = "DoggyCoat specializes in designing and manufacturing high-quality coats and accessories for dogs, providing warmth, comfort, and style for our furry companions. Our range includes a variety of coats tailored to different breeds and sizes, ensuring every dog can enjoy protection from the elements in style."

def call_chat_gpt(messages, json_format=False, max_tokens=2000, temperature=1.0, n=1, frequency_penalty=0, presence_penalty=0):

    client = AzureOpenAI(
        api_version="2023-03-15-preview",
        azure_endpoint="https://dev-france-hoomano.openai.azure.com/",
        azure_deployment='gpt4-turbo',
        api_key="fc10e0d97eff46b3a448d5914affbf72",
    )

    completion = client.chat.completions.create(
        model='gpt4-turbo',
        messages= messages,
        response_format={"type": "json_object"} if json_format else None,
       max_tokens=max_tokens, temperature=temperature #n=n, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty
    )
    return completion.choices[0].message.content

classes_separator = "\n\n"
class_keywords_separator = "\n"
keywords_separator = "; "
with open("./prompt.txt", "r") as f:
    prompt = Template(f.read()).render(trademark_name=trademark_name, trademark_activities=trademark_activities,
                                       classes_separator=classes_separator, class_keywords_separator=class_keywords_separator,
                                       keywords_separator=keywords_separator)

response = call_chat_gpt([{"role": 'user', 'content': prompt}],
                         max_tokens=2000, temperature=0, n=1, frequency_penalty=0, presence_penalty=0)
print(response)


classes = response.split(classes_separator)
# create a list containing [{"class_number": X, 'keywords': [keyword1, keyword2, ...]}, ...]
classes_list = []
for class_ in classes:
    class_number, keywords = class_.split(class_keywords_separator, 1)
    classes_list.append({"class_number": class_number, 'keywords': keywords.split(keywords_separator)})
print(classes_list)
