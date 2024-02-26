# ![mojodex](/webapp/public/images/logo/mojodex_logo_4040.png) MOJODEX
[![](https://dcbadge.vercel.app/api/server/zJhWkwyS?style=flat)](https://discord.gg/4Dun59xwcX)
[![Twitter Follow](https://img.shields.io/twitter/follow/HoomanoCompany?style=social)](https://twitter.com/HoomanoCompany)


Mojodex is an open-source digital assistant platform to help companies and individuals build their own AI-powered assets.

It is designed to be task-oriented, configurable, and personalizable. Mojodex is API-centric, allowing for easy integration with other tools and is available as a web application, mobile application, and Chrome extension.

📚 Complete doc here: [https://hoomano.github.io/mojodex/](https://hoomano.github.io/mojodex/)

> __Our motivation is to help companies build enterprise level agents__

## Demo

[![Mojodex Demo](https://img.youtube.com/vi/9m7AZdd5Qyw/0.jpg)](https://www.youtube.com/watch?v=9m7AZdd5Qyw)

## What's in it?

| Link to the repo | Description | Live Demo Version |
| --- | --- | --- |
| [Plaform Core (this repo)](https://github.com/hoomano/mojodex) | [Open-source NextJS](/webapp), [Python backend](backend), [PostgreSQL database](/pgsql) and more, including the [webapp](/webapp/) convenient for laptop usage. | [https://mojodex.hoomano.com](https://mojodex.hoomano.com) |
| [Mobile app](https://github.com/hoomano/mojodex_mobile) | Open-source Flutter app that allows users to interact with the digital assistant on the go - mainly voice interaction. | [![App Store](/webapp/public/images/app_store.svg)](https://apps.apple.com/fr/app/mojodex/id6446367743) [![Google Play](/webapp/public/images/google_play.svg)](https://play.google.com/store/apps/details?id=com.hoomano.mojodex_mobile) |
| Chrome extension (soon) | Open-source Chrome extension project to access the digital assistant directly from the browser.  | [![Chrome Web Store](/docs/images/chrome_web_store.png)](https://chromewebstore.google.com/detail/mojodex/jagemmajllamdahinjidkopehkffbkho)

__Here we go!__

## Quick Start

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
Edit the .env file and set your OpenAI API key:

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

- **Task-Oriented** : Mojodex is designed to assist users by completing specific tasks, making it easier for the assistant to understand and fulfill user needs.

- **Configurable** : Tailored to various professional uses, allowing for role-specific task configurations (sales, recruitment, personal assistance, etc.).

- **Personalizable** : Builds a memory of user interactions and goals to improve task execution.

- **Proactive** : Independently manages tasks, freeing users to focus on other activities through a chat-independent architecture.

- **Multiple User Interfaces** : Includes a web application in this repository, an open-source mobile application, and a Chrome extension.

- **API-Centric Back-End** : Enables easy integration with other tools through a well-defined API exposure.

- **Using OpenAI's GPT-4 Turbo** : Accessible directly via OpenAI or through Azure's functionalities.