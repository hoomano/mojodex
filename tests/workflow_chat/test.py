import json
import os
from jinja2 import Template
from openai import AzureOpenAI


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


with open("./prompt.txt", "r") as f:
    prompt = f.read()

# load conversation.json
with open("/data/conversation.json", "r") as f:
    conversation = json.load(f)

response = call_chat_gpt([{"role": 'system', 'content': prompt}] + conversation,
                         max_tokens=4000, temperature=0)
print(response)

