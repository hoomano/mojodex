# Open AI

Setup the API key in your `.env` file:

```bash
OPENAI_API_KEY=your-api-key
```

!!! note "Switching from OpenAI to Azure OpenAI Services"
    This is made easy by changing the `MAIN_MODEL_API_TYPE` in your `.env` file.

## Setup a backup engine

To avoid facing ratio / quota limitations, there is a backup engine that can be used. This is set in the `.env` file:

```bash
# GPT4 - gpt-4-32k - Optional - Backup model used in case of reached rate limit with GPT4-TURBO
BACKUP_MODEL_API_TYPE=azure # or "openai"
```

You can specify the provider to use as a backup in case the main provider reaches its rate limit by configuring the appropriate section in the `.env` file.
    

## Coverage

GPT4-Turbo has been used to develop the entire Mojodex platform. The coverage is complete.

