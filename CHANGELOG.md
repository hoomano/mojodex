# Mojodex Changelog

## 2024-07: 0.4.12

### Deployment

**New secret [MOJODEX_WEBAPP_SECRET] for Webapp calls to Backend routes**:

1. Add ARG docker variable to `webapp`:

```docker-compose.yaml
    
  mojodex-webapp:
    build:
      context: ./webapp
      args:
        - SOCKETIO_URI=http://localhost:5001 # use defaut for local execution
        - TERMS_URI= # optional
        - PRIVACY_URI= # optional
        - CHROME_EXTENSION_ID= # optional
        - MOJODEX_WEBAPP_SECRET=webapp_secret # use defaut for local execution
```

2. Add ENV variable to `backend`

```.env
############################################
# Secrets - this is important to set your own and keep them secret
############################################

ENCODING_ALGORITHM=HS256
MOJODEX_SCHEDULER_SECRET=scheduler_secret
FLASK_SECRET_KEY=flask_secret_key
BACKOFFICE_SECRET=backoffice_secret
JWT_SECRET=jwt_secret
MOJODEX_BACKGROUND_SECRET=background_secret
PURCHASE_UPDATER_SOCKETIO_SECRET=purchase_updater_socketio_secret
RESET_PASSWORD_JWT_SECRET=reset_password_jwt_secret
RESET_PASSWORD_SECRET_KEY=reset_password_secret_key
NEXT_AUTH_JWT_SECRET=next_auth_jwt_secret
TOKEN_SECRET_SPLITTER=__mojodex__
MOJODEX_WEBAPP_SECRET=webapp_secret

```
