# ![mojodex](/webapp/public/images/logo/mojodex_logo_4040.png) MOJODEX
[![](https://dcbadge.vercel.app/api/server/zJhWkwyS?style=flat)](https://discord.gg/4Dun59xwcX)
[![Twitter Follow](https://img.shields.io/twitter/follow/HoomanoCompany?style=social)](https://twitter.com/HoomanoCompany)


Mojodex is an open-source digital assistant platform to help companies and individuals build their own AI-powered assets.

It is designed to be task-oriented, configurable, and personalizable. Mojodex is API-centric, allowing for easy integration with other tools and is available as a web application, mobile application, and Chrome extension.

> __Our motivation is to help in creating a baseline on how to create enterprise level agents__

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

## Why Open-Sourcing Mojodex?

Mojodex was created to foster the adoption of digital assistants in businesses. The reasons for its open-source release are:

- Advancing Digital Assistant Usage : To support companies in making a lasting investment in artificial intelligence.

- Working on Own Processes : Configuring a digital assistant equates to refining a company's internal processes, promoting long-term development.

- User Expertise : Users are experts in their fields and are best suited to tailor their assistant to their needs.

- Trusted Platform : Providing an open-source platform for complete control over the assistant's ownership, development, hosting, and evolution.


## Frequently Asked Questions (FAQs)

### What makes the Mojodex open-source platform different from other GPT chat platforms or copilot platforms?

Beyond Chat : Unlike platforms that are solely chat-based, Mojodex is task-oriented, using conversation to achieve the goal of completing tasks and producing deliverables.

### What are the benefits of using Mojodex over other platforms?

- Control Over Investment : Being open-source, it allows for the creation of custom prompts and working on proprietary processes, rather than sending them to an uncontrolled platform.

- Ease of Integration : The assistant's API-centric architecture facilitates seamless integration with existing tools.

### How about the data privacy and security?

- Data Flow Mastery : Complete control over data flows, especially towards large language models, enabling users to connect their proprietary LLM solutions and fully manage the data stream.

- Hosting on Own Infrastructure : For sensitive data, hosting on personal infrastructure provides total control.

### What can I do with the data generated by Mojodex?

Users own their data, allowing the construction of interaction datasets at an enterprise scale, which are invaluable for retraining on specific use cases.

