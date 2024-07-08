import os
from jinja2 import Template
from openai import AzureOpenAI

trademark_name = "Doggy coats"
trademark_activities = "DoggyCoat specializes in designing and manufacturing high-quality coats and accessories for dogs, providing warmth, comfort, and style for our furry companions. Our range includes a variety of coats tailored to different breeds and sizes, ensuring every dog can enjoy protection from the elements in style."
draft_classification={"18": ["Harnesses for animals", "Harness for animals", "Leather straps", "Dog apparel", "Clothing for dogs", "Leather cord", "Animal leads", "Leather for harnesses", "Capes for pets", "Leather laces", "Collars for pets", "Collars of animals", "Leather leads", "Clothes for animals", "Dog leads", "Coats for dogs", "Leashes for pets", "Fittings (Harness -)", "Dog waste bag dispensers adapted for use with leashes", "Dog leashes", "Leashes (Leather -)", "Harness", "Coats for cats", "Animal harnesses", "Collars for cats", "Animal carriers [bags]", "Hats for pets", "Leads for animals", "Garments for pets", "Leather cords", "Dog coats", "Harness fittings", "Pets (Clothing for -)", "Cat collars", "Clothing for domestic pets", "Animal leashes", "Clothing for pets", "Straps (Leather -)", "Pet clothing", "Animal apparel", "Pet leads", "Leather leashes", "Dog bellybands", "Clothing for animals", "Collars for animals", "Leather thongs", 
                            "Harnesses", "Costumes for animals", "Leather", "Dog collars", "Waterproof bags", "Dog shoes", "Dog clothing", "Leashes for animals"],
                      "25": ["Water-resistant clothing", "Caps [headwear]", "Furs [clothing]", "Waterproof pants", "Footwear for sport", "Knitwear [clothing]", "Head wear", "Waterproof clothing", "Waterproof outerclothing", "Knitwear", "Fishing headwear", "Gloves for apparel", "Collars", "Coats", "Footwear for sports", "Rainproof clothing", "Footwear", "Sports footwear", "Leather headwear", "Caps being headwear", "Infants' footwear", "Clothing", "Weatherproof clothing", "Heelpieces for footwear", "Headwear", "Down coats", "Children's footwear", "Children's headwear", "Collars [clothing]", "Waterproof shoes"],
                      "35": ["Online retail store services relating to cosmetic and beauty products", "Online retail store services in relation to clothing", "Retail services in relation to bedding for animals", "Mail order retail services connected with clothing accessories", "Online retail services relating to clothing", "Retail services relating to automobile accessories", "Mail order retail services for clothing accessories", "Online retail store services relating to clothing", "Retail services in relation to pet products", "Retail services connected with the sale of clothing and clothing accessories", "Retail services in relation to fashion accessories", "Retail store services in the field of clothing", "Retail services in relation to clothing accessories"]}


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

def _get_classification_as_formatted_string(classes_dict: list):
    return classes_separator.join([f"""Class {class_number}{class_keywords_separator}{keywords_separator.join(keywords)}""" for class_number, keywords in classes_dict.items()])
    
with open("./refine_prompt.txt", "r") as f:
    prompt = Template(f.read()).render(trademark_name=trademark_name, trademark_activities=trademark_activities,
                                       draft_classification=_get_classification_as_formatted_string(draft_classification) )

response = call_chat_gpt([{"role": 'user', 'content': prompt}],
                         max_tokens=2000, temperature=0, n=1, frequency_penalty=0, presence_penalty=0)
print(response)