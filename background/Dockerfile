FROM python:3.10-buster

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

## FLASK
RUN apt-get update && apt-get install -y git

# dangerous but mojo-monitoring package is the only git project imported and not really at risk
ENV GIT_SSL_NO_VERIFY=true

COPY background/requirements.txt ./
RUN pip install -r requirements.txt


# Install Mojodex core
COPY ./mojodex_core /app/mojodex_core
COPY ./models.conf /app/mojodex_core/llm_engine/providers

WORKDIR /app/mojodex_core
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .


# Add app directory
COPY ./background/app /app
WORKDIR /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--preload","-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "app:app"]