FROM python:3.9-buster

EXPOSE 5000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

## FLASK
RUN apt-get update && apt-get install -y git

## FFMPEG
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg

# dangerous but mojo-monitoring package is the only git project imported and not really at risk
ENV GIT_SSL_NO_VERIFY=true

COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

# Playwright dependencies
RUN apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libatspi2.0-0 libxcomposite1 libgbm1

# Install Mojodex core
COPY ./mojodex_core /app/mojodex_core
COPY ./models.conf /app/mojodex_core/llm_engine/providers
COPY ./embedding_models.conf /app/mojodex_core/embedder
COPY ./stt_models.conf /app/mojodex_core/stt
WORKDIR /app/mojodex_core
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .

# Add app directory
COPY ./backend/app /app
WORKDIR /app


# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
RUN playwright install

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--worker-class", "eventlet", "app:app"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--preload","-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "app:app"]
