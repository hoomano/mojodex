# Instruct Task Execution Workflow in Mojodex

This document provides an overview of the concept related to the task execution process in the Mojodex platform and describes the sequence of events that occur from the moment a user initiates a new task execution until the task is completed and the result is delivered.

## Main concepts

The task execution process involves several concepts matching database tables.

#### Task
- Task concept is fully described in [this doc](./whats_a_task.md). Basically, a task is a some work the assistant can help the user with. A task is fully configurable. A task can be of type "instruct" or "workflow".
> This documentation

#### User Task
- Each user has its own set of tasks it can launch with Mojodex.  A `user_task` stands for the association between a user and a task. Those association are defined by user's product (detailled in a coming doc).

#### User Task Execution
- A `user_task_execution` represents the instance of a task being executed by a user. It captures various details such as the start time and any relevant metadata pertaining to the execution of a specific task by a user.

> Note, sometimes refered as `task_execution` for short.

#### Session
- A `session` represents an interaction between the user and the assistant. It captures the messages exchanged between the user and the assistant, as well as the state of the conversation at any given time. A `user_task_execution` always needs a `session` for the user and its assistant to co-work on the task.

> Note: With existing interface, a `user_task_execution` has 1 `session`.
> 1 `session` can have multiple `user_task_execution`, for example using a more general chat with routing to specific tasks.

#### Message
- A `message` represents a single message exchanged between the user and the assistant within a session. It captures the content of the message, sender, timestamp of the message, and other relevant metadata depeding on the type of message. In the database, a `json` field is used to store the content of the message, allowing high flexibility regarding stored data.

#### Produced text
- A `produced_text` represents the result of a task execution. It contains all versions of the result as references to `produced_text_version`

#### Produced text version
- A `produced_text_version` represents a version of the result of a task execution. It contains the content of the result and the date of the version.

![task_execution](../../images/task_execution/task_execution_concepts.png)

## Task execution workflow

The task execution workflow is a sequence of events that occur from the moment a user initiates a new task execution until the task is completed and the result is delivered. The workflow is described below.

### 1. User Task Execution Creation
Creation of execution is done as soon as the user hits the card of the task they want to create.

![select_task](../../images/tasks/tasks.png)

This generates a call to PUT `/user_task_execution` to the backend (`backend/app/routes/user_task_execution.py`), specifying the `user_task` the user wants to execute.
This call creates a User Task Execution instance in the database and a `session` if not already exists (which is the case in current Mojodex implementations).

```python
from mojodex_core.entities.db_base_entities import MdUserTaskExecution
[...]
class UserTaskExecution(Resource):
    [...]
    def put(self, user_id): 
        [...]
        session_creation = self.session_creator.create_session(user_id, platform, "form")
        [...]
        session_id = session_creation[0]["session_id"]
        [...]
        task_execution = MdUserTaskExecution(user_task_fk=user_task_pk,
                                                json_input_values=empty_json_input_values, session_id=session_id)
        db.session.add(task_execution)
        db.session.commit()
```

