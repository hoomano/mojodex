import json
from jinja2 import Template
from openai import AzureOpenAI
import os
os.environ['AZURE_OPENAI_KEY'] = "8c2b58a2776f4cb9908c9ff0f45f7f25"
SERPAPI_KEY = "5013a5702ef019ea7ca4ba87899c0965df4eeeb17c50871d8574053308fcf46f"

client = AzureOpenAI(
    api_version="2023-03-15-preview",
    azure_endpoint="https://dev-france-hoomano.openai.azure.com/",
    azure_deployment='gpt4-turbo',
    api_key="dafa4ead5b194314b5c9b7ddf0a8dd49",
)

def call_chat_gpt(messages, json_format=False, max_tokens=4000, temperature=1.0, n=1, frequency_penalty=0, presence_penalty=0, streamcallback=None):
    completion = client.chat.completions.create(
        model='gpt4-turbo',
        messages= messages,
        response_format={"type": "json_object"} if json_format else None,
        max_tokens=max_tokens, temperature=temperature,
        n=n, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
        stream= streamcallback is not None
    )
    if streamcallback:
        complete_text = ""
        for token in completion:
            choice = token.choices[0]
            partial_token = choice.delta
            if partial_token.content:
                complete_text += partial_token.content
                streamcallback(complete_text)
        return complete_text
    return completion.choices[0].message.content



achieved_steps = []
current_step = {'name': 'query_writer',
                'description': 'Write the query to search for the company industry.',
                'current_run':{'parameter': {'company_name': 'Hoomano'},
                'result': [{'query': 'Hoomano industry', 'gl': 'US', 'hl': 'en'}]
                }
                }

with open('prompts/initial_system.txt', 'r') as f:
    template = Template(f.read())
    initial_prompt = template.render()

with open('prompts/state_system.txt', 'r') as f:
    template = Template(f.read())
    state_prompt = template.render(steps_executions=achieved_steps,
                                   current_step=current_step)

   
messages = [{'role': 'system', 'content': initial_prompt },
            {'role': 'system', 'content': state_prompt }]

n_files = len(os.listdir("messages/"))
for file_index in range(n_files//2):
    user = open(f"messages/user_{file_index}.txt", "r").read()
    answer = open(f"messages/mojo_{file_index}.txt", "r").read()
    messages.append({"role": 'assistant', 'content': answer})
    messages.append({"role": 'user', 'content': user})

response = call_chat_gpt(messages, json_format=False, max_tokens=4000, temperature=1.0, n=1, frequency_penalty=0, presence_penalty=0)
print(response)

# write to messages/assistant/{n_files_in_folder}.json
n_files_in_folder = len(os.listdir('messages'))
with open(f'messages/{n_files_in_folder}.txt', 'w') as f:
    f.write(response)