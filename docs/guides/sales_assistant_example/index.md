# Sales Assistant Configuration Example

In this documentation, we will go through the process of configuring the Mojodex platform for a specific use case.

Its adaptability to specific use cases is what makes Mojodex the perfect tool for businesses that want to **create a digital assistant tailored to their needs while maintaining control over it**.

To illustrate the process, we will go through the **Sales Assistant** use case.

The goal of the **Sales Assistant** is to help sales people to be more efficient in their daily tasks.

We will start by defining the scope of the Sales Assistant and then describe the different tasks it can perform.

## What you will learn

By the end, you will know how to:
- lead discussions within your teams to define the Sales Assistant's scope
- design the different tasks of the Sales Assistant
- implement the configuration in your Mojodex instance
- deploy and test the Sales Assistant


## 1. Define the Sales Assistant Scope

In their job, sales people have to perform a lot of different tasks and work activities, as described in [the O*NET OnLine - Sales Representatives – Detailed Job Description](https://www.onetonline.org/link/summary/41-4011.00)

We want to select a subset of these tasks to facilitate with the Sales Assistant, to help sales people focus on their core activities.

### Teamwork to define the scope

To define the scope of the Sales Assistant, we will need to work with the sales team to understand their daily tasks and the challenges they face.

We will need to ask them questions such as:
- What are the most repeatable time-consuming tasks?
- Where do you spend most of your time out of your core sales activities?

> 📄 You can use the following template questionnaire to lead the discussion
>
> [Sales Assistant Scope Template](./sales_assistant_scope_template.md)


The result of this teamwork will provide a list of tasks that the team would like to facilitate.

Assess their feasibility with Mojodex and prioritize them.

Once you are ready, you can start to implement the Sales Assistant.

We recommend to start with a few tasks and then iterate on the configuration.

In the next section, you will find common sales assistant tasks that you can use as a starting point.

### Starting point

We recommend the following tasks which are the most common and time-consuming for sales people:

- **Meeting Recap**: The Sales Assistant will help sales people to recap the meetings they had with their leads.
- **Event Conversation Recap**: The Sales Assistant will help sales people to recap the conversations they had with leads during events.
- **Follow-up Email**: The Sales Assistant will help sales people to write follow-up emails to leads.

## 2. Designing the tasks

Now that we have a list of tasks, we want to design how Mojodex will facilitate them.

For each task, you now have a sentence that describes what the team is expecting the Sales Assistant to do.

Use the following route to prepare a task in JSON format for each task:
```
curl --location --request POST 'http://localhost:5001/task_json' \
--header 'Authorization: backoffice_secret' \
--header 'Content-Type: application/json' \
--data-raw '{"datetime": "2024-02-14T17:49:26.545180",
"task_requirements": "<task_description>"
}'
```

You will need those JSON files for the next step: implementation

## 3. Implement the Sales Assistant Configuration

With the scope and tasks designed, we can implement the configuration in Mojodex.

### 3.1 Setup the category

First, we need to setup the category for the Sales Assistant.

> ℹ️ See the environment setup documentation to get your token: `.env.example`
>
> `BACKOFFICE_SECRET=<your_token>`

Replace `<BACKOFFICE_SECRET>` with your actual token and run the following command in your terminal
```shell
curl -X 'PUT' \
  'http://localhost:5001/product_category' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{ \
  "datetime": "2024-02-14T10:46:15.283Z", \
  "label": "string", \
  "displayed_data": [ \
    { \
      "language_code": "en", \
      "name_for_user": "Sales", \
      "description_for_user": "Boosting sales? I've got your back!" \
    } \ 
  ], \
  "emoji": "💼", \
  "implicit_goal": "Drive revenue growth by mastering sales interactions and fostering lasting client relationships." \
}'
```

> The terminal will return a response with the `product_category_pk`. We will need it for the next step.

### 3.2 Setup the product

Then, we need to setup the product for the Sales Assistant.

Replace `<BACKOFFICE_SECRET>` and `<product_category_pk>` with the previously created category pk and run the following command in your terminal:

```shell
curl -X 'PUT' \
  'http://localhost:5001/product' \
    -H 'Authorization: <BACKOFFICE_SECRET>' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
  "datetime": "2024-02-14T10:53:06.502Z",
  "product_label": "sales_assistant",
  "displayed_data": [
    {
      "language_code": "en",
      "name": "Sales Assistant"
    }
  ],
  "product_category_pk": <product_category_pk>,
  "is_free": true,
  "n_days_validity": 99999,
  "n_tasks_limit": null
}'
```

> We set a 99999 days (~273 years) duration for the product to avoid any expiration.

### 3.3 Setup the tasks

#### 3.3.1 Create the tasks
The tasks are described in the `tasks` folder of the repository. Each task is a JSON file that describes the task and its parameters.

- Qualify Leads: [Qualify Leads](../../guides/sales_assistant_example/tasks/qualify_lead.json)
- Meeting Recap: [Meeting Recap](../../guides/sales_assistant_example/tasks/meeting_recap.json)
- Event Conversation Recap: [Event Conversation Recap](../../guides/sales_assistant_example/tasks/event_conversation_recap.json)
- Follow-up Email: [Follow-up Email](../../guides/sales_assistant_example/tasks/follow_up_email.json)

```shell
for task in tasks/*.json; do
    curl -X 'PUT' \
        'http://localhost:5001/task' \
        -H 'Authorization: <BACKOFFICE_SECRET>' \
        -H 'accept: application/json' \
        -H 'Content-Type: application/json' \
        -d "@$task"
done
```

> The terminal will return a response with the `task_pk` for each task. We will need it for the next step.

#### 3.3.2 Specific configuration for the "Qualify Lead" task

For this task, we need to add a tool: Google Search.

This tool will be used to search for information about the lead.

The tool is already available in the Mojodex platform, so we just need to associate it to the task.

Table of default existing tools:
| tool_pk | name | description |
| --- | --- | --- |
| 1 | google_search | Make some research on Google |
| 2 | internal_memory | Retrieve past tasks you helped the user with. |

We provide a description of the usage of the `google_search` tool for the task:
> Use this tool to search for information that could help you qualify the lead.\n Start with a general research about the company to find its industry. A google query made only of the company name is usually the best way to go at first. Make sure you spell the company name correctly. Then look for the company's industry trends, news, and recent events.



Replace `<BACKOFFICE_SECRET>` and `<task_pk>` with the previously created task pk for the "Qualify Lead" task and run the following command in your terminal:

```shell
curl -X 'PUT' 'http://localhost:5001/task_tool' \
-H 'Authorization: <BACKOFFICE_SECRET>' \
-H 'accept: application/json' \
-H 'Content-Type: application/json' \
-d @- <<EOF
{
  "datetime": "2024-02-14T11:00:00.000Z",
  "task_pk": <task_pk>,
  "tool_pk": 1,
  "usage_description": "Use this tool to search for information that could help you qualify the lead.
  Start with a general research about the company to find its industry. A google query made only of the company name is usually the best way to go at first. Make sure you spell the company name correctly. Then look for the company's industry trends, news, and recent events."
}
EOF
```


### 3.4 Associate the tasks to the product

For each task created, we need to associate it to the product.

Replace `<BACKOFFICE_SECRET>` and `<task_pk>` with each previously created task pk and run the following command in your terminal as many times as necessary:

```shell
curl -X 'PUT' \
  'http://localhost:5001/product_task_association' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
    -H 'accept: application/json' \
    -H 'Content-Type: application/json' \
    -d '{
    "datetime": "2024-02-14T11:00:00.000Z",
    "product_pk": <product_pk>,
    "task_pk": <task_pk>
}'
```

## 4. Deploy and test the Sales Assistant

Now, the final part is to provide access to the Sales Assistant to the sales team.

### 4.1 Deployment to the existing users

To do so, we will provide access the sales team accounts to the Sales Assistant product.

Run the following command for each user identified by their email:

In a terminal, run the following command:

> ℹ️ Replace `<BACKOFFICE_SECRET>` , `<product_pk>` and `<user_email>` with the actual values.

```shell
curl -X 'PUT' \
  'http://localhost:5001/manual_purchase' \
  -H 'Authorization: <BACKOFFICE_SECRET>' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "datetime": "2024-02-14T11:53:58.771Z",
  "user_email": "demo@example.com",
  "product_pk": <product_pk>,
  "custom_purchase_id": "demo"
}'
```

### 4.2 New sales team members

For new sales team members, during the onboarding process, they will now have to choose the 'Sales Assistant' product, that we just created.

## Future work

- Integration with the CRM