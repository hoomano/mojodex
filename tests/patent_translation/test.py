import json

import tiktoken as tiktoken
from openai import AzureOpenAI
import os
from jinja2 import Template
from serpapi import GoogleSearch
from PyPDF2 import PdfReader
import requests
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

patent_publication_number = "EP3301617B1"
#target_language = "ENGLISH" # ENGLISH, GERMAN, CHINESE, FRENCH, SPANISH, ARABIC, JAPANESE, KOREAN, PORTUGUESE, RUSSIAN, ITALIAN, DUTCH, SWEDISH, FINNISH, NORWEGIAN, DANISH
#target_office_country = "CN" # https://serpapi.com/google-patents-country-codes
cpc = "G06N3/08"

def _extract_text_from_pdf(publication_number):
    print("👉 Extracting text from PDF")
    reader = PdfReader(f'patents/{publication_number}.pdf')
    total_text = ''
    for page in reader.pages:
        total_text += page.extract_text()

    # write in patents/EP3301617B1.txt
    with open(f'patents/{publication_number}.txt', 'w') as f:
        f.write(total_text)
    print(f"👉 Text extracted from {publication_number}.pdf")
    return total_text

def _download_pdf(patent_publication_number, pdf_url):
    response = requests.get(pdf_url)
    with open(f"patents/{patent_publication_number}.pdf", "wb") as f:
        f.write(response.content)

#def extract_vocabulary(patent_publication_number, n=10):
#    # TODO: try something not using LLM call like TF-IDF
#    # open file patent_publication_number.txt
#    with open(f'patents/{patent_publication_number}.txt', 'r') as f:
#        patent = f.read()
#
#    # open prompt template
#    with open("prompts/lexical_field.txt", "r") as f:
#        template = Template(f.read())
#        prompt = template.render(n=n, patent=patent)
#
#    system_message = {'role': 'assistant', 'content': prompt}
#    response = call_chat_gpt([system_message], json_format=True, temperature=0)
#    response = json.loads(response)
#    return response['words']
#
#
#def search_similar_patents_from_lexical_field():
#    # patent_lexical_field = extract_vocabulary(patent_publication_number)
#    # print(patent_lexical_field)
#    patent_lexical_field = ['apprentissage', 'sécurisé', 'paramètres', 'réseau', 'neurones', 'convolution',
#                            'classification', 'chiffré', 'homomorphique', 'fonction']
#
#    # join all words in patent_lexical_field with ;
#    words = ";".join(patent_lexical_field)
#    search_query = f"{cpc};{words}"
#
#    params = {
#        "engine": "google_patents",
#        "q": search_query,
#        "api_key": SERPAPI_KEY
#    }
#
#    search = GoogleSearch(params)
#    results = search.get_dict()
#    return results

