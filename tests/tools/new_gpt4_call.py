import os
from jinja2 import Template
from openai import AzureOpenAI
import json

def call_chat_gpt(messages, tools, stream=False, json_format=False, max_tokens=2000, temperature=1.0, n=1, frequency_penalty=0, presence_penalty=0):

    client = AzureOpenAI(
        api_version="2023-03-15-preview",
        azure_endpoint="https://dev-france-hoomano.openai.azure.com/",
        azure_deployment='gpt4-turbo',
        api_key="fc10e0d97eff46b3a448d5914affbf72",
    )

    completion = client.chat.completions.create(
        model='gpt4-turbo',
        messages= messages,
        tools=tools,
        tool_choice="auto",
        stream=stream,
        response_format={"type": "json_object"} if json_format else None,
       max_tokens=max_tokens, temperature=temperature #n=n, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty
    )
    if stream:
        complete_text = ""
        for stream_chunk in completion:
            choice = stream_chunk.choices[0]
            partial_token = choice.delta.tool_calls[0]
            if partial_token.function.arguments:
                complete_text += partial_token.function.arguments
                print(complete_text)
        

# load tools from json file tools.json
with open("./tools.json", "r") as f:
    tools = json.load(f)

with open("./new_prompt.txt", "r") as f:
    prompt = f.read()

response = call_chat_gpt([{"role": 'user', 'content': prompt}], tools, stream=True,
                         max_tokens=200, temperature=0.5, n=1, frequency_penalty=0, presence_penalty=0)

if response.content:
    print('🟢 Content not null')
    print(response.content)
else:
    print('🔴 Content is null')
    tool_calls = response.tool_calls
    for tool_call in tool_calls:
        print(tool_call.function.name)
        print(tool_call.function.arguments)