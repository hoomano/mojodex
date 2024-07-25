# Web App

The Mojodex web app is a web application that allows you to interact with the Mojodex API.

## Structure

The web app is composed of:
- A frontend written in React.js
- A backend proxy written in Node.js

The frontend is served by the backend proxy, which also serves as a reverse proxy to the Mojodex API for REST requests.

> IMPORTANT NOTE: For now, Socketio requests are not proxied by the backend. This means that the frontend must connect directly to the Mojodex API for socketio requests.