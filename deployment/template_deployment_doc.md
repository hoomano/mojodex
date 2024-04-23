# Azure deployment

LOCATION=[LOCATION]
RESOURCE_GROUP_NAME=[RESOURCE_GROUP_NAME]
APP_SERVICE_PLAN_NAME=[APP_SERVICE_PLAN_NAME]


## Backend
REGISTRY_NAME=[REGISTRY_NAME]
image=[backend_image]
APP_SERVICE_NAME=[BACKEND_APP_SERVICE_NAME]
tag=mojodex_$(date +%d-%m-%Y"_"%H_%M_%S)

#### To update backend webapp. 
1. Within mojodex_github project, run:
> az acr build --registry $REGISTRY_NAME --resource-group $RESOURCE_GROUP_NAME --image ${image}:${tag} . --file ./backend/Dockerfile
2. On Azure portal, go to the backend app service, deployment center, select the tag you just deployed and save.

#### To check logs:
> az webapp log tail --name $APP_SERVICE_NAME  --resource-group $RESOURCE_GROUP_NAME

## Background_backend
REGISTRY_NAME=[REGISTRY_NAME]
image=[background_image]
APP_SERVICE_NAME=[BACKGROUND_APP_SERVICE_NAME]
tag=mojodex_$(date +%d-%m-%Y"_"%H_%M_%S)

1. Within mojodex_github project, run:
> az acr build --registry $REGISTRY_NAME --resource-group $RESOURCE_GROUP_NAME --image ${image}:${tag}  . --file ./background/Dockerfile
2. On Azure portal, go to the background app service, deployment center, select the tag you just deployed and save.

#### To check logs:
> az webapp log tail --name $APP_SERVICE_NAME  --resource-group $RESOURCE_GROUP_NAME

## Webapp
REGISTRY_NAME=[REGISTRY_NAME]
image=[webapp_image]
APP_SERVICE_NAME=[WEBAPP_APP_SERVICE_NAME]
tag=mojodex_$(date +%d-%m-%Y"_"%H_%M_%S)

1. Within mojodex_github project, run:
> az acr build --registry $REGISTRY_NAME --image ${image}:${tag} ./webapp --build-arg SOCKETIO_URI=[BACKEND_URL] --build-arg TERMS_URI= --build-arg PRIVACY_URI= --build-arg CHROME_EXTENSION_ID=
2. On Azure portal, go to the background app service, deployment center, select the tag you just deployed and save.

#### To check logs:
> az webapp log tail --name $APP_SERVICE_NAME  --resource-group $RESOURCE_GROUP_NAME


## PGSQL
DB_SERVER_NAME=[DB_SERVER_NAME]
DB_NAME=[DB_NAME]
ADMIN_USERNAME=[ADMIN_USERNAME]
ADMIN_PWD=[DB_PASS]
DB_HOST=[DB_HOST]

#### To interact with the database:
> az postgres flexible-server connect -n $DB_SERVER_NAME -u $ADMIN_USERNAME --interactive
#### To execute a sql file:
> az postgres flexible-server execute -n $DB_SERVER_NAME -u $ADMIN_USERNAME -p $ADMIN_PWD -d $DB_NAME --file-path
#### To dump the database:
> pg_dump -U  $ADMIN_USERNAME -d $DB_NAME -h $DB_HOST | gzip -9 > dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql.gz