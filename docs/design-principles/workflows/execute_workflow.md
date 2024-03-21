# Workflow Execution Workflow in Mojodex

This document provides an overview of the concept related to the workflow execution process in the Mojodex platform and describes the sequence of events that occur from the moment a user initiates a new workflow execution until the workflow is completed and the result is delivered.

## Main concepts

The workflow execution process involves several concepts matching database tables.

#### Workflow
- Workflow concept is fully described in [this doc](./whats_a_workflow.md). Basically, a worflow is a some complex process the assistant can help the user with. A workflow is fully configurable.

#### Workflow Step
- A `workflow_step` is a single step in a workflow. It is made of {input specification, execute method, output specification}. The execute method is the core of the step, it is where the step does its job. The input and output specification are used to validate the input and output of the step.
A step can be run multiple times in a workflow, with different inputs and outputs.

#### User Workflow
- Each user has its own set of workflows it can launch with Mojodex.  A `user_workflow` stands for the association between a user and a workflow.

#### User Workflow Execution
- A `user_workflow_execution` represents the instance of a workflow being executed by a user. It captures various details such as the start time and any relevant metadata pertaining to the execution of a specific workflow by a user.

> Note, sometimes refered as `workflow_execution` for short.

#### User Workflow Execution Step Execution
- A `user_workflow_execution_step_execution` represents the instance of a step being executed within a workflow execution. It contains all valid executions of a step on a specific input and its output (refer to as `run`). As its previous step may define the different inputs of a step, step execution is initialized as soon as its previous step is fully validated by the user. The step is initialized with all its runs, based on the provided inputs.

#### User Workflow Step Execution Run
- A `user_workflow_execution_step_execution_run` represents a single run of a step execution. It captures the input and output of the step execution, as well as any relevant metadata pertaining to the execution of a specific step within a workflow execution as whether the step was validated by the user or not.

#### User Workflow Step Execution Run Execution
- A `user_workflow_execution_step_execution_run_execution` represents the instance of a step execution run being executed. A run can have multiple execution if the user asks for edition on this precise run without changing the input.

#### Session
- A `session` represents an interaction between the user and the assistant. It captures the messages exchanged between the user and the assistant, as well as the state of the conversation at any given time. A `user_workflow_execution` always needs a `session` for the user and its assistant to co-work on the workflow.

#### Message
- A `message` represents a single message exchanged between the user and the assistant within a session. It captures the content of the message, sender, timestamp of the message, and other relevant metadata depeding on the type of message. In the database, a `json` field is used to store the content of the message, allowing high flexibility regarding stored data.


![workflow_execution](../../images/workflow_execution/workflow_execution_concepts.png)

## Workflow execution workflow

The workflow execution workflow is a sequence of events that occur from the moment a user initiates a new workflow execution until the workflow is completed. The workflow is described below.

### 1. User Workflow Execution Creation
Creation of execution is done as soon as the user hits the card of the workflow they want to create.

![select_workflow](../../images/workflows/workflows.png)

This generates a call to PUT `/user_workflow_execution` to the backend (`backend/app/routes/user_workflow_execution.py`), specifying the `user_workflow` the user wants to execute.
This call creates a User Workflow Execution instance in the database and a `session` if not already exists (which is the case in current Mojodex implementations).

```python
from mojodex_core.entities import MdUserWorkflowExecution
[...]
class UserWorkflowExecution(Resource):
    [...]
    def put(self, user_id): 
        [...]
        session_creation = self.session_creator.create_session(user_id, platform, "form")
        [...]
        session_id = session_creation[0]["session_id"]
        [...]
        db_workflow_execution = MdUserWorkflowExecution(
                user_workflow_fk=user_workflow_pk,
                session_id=session_id,
                json_inputs=workflow.json_inputs_spec
            )
        db.session.add(db_workflow_execution)
        db.session.commit()
```

