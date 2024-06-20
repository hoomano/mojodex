# MOJODEX Background

The background backend is responsible for processing data in the background.
It is useful for long-running process that would otherwise block the main backend.
It is also useful for processing batch data (like sending emails or notifs to a group of users).


## Structure
The background is a Flask application which routes can only be called by Mojodex's backend.

> The background must be deployed in the same network as the backend so that the backend can call its routes but its routes must not be accessible from the outside.

`background/app/app.py`
```python
[...]
from flask import Flask
from flask_restful import Api

app = Flask(__name__)
api = Api(app)

from http_routes import *
HttpRouteManager(api)
[...]
```

The API routes are all defined in `background/app/http_routes.py` in the `HttpRouteManager` class, pointing to related Flask Resources in `background/app/routes/`.

## Usage
When Mojodex's Backend calls Mojodex's Background to manage a process, it sends a request using REST API. Then, the route always process as follow:

The Cortex are (mainly) located in `background/app/models/cortex`directory (those that are not may be refactored in coming updates). Those Cortex are classes implemented by the requested Flask Resource with 2 objectives:

- 1. Load all data needed for the process from the database. This is done synchronously in the constructor of the Cortex. This is to keep database access in the main thread and avoid database lock issues.

- 2. Process the data in the main method of the Cortext in a parallel thread launched in the Flask Resource. This main method does not have a consistent name for now and is specific to each process/cortex. An abstract class `Cortex`should be added in the future to ensure a consistent structure for all cortexes.

> Note: "Cortex" name is a reference to the outer most layer of the brain. The cortex is involved in higher processes in the human brain, including memory, thinking, learning, reasoning, problem-solving, emotions, consciousness and functions related to your senses. Here, this is an abstraction to suggest the autonomy of this technical component regarding its process.

If any additional data from the database is needed during the process, a request to the Backend will retrieve it.

- 3. Finally, if any data needs to be inserted or updated in the database, this is done by calling a Backend API route from the Cortex. This way, we ensure responsability segregation and every data written in the database is done by the Backend.

```python
class Cortex:

    def __init__(self, user_task_execution):
        # Load all data needed for the process from the database
        

    def main_method(self):
        # Run process
        # Send created or updated data to backend for update in database
```

## Functionalities

For now, Mojodex's Background manages 8 processes:

### UserTaskExecutionTitleAndSummary
- Resource: `background/app/routes/user_task_execution_title_and_summary.py`
- Cortex: `background/app/models/cortex/user_task_execution_title_and_summary_cortex.py`
- Launched from: `backend/app/models/tasks/task_manager.py`

This process is called each time the user sends a message to a task. It updates (or creates if not exists) the title and summary of the task from the ongoing conversation.

### ExtractTodos
- Resource: `background/app/routes/extract_todos.py`
- Cortex: `background/app/models/cortex/extract_todos_cortex.py`
- Launched from: `backend/app/routes/extract_todos.py`

This process is launched at the end of a task to extract any next step the user could have mentioned explictely in the task process and turn those into To-Do items to add to the user's To-Do list.

### RescheduleTodo
- Resource: `background/app/routes/reschedule_todo.py`
- Cortex: `background/app/models/cortex/reschedule_todo_cortex.py`
- Launched from: `backend/app/routes/todo_scheduling.py`

This process is called to reschedule a To-Do item that passed its due date without being deleted or marked as completed.

### ParseWebsite
- Resource: `background/app/routes/parse_website.py`
- Cortex: `background/app/models/document/website_parser.py`
- Launched from: `backend/app/routes/company.py` && `backend/app/routes/resource.py`

This process is called to parse a website, extract its content, cut it into chunks and load it in database as a document. It is used when user provides a new website as resource.

### UpdateDocument
- Resource: `background/app/routes/update_document.py`
- Cortex: `background/app/models/document/website_parser.py` || `background/app/models/document/document_manager.py` depending if the update is an edition or addition.
- Launched from: `backend/app/routes/resource.py`

This process is called to update a document in the database when user provides a new version of a resource.

### EventsGeneration
- Resource: `background/app/routes/event_generation.py`
- Cortex: `background/app/models/events/event_generator.py` (abstract class, implementation depends on parameters of request)

This process is called any time the backend wants to send a notification to the user whether it is a mail, push notification... The Background is only responsible for notification content generation.


## System 1/System 2 Abstraction

To draw a parallel with the System 1/System 2 abstraction, **Mojodex's Background embodies the deliberate nature of System 2 thinking.**

It meticulously manages long-running processes and handles batch data tasks with careful attention, akin to System 2's deliberate memory search and complex computations. This component ensures the smooth functioning of Mojodex's operations, providing the necessary depth and thoroughness to complement the swift responsiveness of the Backend.
