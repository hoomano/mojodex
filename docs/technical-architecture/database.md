# Database

This directory contains the SQL scripts to initialize the Mojodex database into a Docker container.

The Mojodex database is a PostgreSQL database using the pg_vector extension to store and query vector data.

The database is launched as a Docker container and is accessed by the `backend` and `background` services. See general documentation for more information.

## Database schema

You can have a look at the database schema at dbdiagram.io:
https://dbdiagram.io/d/MojodexDatabase-659d0645ac844320ae85b440


## Prerequisites

- Docker

## Installation

Clone the repository and navigate to the `pgsql` directory:

```bash
git clone
cd mojodex/pgsql
```

## Database configuration

The `Dockerfile` contains default environment variables for the PostgreSQL database. You can modify these variables to suit your environment.

```Dockerfile
[...]
ENV POSTGRES_DB=<database_name>
ENV POSTGRES_USER=<username>
ENV POSTGRES_PASSWORD=<password>
[...]
```

> Note: The `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD` environment variables are required to initialize the database.
> 
> ⚠️ Do not forget to change the default values in the `Dockerfile` before building the Docker container.

## Initialization of Mojodex data

The `init-mojodex-data.sql` file contains the SQL scripts to create the Mojodex schema and data. You can modify this file to add or remove data.

This will create the following Mojodex config:
- user: `user@demo.com`
- password: `password`
- product: `demo`
- task: `meeting_recap`

You will be able to use the default user and password to connect to your assistant to check everything is working.


## Build

To build the Docker container, run the following command:

```bash
docker build -t mojodex-db .
```

## Usage

To initialize the database, run the following command:

```bash
docker run -d --name mojodex-db -p 5432:5432 mojodex-db
```

This will create a Docker container running a PostgreSQL database with the Mojodex schema and data.

## Troubleshooting

To check if the database is running, run the following command:

```bash
psql -h localhost -U <username> -d <database_name>
```

Then, use your password to connect to the database and look at the tables:

```sql
\dt
```

You should see the following tables:

```sql
                            List of relations
 Schema |                   Name                    | Type  |   Owner    
--------+-------------------------------------------+-------+------------
 public | md_calendar_suggestion                    | table | <your_user>
 public | md_company                                | table | <your_user>
 public | md_device                                 | table | <your_user>
 public | md_document                               | table | <your_user>
 public | md_document_chunk                         | table | <your_user>
 public | md_error                                  | table | <your_user>
 public | md_event                                  | table | <your_user>
 public | md_home_chat                              | table | <your_user>
 public | md_message                                | table | <your_user>
 public | md_platform                               | table | <your_user>
 public | md_predefined_action_displayed_data       | table | <your_user>
 public | md_produced_text                          | table | <your_user>
 public | md_produced_text_version                  | table | <your_user>
 public | md_product                                | table | <your_user>
 public | md_product_category                       | table | <your_user>
 public | md_product_category_displayed_data        | table | <your_user>
 public | md_product_displayed_data                 | table | <your_user>
 public | md_product_task                           | table | <your_user>
 public | md_purchase                               | table | <your_user>
 public | md_session                                | table | <your_user>
 public | md_task                                   | table | <your_user>
 public | md_task_displayed_data                    | table | <your_user>
 public | md_task_platform_association              | table | <your_user>
 public | md_task_predefined_action_association     | table | <your_user>
 public | md_task_tool_association                  | table | <your_user>
 public | md_task_tool_execution                    | table | <your_user>
 public | md_task_tool_query                        | table | <your_user>
 public | md_text_edit_action                       | table | <your_user>
 public | md_text_edit_action_displayed_data        | table | <your_user>
 public | md_text_edit_action_text_type_association | table | <your_user>
 public | md_text_type                              | table | <your_user>
 public | md_todo                                   | table | <your_user>
 public | md_todo_scheduling                        | table | <your_user>
 public | md_user                                   | table | <your_user>
 public | md_user_task                              | table | <your_user>
 public | md_user_task_execution                    | table | <your_user>
 public | md_user_vocabulary                        | table | <your_user>
```

## Entities
Each table is represented as a python class in `mojodex_code/entities.py`. This file is generated using `sqlacodegen`tool:
```bash
sqlacodegen postgresql+psycopg2://$DBUSER:$DBPASS@localhost:5432/$DBNAME --outfile mojodex_core/entities.py
```

## Go further

You can use the Mojodex API to create new users, products, tasks, etc.
See the [Mojodex API documentation](#) for more information.