This call also returns a json representation of the workflow, including json_inputs_spec to display to the user in the interface so that user have the instructions to start. Those input fields are the one defined in [the workflows's json configuration file as `json_inputs_spec`](../../guides/tasks/task_spec.json).
```python
return {
                "workflow_name": <name>,
                "user_workflow_execution_pk": <pk>,
                "user_workflow_fk": <fk>,
                "steps": [step_execution.to_json() for step_execution in steps_executions],
                "session_id": <session_id>,
                "inputs": <json_inputs>
            }
```

### 2. User Workflow Execution Start
From those instructions, there are 2 ways to start the workflow:

#### 2.1. User Workflow Execution Start from filled form
This is the method used in the web interface. The user fills the form and submit it. This generates a call to POST `/user_workflow_execution` to the backend (`backend/app/routes/user_workflow_execution.py`), specifying the `user_workflow_execution_pk` received at previous step and the values of filled form.

Resource associated to the route updates the User Workflow Execution instance and instanciate a Python object WorkflowExecution.
Finally, it launches in a parallel thread the start of the workflow by running workflow.`run` method.


```python
[...]
class UserWorkflowExecution(Resource):
    [...]
    def post(self, user_id):
        [...]
        db_workflow_execution.json_inputs = json_inputs
        flag_modified(db_workflow_execution, "json_inputs")
        db_workflow_execution.start_date = datetime.now()
        db.session.commit()

        workflow_execution = WorkflowExecution(user_workflow_execution_pk)

        server_socket.start_background_task(workflow_execution.run)
        [...]
```

The `WorkflowExecution` is the epicenter of workflow execution. The function `run()` will:
- Determine what is the current step to run
- Eventually initialize current step's runs according to inputs if not done yet
- Run current run of current step
- Ask for user validation once the run is done

![start_user_workflow_execution_from_form](../../images/workflow_execution/start_user_workflow_execution_from_form.png)

> The Workflow Execution detailled flow is described in part 3.

#### 2.2. User Workflow Execution Start from user message
> TODO - NOT IMPLEMENTED YET

### 3. Workflow Execution
A Workflow Execution is a Python object that manages the execution of a workflow. It corresponds to a `user_workflow_execution` in the database.
It has a list of `WorkflowStepExecution` objects, one for each step of the workflow. The current step to run is stored in the `current_step_execution` attribute.

The entry point of the workflow execution is the `run` method of the `WorkflowExecution` class. This method is called in a parallel thread when the user starts the workflow execution or when a step_runs needs to be executed (because of user validation or because of a user instruction to re-execute).

```python
class WorkflowExecution:
    [...]
    def run(self):
        [...]
        step_execution_to_run = self.current_step_execution
        if not step_execution_to_run:
            return # TODO: manage end of workflow
        
        if not step_execution_to_run.initialized:
            step_execution_to_run.initialize_runs(self._intermediate_results[-1] if self._intermediate_results else [self.initial_parameters], self.db_object.session_id)
        
        step_execution_to_run.run(self.initial_parameters, self._history, self.db_object.session_id, workflow_conversation="")
        
        self._ask_for_validation()
        [...]
        
    [...]
```

#### 3.1 Determining current_step
The `current_step_execution` attribute is defined as the last workflow's step initialized which runs are not all validated or if there is no, the first step not initialized.
```python
class WorkflowExecution:
    [...]
     @property
    def current_step_execution(self):
        [...]
        # browse steps backwards to find last one initialized which runs are not all validated
        for step_execution in reversed(self.steps_executions):
            if step_execution.initialized and not step_execution.validated:
                return step_execution
        # else, next step to run is the first one not initialized
        for step_execution in self.steps_executions:
            if not step_execution.initialized:
                return step_execution
        return None
```

#### 3.2 Initializing a step execution
A step execution can have mulitple runs, defined by previous steps response. Therefore, we can't know in advance the number of runs a step will have. 

>Example: A workflow "Translate long text" could have 2 steps:
>- Step 1: "Divide the text in sections"
>- Step 2: "Translate each section"
>In this workflow, step 2 will have as many runs as the number of sections in the text.

At the moment the workflow enters the step, the step is initialized with as many runs as necessary. The `initialize_runs` method is called with the previous step's output corresponding to different parameters the step will be called on: 1 execution of a step on 1 parameter is called a "run".

```python
class WorkflowStepExecution:
    [...]
        def initialize_runs(self, parameters: List[dict], session_id: str):
            [...]
            for parameter in parameters:
                parameter = json.dumps(parameter)
                # create run in db
                db_run = MdUserWorkflowStepExecutionRun(
                    user_workflow_step_execution_fk=self.db_object.user_workflow_step_execution_pk,
                    parameter=parameter
                )
                self.db_session.add(db_run)
                self.db_session.commit()
                self.runs.append(WorkflowStepExecutionRun(self.db_session, db_run))
            step_json = self.to_json()
            # add session_id to step_json
            step_json["session_id"] = session_id
            server_socket.emit('workflow_step_execution_initialized', step_json, to=session_id)
            [...]
```

#### 3.3 Running a step execution
Running a step execution consists in running the last run of the step that has not been validated.

### 4. User validation
#### 4.1. User validates
#### 4.2. User does not validate