This call also returns the input fields to display to the user in the interface so that user have the instructions to start. Those input fields are the one defined in [the task's json configuration file as `json_input`](../../guides/tasks/task_spec.json).
```python
return {**{"user_task_execution_pk": task_execution.user_task_execution_pk,
                     "json_input": json_input,
                     "actions": predefined_actions,
                     "text_edit_actions" : recover_text_edit_actions(user_task_pk=user_task_pk)
                     }, **session_creation[0]}, 200
```

![task_instructions](../../images/tasks/starting_task.png)

![instanciate_user_task_execution](../../images/task_execution/instanciate_user_task_execution.png)

### 2. User Task Execution Start
From those instructions, there are 2 ways to start the task:

#### 2.1. User Task Execution Start from filled form
This is the method used in the web interface. The user fills the form and submit it. This generates a call to POST `/user_task_execution_run` to the backend (`backend/app/routes/user_task_execution_run.py`), specifying the `user_task_execution_pk` received at previous step and the values of filled form.

Resource associated to the route updates the User Task Execution instance and instanciates a `Session`(`backend/app/models/session/session.py`).

Finally, it launches in a parallel thread the start of the task by running session.`process_form_input` method.

```python
[...]
class UserTaskExecutionRun(Resource):
    [...]
    def post(self, user_id):
        [...]
        user_task_execution.start_date = datetime.now()
        db.session.commit()
        [...]
        from models.assistant.session_controller import SessionController
        session = SessionController(user_task_execution.session_id)

        def launch_process(session, app_version, platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder):
            session.process_form_input( app_version, platform, user_task_execution_pk, use_message_placeholder=use_message_placeholder, use_draft_placeholder=use_draft_placeholder)
            return
        [...]
        server_socket.start_background_task(launch_process, session, app_version, platform, user_task_execution_pk, use_message_placeholder, use_draft_placeholder)
```

The `SessionController` is the epicenter of task execution. The function `process_form_input()` will:
- Asynchronously generate task execution title and summary
- Prepare first assistant's response to the user.

![start_user_task_execution_from_form](../../images/task_execution/start_user_task_execution_from_form.png)

#### 2.2. User Task Execution Start from user message
On the mobile app, the user sees the same instructions as in the web's form but is free to send to the assistant the first message they want. 

This first message generates a call to PUT `/user_message` (`backend/app/routes/user_message.py`) specifying the `user_task_execution_pk` received at previous step and the message content.

This route can be called for any user message, at any step in the task execution process to send user's message to backend. If it appears the User Task Execution identified by the `user_task_execution_pk` is not started, it will start it.

```python
[...]
class UserMessage(Resource):
    [...]
    def put(self, user_id):
        [...]
        user_task_execution = db.session.query(MdUserTaskExecution) \
            .join(MdUserTask, MdUserTaskExecution.user_task_fk == MdUserTask.user_task_pk) \
            .filter(MdUserTaskExecution.user_task_execution_pk == user_task_execution_pk) \
            .filter(MdUserTask.user_id == user_id) \
            .first()
        [...]

        if user_task_execution.start_date is None:
            user_task_execution.start_date = datetime.now()
            db.session.commit()
        [...]
```

Once the User Task Execution is updated, the Resource will instanciate a `SessionController` object (`backend/app/models/assistant/session_controller.py`), responsible for managing user and assistant messages exchanges.

Finally, it launched a parallel thread in which it runs method `process_chat_message` of `SessionController`.
    
```python
[...]
class UserMessage(Resource):
    [...]
    def put(self, user_id):
        [...]
        session = SessionController(session_id)

        session_message = {"text": db_message.message["text"],
                               "message_pk": db_message.message_pk,
                               "audio": not "text" in request.form,
                               "user_task_execution_pk": user_task_execution_pk,
                               "origin": origin,
                               "home_chat_pk": db_home_chat.home_chat_pk if db_home_chat else None,
                               "message_date": message_date.isoformat(),
                               "platform": platform,
                               "use_message_placeholder": use_message_placeholder,
                               "use_draft_placeholder": use_draft_placeholder}


        server_socket.start_background_task(session.process_chat_message, "user_message", session_message)
        [...]
```

The `process_chat_message` method will:
- Check the message is a task execution message
- Asynchronously generate task execution title and summary
- Instanciate an appropriate `ChatAssistant` object depending of the type of the task
- Call `generate_message()` of this assistant to generate the assistant's response to the user.

```python
[...]
class SessionController:
    
    [...]

    def process_chat_message(self, message):

        [...]

        if "message_pk" not in message:
            self._new_message(message, Message.user_message_key, "user_message")

        [...]

        if "user_task_execution_pk" in message and message["user_task_execution_pk"] is not None:

            [...]

            server_socket.start_background_task(TaskExecutionTitleSummaryGenerator.generate_title_and_summary,
                                                    user_task_execution.user_task_execution_pk, callback=callback)

            [...]
            # For now only task sessions
            if user_task_execution.task.type == "instruct":
                return self.__manage_instruct_task_session(self.platform, user_task_execution, use_message_placeholder,
                                                           use_draft_placeholder)
            else:
                return self.__manage_workflow_session(self.platform, user_task_execution, use_message_placeholder,
                                                      use_draft_placeholder)
        [...]
[...]
```



![start_user_task_execution_with_message](../../images/task_execution/start_user_task_execution_with_message.png)
     
### 3. Iterating on a task

The task execution process is an iterative process. The user and the assistant exchange messages until the user is satisfied with the produced result.

When the assistant sends a message to ask for any precision or when they want to ask for an edition, the user can send a message through the chat interface to interact with the assistant.

When the user sends a message during a task execution, the message is sent to the backend through a PUT `user_message` call and the same process as described in part 2.2 is repeated.

![complete_user_task_execution_flow](../../images/task_execution/complete_user_task_execution_flow.png)