def search_similar_patents_from_similarity():
    params = {
        "engine": "google_patents",
        "q": f"{cpc};(~patent/{patent_publication_number})",
        "page": "1",
        #"language": target_language,
        "country": target_office_country,
        "api_key": SERPAPI_KEY
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    return results

def look_for_similar_patents_lexical_field():
    #results = search_similar_patents_from_lexical_field()
    results = search_similar_patents_from_similarity()

    for result in results['organic_results']:
        publication_number = result['publication_number']
        # ensure publication_number is != patent_publication_number
        if publication_number == patent_publication_number:
            continue

        pdf_link = result['pdf']
        _download_pdf(publication_number, pdf_link)
        extracted_text=_extract_text_from_pdf(publication_number)
        if extracted_text.strip() == '':
            continue
        try:
            targeted_vocabulary = extract_lexical_field(publication_number)
            return targeted_vocabulary
        except Exception as e:
            print(f"Error extracting lexical field: {e}")
            continue

def streamcallback(response):
    # write response in file "response.txt"
    with open("response.txt", "w") as f:
        f.write(response)


def __extract_lexical_field(patent_publication_number):
    try:
        # open file patent_publication_number.txt
        with open(f'patents/{patent_publication_number}.txt', 'r') as f:
            patent = f.read()

        # open prompt template
        with open("prompts/lexical_field.txt", "r") as f:
            template = Template(f.read())
            prompt = template.render(patent=patent)

        system_message = {'role': 'system', 'content': prompt}
        response = call_chat_gpt([system_message], temperature=0, streamcallback=streamcallback)
        # extract text between "<WORDS>" and "</WORDS>"
        text = response.split("<WORDS>")[1].split("</WORDS>")[0].strip()
        return text.split("\n")
    except Exception as e:
        raise Exception(f"Error extracting lexical field: {e}")

#targeted_vocabulary = look_for_similar_patents_lexical_field()
#print(targeted_vocabulary)
#print(len(targeted_vocabulary))
#similar_patent_publication_number = "US11295208B2"

def extract_lexical_field(patent_text):
        try:
            starting_list_tag, ending_list_tag = "<WORDS>", "</WORDS>"
            # open prompt template
            with open("prompts/lexical_field.txt", "r") as f:
                template = Template(f.read())
                prompt = template.render(patent=patent_text,
                                         starting_list_tag=starting_list_tag, ending_list_tag=ending_list_tag,
                                         max_words=100)

            # write prompt in file "/data/extract_lexical_field_prompt.txt"
            with open("extract_lexical_field_prompt.txt", "w") as f:
                f.write(prompt)
            messages = [{'role': 'user', 'content': prompt}]

            response = call_chat_gpt(messages, temperature=0, max_tokens=1000)
            # write response in file "/data/extract_lexical_field_response.txt"
            with open("extract_lexical_field_response.txt", "w") as f:
                f.write(response)
            text = response.split(starting_list_tag)[1].split(ending_list_tag)[0].strip()
            return text.split("\n")
        except Exception as e:
            raise Exception(f"Error extracting lexical field: {e}")



# dowload https://patentimages.storage.googleapis.com/ef/14/52/9f85b83180ef99/US3444866.pdf
#_download_pdf("US3444866", "https://patentimages.storage.googleapis.com/ef/14/52/9f85b83180ef99/US3444866.pdf")


#with open("patents/US3444866.txt", "r") as f:
#    patent = f.read()
#    targeted_vocabulary = extract_lexical_field(patent)

def generate_tool_params():
    with open("prompts/generate_tool_params.txt", "r") as f:
        prompt = f.read()

    messages = [{"role": "system", "content": prompt}]
    response = call_chat_gpt(messages, temperature=0, max_tokens=2000)
    return response

#response = generate_tool_params()
#print(response)

encoding = tiktoken.get_encoding("cl100k_base")




with open("patents/to_translate.txt", "r") as f:
    patent_to_translate = f.read()

with open("lexical_field.txt", "r") as f:
    targeted_vocabulary = f.read().split("\n")

def translate(patent_to_translate, targeted_vocabulary):
    with open("prompts/translate_bis.txt", "r") as f:
        template = Template(f.read())
        prompt = template.render(patent=patent_to_translate, language="english", lexical_field="\n".join(targeted_vocabulary))

    num_tokens = len(encoding.encode(prompt))
    total_tokens = num_tokens
    print(f"initial prompt num_tokens: {num_tokens}")
    with open("translate_prompt.txt", "w") as f:
        f.write(prompt)
    messages = []
    try:
        # Then, call llm as long as finish reason is length
        messages = [{"role": "system", "content": prompt}]
        finish_reason = 'length'
        translation_text = ""

        while finish_reason == 'length':
            print(f"number of messages: {len(messages)}")
            completion = client.chat.completions.create(model='gpt4-turbo', messages= messages, temperature=0)
            #print(completion.choices[0])
            #print(completion.choices[0].message.content)
            response_num_tokens = len(encoding.encode(completion.choices[0].message.content))
            print(f"num_tokens in assistant_response = {response_num_tokens}")
            total_tokens += response_num_tokens
            print(f"🟢 total_tokens = {total_tokens}")
            translation_text += completion.choices[0].message.content + " "
            finish_reason = completion.choices[0].finish_reason
            messages.append({"role": "assistant", "content": completion.choices[0].message.content})
            messages.append({"role": "user", "content": "Continue"})

        with open("messages.json", "w") as f:
            json.dump(messages, f, indent=4)

        with open("translation.txt", "w") as f:
            f.write(translation_text)
#

    except Exception as e:
        # dump messages in json file
        with open("messages.json", "w") as f:
            json.dump(messages, f, indent=4)


#patent = """Un dispositif de téléportation quantique utilisant des particules subatomiques pour le transfert instantané d'objets entre deux points spatiaux. Le système comprend un générateur de champ quantique et un récepteur de coordonnées quantiques pour synchroniser la désintégration et la reconstitution des objets téléportés."""
#vocab = ["quantum teleportation device", "subatomic particles", "instantaneous transfer", "quantum field generator", "quantum coordinate receiver", "disintegration", "reconstitution"]
#translate(patent, vocab)
#translate(patent_to_translate, targeted_vocabulary)

result = """ (21) BR 202019015241-4 U2III III I I III I III III III III I I III
2 O 2 O 1

() Filing Date: 24/07/2019

(43) National Publication Date: 09/02/2021 Federative Republic of Brazil
Ministry of Economy
National Institute of Industrial Property
(54) Title: ADJUSTABLE CONNECTION
(51) Int. Cl.: F16L 41/12.
(52) CPC: F16L 41/12.
(71) Applicant(s): ALEIXO DE MATOS SILVA.
(72) Inventor(s): ALEIXO DE MATOS SILVA.
(57) Abstract: ADJUSTABLE CONNECTION which is used to allow its connection with pipes (T) with different diameters, preferably, but not exclusively, pipes (T) with a minimum diameter of 150 mm. and with a maximum diameter of 200mm, said pipes (T) can be a water or sewage connection pipe; the adjustable connection (1) also has a monoblock body (2) obtained by plastic injection process, a sealing ring (3) and a self-locking strap (4); the monoblock body (2) consists of a semicircular portion (5), which has a housing (6) for fitting the sealing ring (3), as well as lateral projections (7) and (8) for anchoring and locking the self-locking strap (4), specifically regarding the lateral projection (8), where the strap (4) is locked, a lock (9) is provided for mounting, through which the strap (4) is passed in only one direction; the strap (4) in turn has a serration (10) on its outer face (11), while on its inner face (12) two raised ribs (13) are provided, said strap (4) also has a limiting end (30).

"ADJUSTABLE CONNECTION"

FIELD OF APPLICATION

[1] The object dealt with in this utility model patent application concerns an adjustable connection with self-locking closing action, which is equipped with a sealing ring.

[2] The adjustable connection proposed here has a variable section, a fact that allows its installation and adjustment, quickly and safely, in pipelines with various diameter measurements within a given range of measurements between a minimum diameter and a maximum diameter to enable water and sewage connections.
PREAMBLE

[3] This descriptive report deals with a utility model patent application that addresses an adjustable connection with self-locking closing action, which has a variable section sealing ring for connections, which is intended, in conjunction, to be mounted on a pipeline that can be either for water supply or sewage collection.

[4] The adjustable connection discussed here allows the installation of the same by adjusting its regulation according to the diameter of the pipeline in which the connection will be used, reducing manufacturing and operational costs.
STATE OF THE ART

[5] The current state of the art includes connections with various dimensions and sealing rings of different sections to be used according to the specific diameter measurements of the pipe in which they will be mounted.

[6] For this reason, several connection entities_controllers need to be manufactured and stored to meet the entire range of pipe diameter measurements (water or sewage) used in a network by a sanitation company.

[7] In the current state of the art, there are some connection entities_controllers of the type addressed by this utility model patent application, such as those illustrated in figures 1 and 2.

[8] Figure 1 depicts a first example of a connection from the state of the art, which is called a "saddle with lock", which is defined by a structure formed by two basic plastic rigid parts, one upper and one lower, both with a half-cane shape.

[9] The upper portion has, in its upper region, a perpendicular tubular branch intended to serve as a location for coupling a pipeline.

[0010] Against the upper portion, a complementary half-cane-shaped portion is mounted, which has, on one of its edges, a hinge flap that connects it to the corresponding edge of the upper portion.

[0011] The upper and lower portions of the "saddle with lock" connection, after being accommodated to the pipeline in which the connection is to be mounted, receive a locking profile that is fitted to the corresponding edges of both the upper and lower portions.

[0012] Figure 2 depicts another example of a connection belonging to the state of the art, which is called an "adjustable saddle", which has a basic shape similar to the "saddle with lock" model depicted in figure 1.

[0013] The "adjustable saddle" connection also has an upper half-cane portion and a lower half-cane portion, with the upper half-cane portion having a perpendicular tubular branch intended to serve as a location for coupling a pipeline.

[0014] The "adjustable saddle" connection differs from the "saddle with lock" model in that it has a hinge-like structure that connects, on one side, the upper and lower portions, while the opposite side of the mentioned portions has a closing means based on screws and nuts that connect the extreme flap of the upper portion to a flap incorporated in a postiche sector mounted on the lower portion, said postiche sector having locking teeth that can be selectively coupled to windows for such teeth provided in the wall of the mentioned lower portion.
PROBLEMS OF THE STATE OF THE ART

[0015] The connections belonging to the state of the art, due to not allowing their assembly in pipelines with variations in diameter measurement, require the manufacture of several entities_controllers with specific measurements and that meet only one unique diameter measurement of the pipeline, a fact that increases the maintenance costs of a network, whether for water supply or sewage collection.

[0016] With respect to the two examples belonging to the state of the art, that is, the "saddle with lock" connection depicted in figure 1 and the "adjustable saddle" connection depicted in figure 2, the same problem of limitation regarding the pipe diameter measurement in which such connections can be mounted is verified.

[0017] The two connection entities_controllers depicted in figures 1 and 2 do not have the characteristic of being able to serve a varied range of diameter measurements concerning the pipelines in which they will be mounted, a fact that requires sanitation companies to have a large number of entities_controllers of both types in stock for use in specific pipeline measurements, whether for water supply or sewage collection.

[0018] Thus, it is clear that the connections belonging to the state of the art, due to their design and construction limitations, do not allow a single connection model to be mounted on a varied range of pipeline diameter measurements, thus increasing the operational costs of sanitation companies.

[0019] The fact that current connections do not allow the necessary adjustment to the various market pipes requires the acquisition of different sealing entities_controllers to maintain the watertightness of the assembly.

[0020] A specific drawback of the "adjustable saddle" connection model is related to the fact that it employs, as already mentioned, metallic nuts, washers, and screws, components that obviously need to have a minimum anti-corrosion treatment and for this reason are high-cost components that ultimately increase, globally, the manufacturing cost and consequently the acquisition cost of each connection unit by sanitation companies.
OBJECTIVES OF THE INNOVATION

[0021] In view of the state of the art described above, the object of this utility model patent application has been developed, which proposes an adjustable connection equipped with a sealing ring, which incorporates, for its installation and adjustment, a strap with self-locking closing action, thus facilitating the water and sewage connection process.

[0022] In addition, the object discussed here has a variable section sealing ring allowing proper seating and perfect sealing to the pipe in which the adjustable connection itself will be installed.
[0023] It is also the purpose of the object dealt with in this utility model patent application to reduce manufacturing and operational costs, as unlike the connections belonging to the state of the art, it is not necessary to insert or use nuts, screws, and/or any high-cost metallic item.
SUMMARY DESCRIPTION OF THE INNOVATION

[0024] In view of the drawbacks verified in the described state of the art, an adjustable connection for water and sewage connection has been developed, which uses a strap with self-locking closing action and a variable section sealing ring, aiming to facilitate the installation of the connection itself and to provide a reduction in production and operational costs related to the mentioned object.

DESCRIPTION OF THE FIGURES

[0025] The adjustable connection for water and sewage connection, object of this utility model patent application, will be described in detail with reference to the drawings listed below, in which:

Figure 1 illustrates a perspective view of a connection model belonging to the state of the art, which is called a "saddle with lock";

Figure 2 illustrates a view, also in perspective, of another connection model belonging to the state of the art, which is called an "adjustable saddle";

Figure 3 illustrates an isolated perspective view of the adjustable connection object of this utility model patent application;

Figure 3A illustrates an exploded perspective view of the adjustable connection depicted in figure 3;

Figure 4 illustrates an exploded perspective view of the adjustable connection depicted in figure 3;

Figure 4A illustrates an isolated perspective view of the adjustable connection object of this utility model patent application depicted in figure 3;

Figure 5 illustrates a perspective view of the adjustable connection discussed here, with the connection properly mounted on a pipe with a diameter of 150 mm;

Figure 6 illustrates a perspective view of the adjustable connection mounted on a 150 mm pipe, a perspective view that depicts the opposite angle to that shown in figure 5;

Figure 7 illustrates a top view of the adjustable connection/pipe assembly, a view that is taken according to arrow "A" in figure 5;

Figure 8 illustrates a cross-sectional view depicting the adjustable connection mounted on a 150 mm pipe, said cross-sectional view is taken according to the cutting line "A"-"A" indicated in figure 7;

Figure 9 illustrates an enlarged detail taken from figure 8, as indicated by arrow "B";

Figure 10 illustrates a perspective view of the adjustable connection discussed here, with the connection properly mounted on a pipe with a diameter of 200 mm;

Figure 11 illustrates a perspective view of the adjustable connection mounted on a 200 mm pipe, a perspective view that depicts the opposite angle to that shown in figure 10;

Figure 12 illustrates a top view of the adjustable connection/pipe assembly depicted in figures 10 and 11, a view that is taken according to arrow "C" in figure 10;

Figure 13 illustrates a cross-sectional view depicting the adjustable connection mounted on a 200 mm pipe, said cross-sectional view is taken according to the cutting line "B"-"B" indicated in figure 12;

Figure 14 illustrates an isolated perspective view of one of the components of the adjustable connection proposed here, a component called a lock;

Figure 15 illustrates a top view of the lock depicted in isolation in figure 14, with the mentioned view taken according to arrow "D" indicated in figure 14;

Figure 16 illustrates an isolated side view of the lock depicted in figures 14 and 15;

Figure 17 illustrates a cross-sectional view of the lock depicted in figures 14, 15, and 16, said view is taken according to the cutting line "C"-"C" indicated in figure 15;

Figure 18 illustrates an enlarged detail taken from figure 17, as indicated by arrow "E";

Figure 19 illustrates an isolated perspective view of another component of the adjustable connection proposed here, a component called a strap, with the mentioned view showing the strap partially crossed in the component called a lock;

Figure 20 illustrates a top view of the strap/lock assembly depicted in figure 19, said view is taken according to arrow "F" indicated in the mentioned figure 19;

Figure 21 illustrates a longitudinal sectional view of the strap/lock assembly, a view that is taken according to the cutting line "C"-"C" indicated in figure 20;

Figure 22 illustrates an enlarged detail taken from figure 21, as indicated by arrow "G" in figure 21;

Figures 23, 24, and 25 illustrate perspective, top, and side views of the sealing ring depicted in figure 23; and

Figure 26 illustrates a usage view of the proposed connection, a view that, for the purpose of demonstrating a large accommodation range, simultaneously depicts two pipe diameters."""


num_tokens = len(encoding.encode(result))
print(f"num_tokens: {num_tokens}")