# Create a new tool

## Technical definition
A tool is some code the agent can execute in background to complete a task. It can be an API call, a database query, a file reading, etc.
Often, a tool is used to collect information needed for task execution.

## How to create a new tool?

STEP 1: Create the tool in the database

Replace `<BACKOFFICE_SECRET>` with your actual token and name and definition with the actual tool name and definition. Then, run the following command in your terminal:

```shell
curl --location --request PUT 'http://localhost:5001/tool' \
--header 'Authorization: <BACKOFFICE_SECRET>' \
--header 'Content-Type: application/json' \
--data-raw '{"datetime": "2024-02-14T17:49:26.545180",
"name": "<TOOL_NAME>", "definition": "<TOOL_DEFINITION>"
}'
```

STEP 2: Create the tool in the background code

In `background>app>models>task_tool_execution>tools`, create a new file named `<TOOL_NAME>.py` and implement the tool code.

The tool code must extends the `Tool` class. Define:
- a variable `name` with the tool name that matches the one in the database
- a variable `tool_specifications` containing the json specifications of parameters required to run a tool query.
- a variable `n_total_usages` defining the number of queries within 1 tool execution. Queries are chained, allowing the assistant to go step by step deeper in the information gathering process.
- a method `run_tool` that executes a tool query from given parameters and returns the result.

STEP 3: Add tool to list of available tools in Cortex
Add your tool class in `background/app/models/cortex/task_tool_execution_cortex.py` available_tools list.

> Your tool is now available for use in tasks.

## Associate tool to a task
A tool can be used only in tasks that have been explicitly associated with it. This association includes a task, a tool and a description of how the tool is used in the task.

To associate a tool to a task:

Replace `<BACKOFFICE_SECRET>` with your actual token, `<TOOL_PK>` with the actual tool primary key, `<TASK_PK>` with the actual task primary key and `<USAGE_DESCRIPTION>` with the actual usage description. Then, run the following command in your terminal:

```shell
curl --location --request PUT 'http://localhost:5001/task_tool' \
--header 'Authorization: <BACKOFFICE_SECRET>' \
--header 'Content-Type: application/json' \
--data-raw '{"datetime": "2024-02-14T17:49:26.545180",
"tool_pk": "<TOOL_PK>", "task_pk": "<TASK_PK>", "usage_description": "<USAGE_DESCRIPTION>"
}'
```