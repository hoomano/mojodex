import base64
import json
import os
from openai import AzureOpenAI, OpenAI
os.environ["OPENAI_LOG"] = "debug"


def call_chat_gpt(messages, max_tokens=2000, temperature=1.0):

    client = AzureOpenAI(
        api_version="2024-02-01",
        azure_endpoint="https://dev-westus-hoomano.openai.azure.com/",
       azure_deployment='gpt4-vision',
        api_key="0395d43389544e0bb98efa44868f6c34",
    )

    #client = OpenAI(api_key="sk-mojodex-dev-account-ADrxmJZFIYbtv3u5U56PT3BlbkFJYmpOyEyLuxz8qwRf9uae")

    completion = client.chat.completions.create(
        #model='gpt-4-vision-preview',
        model='gpt4-vision',
        messages= messages,
       max_tokens=max_tokens, temperature=temperature,
       stream=False
    )
    return completion.choices[0].message.content

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

with open("./extract_annotations.txt", "r") as f:
    prompt = f.read()

messages = [
                        {"role": 'user', 'content': [
                                {"type": "text", "text": prompt},
                                {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{encode_image('./patent_figure.png')}"
                                     }
                                }
                        ]},
                        ]


response = call_chat_gpt(messages, max_tokens=4000, temperature=0)
print(response)
# split by line
#annotations = [a.strip() for a in response.split("\n") if a not in ["CORRECT ANNOTATIONS", "MISSING ANNOTATIONS"]]
#print(annotations)

