# Create a new workflow

## Technical definition
A workflow is a sequence of steps that the agent must execute one by one. Each step execution then requires a user validation before the agent can proceed to the next step. 
Compared to the tasks, the workflows are more complex and constrainted, allowing the user to keep more control over the agent's actions.

## How to create a new workflow?

STEP 1: Create the steps' code
In `backend>app>models>workflows` create a new folder named by your workflow. In this folder, create one file per step in your workflow.
In each of those files, implement the crresponding step code.
A workflow step is a class that implements the `WorkflowStep` class. 

An implementation of `WorkflowStep` looks like this:
```python
from models.workflows.step import WorkflowStep        

class MyWorkflowStep(WorkflowStep):

    @property
    def description(self):
        return "This is the description of the step" # Description of the step as used in prompts

    @property
    def input_keys(self):
        return ['input_key1', 'input_key2'] # List of keys that must be present in the input parameter
     
    @property
    def output_keys(self):
        return ['output_key1', 'output_key2'] # List of keys that will be present in the output parameter

    
    def _execute(self, parameter: dict, learned_instructions: dict, initial_parameter: dict, history: List[dict],  workflow_conversation: str):
        try: 
            # parameter contains every input keys
            return [{'output_key1': <output>, 'output_key2': <output>}] # output contains every output key
        except Exception as e:
            raise Exception(f"execute :: {e}")
```

STEP 2: Add your steps to the steps library
In `backend>app>models>workflows>steps_library.py`, add your steps to the `STEPS` dictionary. The key must be the name of the step and the value must be the class of the step. This is used to dynamically load the steps from their name in the database.

STEP 3: Create the workflow
To create a new workflow, you can use the dedicated route PUT `/workflow`

Replace `<BACKOFFICE_SECRET>` with your actual token and name, steps, icon and description with the actual workflow name, steps, icon and description.
> Careful: steps names must match the ones in the steps library.
> Careful: steps must be in the right order.

Then, run the following command in your terminal:

```shell
curl --location --request PUT 'http://localhost:5001/workflow' \
--header 'Authorization: <BACKOFFICE_SECRET>' \
--header 'Content-Type: application/json' \
--data-raw '{"datetime": "2024-02-14T17:49:26.545180",
    "name": "<WORKFLOW_NAME>",
    "steps": ["<STEP_1_NAME>", "<STEP_2_NAME>"],
    "icon": "<EMOJI>",
    "description": "<WORKFLOW_DESCRIPTION>",
    "json_inputs_spec": [{"input_name": "<INPUT_NAME>", "default_value": "<DEFAULT_VALUE>"}]
}'
```
⚠️ "default_value" in "json_inputs_spec" is temporary, for debug purpose. Nothing has been implemented yet to handle other values than the default one.

STEP 4: Define workflow checkpoints
By default, every step is defined as a checkpoint. This means that at the end of each step_execution_run, if the user does not validate the result, the user will give an instruction and this same step_execution_run will be executed again.

Example on Qualify Lead workflow:
Step 1 is "Write the query you will use with SERP API to search Google"

- Step 1 - Run 1 - Execution 1:
        parameter: {"company": "Hoomano"}
        learned instructions: None
        step result:  "query: 'Hoomano industry'"
        <USER DOES NOT VALIDATE>
        user instruction: "This query is not specific enough, please add more keywords"
        
- Step 1 - Run 1 - Execution 2: 
        parameter: {"company": "Hoomano"}
        learned instructions: "Make specific queries"
        step result:  "query: 'Hoomano company industry trends AI"
        <USER VALIDATES>
        
On the contrary, if a step is not defined as a checkpoint, the user will give an instruction but the last checkpoint step last run will be executed again.
Let's keep Qualify Lead workflow example running:
Step 2 is "Check the SERP API results and select the 3 most relevant one"

- Step 2 - Run 1 - Execution 1:
        parameter: {"query": "Hoomano company industry trends AI"}
        learned instructions: None
        step result:  "result 1, result 2, ..."
        <USER DOES NOT VALIDATE>
        user instruction: "This is not relevant, please try again, look for any blog post the company wrote"

- Step 1 - Run 1 - Execution 3:
        parameter: {"company": "Hoomano"}
        learned instructions: "Make specific queries, look for any blog post the company wrote"
        step result:  "query: 'Hoomano company AI blog posts"
        <USER VALIDATES>

- Step 2 - Run 2 - Execution 1:
        parameter: {"query": "Hoomano company AI blog posts"}
        learned instructions: "Make specific queries, look for any blog post the company wrote"
        step result:  "result 1, result 2, ..."
        <USER VALIDATES>

STEP 5: Associate workflow to a user
Replace `<BACKOFFICE_SECRET>` with your actual token and `<user_id>` and `<workflow_pk>` with the actual user id and workflow primary key.
Then, run the following command in your terminal:

```shell
curl --location --request PUT 'http://localhost:5001/user_workflow' \
--header 'Authorization: <BACKOFFICE_SECRET>' \
--header 'Content-Type: application/json' \
--data-raw '{
 "datetime": "'"$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"'",
 "user_id": <user_id>,
 "workflow_pk": <workflow_pk>
}'
```



