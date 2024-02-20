# Internal Memory tool

## Definition
> ```json
> {
>     "name": "internal_memory",
>     "definition": "Retrieve past tasks you helped the user with."
> }
> ```

## Usage
Used in "Briefing notes" with usage:
```
"Utilize this tool to access your internal memory, which stores information about every past tasks you helped the user with. Tasks can include meeting minutes, emails, notes or other document you help them prepare. Search in internal memory will be done using vectorial cosine distance."
```

## Code

### n_total_usages
The tool can be used to make only 1 query by execution.

### tool_specifications
```json
{
    "query": "<query you want to search in past tasks' results. It has to be made of precise keywords.>"
        
}
```

### run_tool
The `run_tool` method executes 1 query from given parameters.
The method:

- Gathers nearest neighbors of the query within the past tasks' results. This is done using a call to backend route: `backend/app/routes/retrieve_produced_text.py`. The route uses a vectorial cosine distance to find the nearest neighbors of the query in the past tasks' results embeddings stored as Vector using pgvector extension in the postgres database.
For now, limits are: 10 neighbors max and max distance 0.2.

- Extracts keypoints related to the query from the retrieved neighbors. This is done by batch to avoid too long context window and is useful to suummarize key information.

## Results
Result of the query is made of a list of references containing:
- a reference to a User Task Execution
- a produced text title
- a task icon corresponding to the task type
- the list of extracted information keypoints that could be relevant in completing the task.

```json
[
    {
        "user_task_execution_pk": 123,
        "produced_text_title": "Title of retrieved produced text",
        "task_icon": "📝",
        "extracted_informations": [
          ...
        ]
    },
    ...
    ]
```

The results of the query is then passed to the assistant so that it can write a message presenting the results to the user.