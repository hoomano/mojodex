# Create a new task

## Technical definition
A task is a JSON object that contains all necessary information to render it in the app and to guide the assistant through the process of drafting the document resulting from the task.
You can find a template of a task in the file `task_spec.json` in this repository.

Let's break this specification down with "meeting_minutes" task as an example.

#### Platforms
```
"platforms": ["mobile"]
```
Platforms on which the task is available. Can be "webapp", "mobile" or both.

### System information
```
"name_for_system": "prepare_meeting_minutes",
"definition_for_system": "The user needs assistance to prepare a meeting minutes"
```
These fields are used by the system to defined tasks in prompts. name_for_system should be snake_case.

### Final instruction
```
"final_instruction": "Write a meeting minutes in the form of bullet points"
```
This is the final instruction provided to the assistant prompt. It contains all instruction the assistant will follow to draft the document. It ends with an infinitive verb sentence as if it was an order to the assistant.

### Output format
```
"output_format_instruction_title": "SHORT CONTEXT - DATE OF THE DAY",
"output_format_instruction_draft": "CONTENT OF THE MEETING MINUTES"
```
These fields are used to define the format of the document resulting from the task. The assistant will use these instructions to format the document title and content.

### Output type
```
"output_type": "meeting_minutes"
```
This field is used to define the type of document resulting from the task. It is used to enable special edition features once the document is ready. The value should match one existing in table 'md_text_type' of your database. Default existing values in database are "meeting_minutes", "email" and "document". We will cover how to add new types in a coming documentation.

### Icon
```
"icon": "📝"
```
The icon displayed in the app to represent the task.

### Task displayed data
```
"task_displayed_data": [
    {
        "language_code": "en", 
        "name_for_user": "Meeting Recap",
        "definition_for_user": "Get a simple summary and next steps for your meeting",
        "json_input": [  
            {
                "input_name": "meeting_informations",
                "description_for_user": "How was your meeting?",
                "description_for_system": "Informations the user gave about the meeting (ex: participants, date, key topics, followup actions...)",
                "placeholder": "Record a quick summary of what was discussed.",
                "type": "text_area"
            }
        ]
    },
    {
        "language_code": "fr",
        "name_for_user": "Récapitulatif de Réunion",
        "definition_for_user": "Obtenez un récapitulatif simple de votre réunion",
        "json_input": [
            {
                "description_for_system": "Informations que l'utilisateur a fournies sur la réunion (ex : participants, date, sujets clés, actions de suivi...)",
                "description_for_user": "Comment s'est passée votre réunion ?",
                "input_name": "informations_reunion",
                "placeholder": "Enregistrez un bref résumé de ce qui a été discuté.",
                "type": "text_area"
            }
        ]
    }
]
```
This field contains all data displayed to the user in the app. It is an array of objects, each object representing a language. You can add as many languages as you want but you have to define at least english as it will be used as a fallback if the user's language is not available.
The object contains the following fields:
- language_code: the language code of the language
- name_for_user: the name of the task in the language as it will be displayed to the user
- definition_for_user: the definition of the task in the language as it will be displayed to the user
- json_input: an array of objects, each object representing an information the user has to provide to the assistant when starting a new task. 
    - On the web app, it will be displayed as a form, one input per object. 
    - On the mobile app, it will be displayed in a chat as questions.
    Each object contains the following fields:
        - input_name: the name of the input as it will be used in the assistant prompt
        - description_for_user: the description of the input as it will be displayed to the user
        - description_for_system: the description of the input as it will be used in the assistant prompt
        - placeholder: the placeholder of the input as it will be displayed to the user
        - type: the type of the input. Can be only "text_area" for now.

> Note: For mobile use to remain interface friendly, we recommend to keep the number of inputs to 1. If the assistant needs to ask more than one question, it will do it in a conversational way.

### Infos to extract
```
"infos_to_extract": [
    {
        "info_name": "key_topics",
        "description": "Key topics discussed in the meeting"
    },
    {
        "info_name": "participants",
        "description": "Participants of the meeting"
    },
    {
        "info_name": "date_of_meeting",
        "description": "Date of the meeting"
    },
    {
        "info_name": "followup_actions",
        "description": "Followup actions if any"
    }
]
```
This field contains all the information the assistant needs to collect from the user before drafting the document. It is an array of objects, each object representing an information. Each object contains the following fields:
- info_name: the name of the information as it will be used in the assistant prompt
- description: the description of the information as it will be used in the assistant prompt


#### predefined_actions
```
"predefined_actions": []
```
Predefined actions will be covered in a coming documentation. Let's keep it empty for now.

## How to create a new task?

Let's create your first task on Mojodex.

From the root of the repository.

STEP 1: Create the json file
```
cp ./docs/configure_assistant/create_tasks/task_spec.json ./docs/configure_assistant/create_tasks/tasks_json/my_task.json
```

Fill the json values of my_task.json with the ones fitting your need for this task.

STEP 2: Add the task to the database
```
CURRENT_DATETIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
jq --arg datetime "$CURRENT_DATETIME" '. + {datetime: $datetime}' ./docs/configure_assistant/create_tasks/tasks_json/my_task.json > modified_task.json

curl --location --request PUT 'http://localhost:5001/task' \
--header 'Authorization: backoffice_secret' \
--header 'Content-Type: application/json' \
--data @modified_task.json
```
This commands create the task in the database and returns the primary key of the task. You will need this primary key in next step.

STEP 3: Associate the task to your user though a product
Default user `demo@example.com` is associated with default product `demo` with pk 1. Let's add the task to this product.
```
curl --location --request PUT 'http://localhost:5001/product_task_association' \
--header 'Authorization: backoffice_secret' \
--header 'Content-Type: application/json' \
--data-raw '{
 "datetime": "'"$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"'",
 "product_pk": 1,
 "task_pk": <task_pk retrieved from previous command>
}'
```

STEP 4: Test your task

Run your local Mojodex instance and access the web or mobile app.

You should now see your task in the list of available tasks. If you don't, ensure to reload the app to get rid of any potential cache.