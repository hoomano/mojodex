# MOJODEX Background

The background is responsible for processing data in the background.
It is useful for long-running process that would otherwise block the main backend.
It is also useful for processing batch data (like sending emails or notifs to a group of users).


## Structure
The background is a Flask application which routes can only be called by Mojodex's backend or by the Scheduler.

> The background must be deployed in the same network as the backend and scheduler so that the backend can call its routes but its routes must not be accessible from the outside.

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
When Mojodex's Backend or Scheduler calls Mojodex's Background to manage a process, it sends a request using REST API. Then, the route uses the app `ThreadPoolExecutor executor` to launch the required process in a parallel thread and return a 200 status code to indicate that the process has been launched.

Access to the database within parallel threads is done by decorating methods requiring this access with decorator `@with_db_session`. This decorator opens a new Session accessing the database, executes the decorated method and closes the session. This ensures no database session will remain open after the method is executed.

Here is an example of a parallel process to extract To-Do items from a task:

`background/app/models/todos/todos_creator.py`
```python
class TodosCreator:

    # The instanciation is done by passing a key and not a DB object to avoid keeping a DB session open while a parallel thread using this object will be launched
    def __init__(self, user_task_execution_pk):
        self.user_task_execution_pk = user_task_execution_pk
        
    # This is the method launched in a parallel thread
    def extract_and_save(self):
        collected_data = self._collect_data()
        json_todos = self._extract(*collected_data)
        [...]
        self._save_to_db(todo['todo_definition'], todo['due_date'])

    @with_db_session
    def _collect_data(self, db_session):
        # This method uses a dedicated db_session to access the database and retrieve all the data needed for the process
        # It does not return any DB object but only required data to avoid keeping the DB session open
        [...]
        user = db_session.query(User) ...
        [...]
        return user.user_id, user.datetime_context, user.name, ...

    def _extract(self, user_id, datetime_context, name, ...):
        # This method processes the raw data provided by _collect_data to extract To-Do items
        [...]

    @with_db_session
    def _save_to_db(self, description, due_date, db_session):
         # create new todo
            new_todo = MdTodo(
                creation_date=datetime.now(),
                description=description,
                user_task_execution_fk=self.user_task_execution_pk
            )
            db_session.add(new_todo)
            [...]
            db_session.commit()
            [...]
```

This process is launched when calling route `background/app/routes/extract_todos.py` from the Backend:
```python
class ExtractTodos(Resource):

    def post(self):
        [...]
        todos_creator = TodosCreator(user_task_execution_pk)
        executor.submit(todos_creator.extract_and_save)
        return {"success": "Process started"}, 200
```


## Functionalities

For now, Mojodex's Background manages 5 processes:

### ExtractTodos
- Route: `background/app/routes/extract_todos.py`
- Service: `background/app/models/todos/todos_creator.py`

This process is launched at the end of a task to extract any next step the user could have mentioned explicitely in the task process and turn those into To-Do items to add to the user's To-Do list.
It is triggered by the Scheduler, calling the Backend that collects ended tasks that have not been processed yet and calls the Background to launch the extraction process for each of those tasks.

### RescheduleTodo
- Route: `background/app/routes/reschedule_todo.py`
- Service: `background/app/models/todos/todos_rescheduler.py`

This process is called to reschedule a To-Do item that passed its due date without being deleted or marked as completed.
It is triggered by the Scheduler, calling the Backend that collects To-Do items that have passed their due date and calls the Background to launch the rescheduling process for each of those To-Do items.

### CreateDocumentFromWebsite
- Resource: `background/app/routes/create_document_from_website.py`
- Service: Uses `mojodex_core.website_parser` to parse the website, extract its content and turn it into a document.

This process is called to parse a website, extract its content, cut it into chunks, vectorized and load it in database as a document. It is used when user provides a new website as resource. It is useful to launch it in background because the process of validating chunks that are relevant and embedding them can be long.

### UpdateDocument
- Resource: `background/app/routes/update_document.py`
- Service: Uses `mojodex_core.website_parser` if the document is a website, `Document.update` otherwise.

This process is called to update a document in the database when user provides a new version of a resource.
If the document is a website, it will parse the website again, extract its content, cut it into chunks, vectorized and update associated document in database.
If the document is not a website but directly a text, it will only update the document in database.
Anyway, the process of updating a document requires embedding the new version, which take time and therefore is launched through the Background.

### EventsGeneration
- Resource: `background/app/routes/event_generation.py`
- Cortex: `background/app/models/events/event_generator.py` (abstract class, implementation depends on parameters of request)

This process is called any time the Backend wants to send a notification to the user whether it is a mail, push notification... The Background is responsible for notification content generation and event sending.
For now, 2 types of events are generated:
- calendar_suggestions: will be removed soon
- todo_daily_emails: An email to remind the user of his To-Do items for the day. Launched from the Scheduler every day at 8am, the Backend selects the user that opted-in this option and triggers the Background to generate the email content.


## System 1/System 2 Abstraction

To draw a parallel with the System 1/System 2 abstraction, **Mojodex's Background embodies the deliberate nature of System 2 thinking.**

It meticulously manages long-running processes and handles batch data tasks with careful attention, akin to System 2's deliberate memory search and complex computations. This component ensures the smooth functioning of Mojodex's operations, providing the necessary depth and thoroughness to complement the swift responsiveness of the Backend.
