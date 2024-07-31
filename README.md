# ![mojodex](/webapp/public/images/logo/mojodex_logo_4040.png) MOJODEX

Mojodex is an open-source digital assistant platform to help companies and individuals build their own AI-powered assets.

It is designed to be task-oriented, configurable, and personalizable. Mojodex is API-centric, allowing for easy integration with other tools and is available as a web application, mobile application, and Chrome extension.

📚 Complete doc here: [https://hoomano.github.io/mojodex/](https://hoomano.github.io/mojodex/)

> __Our motivation is to help companies build enterprise level agents__

## Demo

[![Mojodex Demo](https://img.youtube.com/vi/9m7AZdd5Qyw/0.jpg)](https://www.youtube.com/watch?v=9m7AZdd5Qyw)

## What's in it?

| Link to the repo                                               | Description                                                                                                                                                     | Live Demo Version                                                                                                                                                                                                                         |
| -------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [Plaform Core (this repo)](https://github.com/hoomano/mojodex) | [Open-source NextJS](/webapp), [Python backend](backend), [PostgreSQL database](/pgsql) and more, including the [webapp](/webapp/) convenient for laptop usage and the [CLI](/cli) (yes a CLI 💻). | [https://mojodex.hoomano.com](https://mojodex.hoomano.com)                                                                                                                                                                                |
| [Mobile app](https://github.com/hoomano/mojodex_mobile)        | Open-source Flutter app that allows users to interact with the digital assistant on the go - mainly voice interaction.                                          | [![App Store](/webapp/public/images/app_store.svg)](https://apps.apple.com/fr/app/mojodex/id6446367743) [![Google Play](/webapp/public/images/google_play.svg)](https://play.google.com/store/apps/details?id=com.hoomano.mojodex_mobile) |
| Chrome extension (soon)                                        | Open-source Chrome extension project to access the digital assistant directly from the browser.                                                                 | [![Chrome Web Store](/docs/images/chrome_web_store.png)](https://chromewebstore.google.com/detail/mojodex/jagemmajllamdahinjidkopehkffbkho)                                                                                               |

__Here we go!__

## Quick Start: 3-steps installation of the Mojodex platform

See the installation video guide here: https://youtu.be/86_S_cXhhTA

STEP 1: Clone the repository

```bash
git clone https://github.com/hoomano/mojodex.git
cd mojodex
```

STEP 2: Set up your OpenAI API key in the .env file

```bash
cp .env.example .env
```
Edit the models.conf, stt_models.conf and embedding_models.conf file and set your OpenAI API key (or any LLM provider's credentials):

```bash
[...]
OPENAI_API_KEY=<your_openai_api_key>
[...]
```


STEP 3: Start the Mojodex services

```bash
docker compose up -d --build
```

STEP 4: Access the Mojodex web app

> 🎉 Congratulations
> 
> Open your web browser and go to [http://localhost:3000](http://localhost:3000)
> 
> Login with the default user: `demo@example.com` and password: `demo`


## Mojodex Mobile

For a complete experience, you can also build and use the open-source Mojodex mobile app.

> ℹ Mojodex Mobile is an open-source Flutter app
>
> 👉 [Open GitHub repo](https://github.com/hoomano/mojodex_mobile)
>
> Join us on [Discord](https://discord.gg/zJhWkwyS) to get the latest updates.

## Key Features

- **Task-Oriented** : Mojodex is designed to assist final users by completing specific tasks, making it easier for the assistant to understand and fulfill user needs.

- **Configurable** : Easy to tailor to any professional uses, allowing for role-specific task configurations (sales, recruitment, personal assistance, etc.).

- **Personalizable** : Built-in memory of user interactions and goals to improve task execution.

- **Proactive** : Independently organizing todos from tasks, freeing users to focus on other activities through a multi-platform architecture.

- **Multiple User Interfaces** : Includes a web application in this repository, an open-source mobile application, and a CLI (yes, a CLI).

- **API-Centric Back-End** : Enables easy customization and integration with other tools through a well-defined API exposure.

- **Multi-LLM** : Take the most of any model. Designed to be working with state of the art models, and customizability to adjust to any LLM

## Documentation

Access the complete documentation online: https://hoomano.github.io/mojodex

or Run the documentation locally

```
mkdocs serve
```

Browse the doc from your browser

## Contribution

How do you want the project to move forward? 
Open an issue an let us know.
