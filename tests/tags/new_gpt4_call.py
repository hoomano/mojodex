import os
from jinja2 import Template
from openai import AzureOpenAI
import json

ask_user_input_start_tag, ask_user_input_end_tag = "<ask_user_primary_info>", "</ask_user_primary_info>"
execution_start_tag, execution_end_tag = "<execute>", "</execute>"
title_start_tag, title_end_tag = "<title>", "</title>"
draft_start_tag, draft_end_tag = "<draft>", "</draft>"


def extract_text(text, start_tag, end_tag):
    return text.split(start_tag)[1].split(end_tag)[0].strip() if start_tag in text else ""

def call_chat_gpt(messages, stream=False, json_format=False, max_tokens=2000, temperature=1.0, n=1, frequency_penalty=0, presence_penalty=0):

    client = AzureOpenAI(
        api_version="2023-03-15-preview",
        azure_endpoint="https://dev-france-hoomano.openai.azure.com/",
        azure_deployment='gpt4-turbo',
        api_key="fc10e0d97eff46b3a448d5914affbf72",
    )

    completion = client.chat.completions.create(
        model='gpt4-turbo',
        messages= messages,
        stream=stream,
        response_format={"type": "json_object"} if json_format else None,
       max_tokens=max_tokens, temperature=temperature #n=n, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty
    )
    if stream:
        complete_text_with_tags, complete_mojo_message = "", ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                # remove all tags from the response
               
                content = chunk.choices[0].delta.content
                complete_text_with_tags += content
                print(f"🟠 complete_text: {complete_text_with_tags}")
                
                try:
                    if execution_start_tag in complete_text_with_tags:
                        mojo_message = extract_text(complete_text_with_tags, execution_start_tag, execution_end_tag)
                    elif ask_user_input_start_tag in complete_text_with_tags:
                        mojo_message = extract_text(complete_text_with_tags, ask_user_input_start_tag, ask_user_input_end_tag)
                    else:
                        mojo_message = ""
                    
                    if "<" in mojo_message:
                        mojo_message = mojo_message.split("<")[0]
                    # difference between complete_mojo_message and mojo_message
                    mojo_message_diff = complete_mojo_message.replace(mojo_message, "")
                    print(f"🟢 mojo_message_diff: {mojo_message_diff}")
                    
                    complete_mojo_message = mojo_message
                   
                except Exception as e:
                    print(e)
        


with open("./run_task.txt", "r") as f:
    prompt = f.read()

call_chat_gpt([{"role": 'user', 'content': prompt}], stream=True,
                         max_tokens=1000, temperature=0.5, n=1, frequency_penalty=0, presence_penalty=0)

