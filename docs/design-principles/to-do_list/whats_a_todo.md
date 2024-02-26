# What's a to-do?

## To-Do
A To-Do item is some work the user has to tackle later.

## Why?
This feature was thought to be the sparkle of proactivity in Mojodex. The idea is that your assistant manages your To-Do list seamlessly while you're tackling your task with its help.

> The vision of the todo-list feature is to manage itself without you having to think about it.

## Mojodex usage

### Generating to-dos items
When running [a task](../../design-principles/tasks/whats_a_task.md) on Mojodex, user may mention some next steps it has to take regarding this task.

> Example: 
> - get in touch in 3 days
> - send follow-up email
> - prepare a quote
> ...

Once the task is done, the assistant will extract any mentionned next step, turn it into a to-do item and organize it in user's to-do list. 

### To-do list extracted from achieved tasks
This way, in their to-do list, users can access the list of any work to-do mentioned to their assistant while working on tasks. Users can manage their to-do list by deleting items that might not be relevant or marking some as completed as soon as they have worked on it.

Each to-do item comes with a "scheduled_date", representing the deadline to achieve this work. This date is defined by the assistant at to-do creation.

### Proactive organization: Organize & Remind the user
For users not to forget their pending work, a daily email is sent to them every morning containing:

- The list of to-do items due for the day
- An eventual summary of the re-organization work done by the assistant during the night

Re-organization consists in re-scheduling for later any to-do items that should have been achieved by the day before but have not been marked as completed.

### User action
User keeps control on their To-Do list by:
- Deleting items that might not be relevant
- Marking some as completed as soon as they have worked on it

### To go further
Learn how the todo-list feature works in the [technical documentation](./how_todo_works.md)