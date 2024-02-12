# How To-Do works?

## Extract To-Dos from achieved tasks
Mojodex's scheduler is a simple python module that triggers routes calls at a certain frequency.
One of its trigger checks every 10 minutes if a task has just been achieved.

> In this context, a task is considered just achieved if it has an associated produced_text which last version's date is between 10 and 20 minutes ago.

This task is then processed in background for To-Do extraction using a prompt filled with all tasks data and which main instructions are:

- Extraction instruction: To define what is a To-Do.
```
[...]
Extract any todo the user mentioned in the task as next steps they have to take.
Those todos describes actions the user will have to do in the future. They cannot be passive.
[...]
```

- Explicitely-mentioned only instruction: To avoid any hallucination from the agent.
```
[...]
Extract ONLY next steps the user explicitly mentioned in the task.
[...]
```

- Assigned-only instruction: To avoid including To-Dos' that could be assigned to the user's contact in an email task or other participant mentioned in a meeting minutes, for example.
```
[...]
Extract ONLY next steps assigned to the user.
[...]
```

The result of the prompt is a json list of dictionnary defining To-Do items.
```
{
    "todo_definition": "<Definition as it will be displayed in the user's todo list.
        The definition should help the user remember what was the original task.
        Mention any name, company,... that can help them get the context.>",
    "mentioned_as_todo": <Did the user explicitly mentioned this as a todo? yes/no>,
    "due_date": "<Date at which the todo will be displayed in user's todo list. Format yyyy-mm-dd>"
}
```

This json is parsed and items are added to the database, related to the task.

![extract_todos](../images/to-dos%20flow/extract_todos.png)

## Remind the user
Here comes Mojodex's scheduler again with another trigger that every hour checks users whose local time is `DAILY_TODO_EMAIL_TIME` (defined in env vars).
For each of those users, the assistant will collect all To-Dos that are due for the coming day + the re-organization work it has done (cf step 4) and draft a friendly reminding emails to send to the user.

![remind_user](../images/to-dos%20flow/remind_user.png)

## Organize
Another trigger of the scheduler takes care of reorganizing user's To-Do list every night to keep it up-to-date.
Every night between 1am and 2am user's time, the assistant collects every To-Do items that was due for the day before and has not been deleted, nor completed. In background, the assistant is prompted to re-scheduled those to a later date.

This prompt is provided with:
- related task data
- To-Do item along with the number of times it has already been rescheduled and
- User's To-Do list in upcoming days

```
[...]
Regarding the TASK, TODO ITEM and USER TODO LIST, decide when to reschedule the TODO ITEM for later.
The task was currently scheduled for yesterday.
Provide the new scheduled date.
[...]
```

This prompt outputs a json answer that can be parsed so that a new scheduling can be added to database.

![reschedule_todos](../images/to-dos%20flow/reschedule_todos.png)

## Bonus Step
User can of course also act on their own To-Dos. For now, they can take 2 actions:
- Delete a To-Do item, if it was not relevant to add it or the assistant made any mistake
- Mark a To-Do as completed as soon as they don't need it anymore to remember of the work they have to do.

![user_actions](../images/to-dos%20flow/user_actions.png)
