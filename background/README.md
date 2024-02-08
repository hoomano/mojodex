# MOJODEX Background Backend

The background backend is responsible for processing data in the background.
It is useful for long-running process that would otherwise block the main backend (like using tools in tasks).
It is also useful for processing batch data (like sending emails or notifs to a group of users).

The background is a Flask application which routes can only be called by Mojodex's backend.

## Deployment
The background must be deployed in the same network as the backend so that the backend can call its routes but 
its routes must not be accessible from the outside.

The background app has its own Dockerfile and a requirements.txt file. It has some environment variables that must be set.

## Usage
When the background is called by backend to run a process, a "Cortex" associated to the task is created.
The role of the Cortex is to load all database data required for the process before running the process in a dedicated thread.
This is to avoid accessing the database in a thread that is not the main thread which could lead to database locks and issues.
