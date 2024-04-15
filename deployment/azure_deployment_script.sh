webapppath="../webapp"
backendwebpath="../backend"
backgroundpath="../background"
schedulerpath="../scheduler"
pgsqlpath="../pgsql"
datalocalpath="../data"

echo "Database password:"
read DB_PASS

echo "Scheduler secret:"
read scheduler_secret


LOCATION="westeurope"
resourceGroup="mojodex-rg"
appServicePlan="mojodex-plan"
registry="mojodexregistry"
backendWebApp="mojodex-backend"
backgroundWebApp="mojodex-background"
webApp="mojodex-webapp"
schedulerContainerInstance="mojodex-scheduler"
webappImage="mojodex_webapp"
backendImage="mojodex_backend"
backgroundImage="mojodex_background"
schedulerImage="mojodex_scheduler"
STORAGE_ACCOUNT_NAME="mojodexstorage"
PG_SERVER_NAME='mojodex-pgsql'
DB_NAME="MojodexBackend"
DB_USER="mojoserver"
tag=mojodex_$(date +%d-%m-%Y"_"%H_%M_%S)

# Check if that fits your needs
APP_SERVICE_PLAN_SKU="P1v2"
REGISTRY_SKU="Basic"
PG_SERVER_SKU="Standard_B1ms"
STORAGE_ACCOUNT_SKU="Standard_LRS"


## Optional
TERMS_URI=""
PRIVACY_URI=""
CHROME_EXTENSION_ID=""

# Create a resource group
echo "Creating $resourceGroup"
az group create --name $resourceGroup --location $LOCATION

# Create an App Service plan
echo "Creating $appServicePlan"
az appservice plan create --name $appServicePlan --resource-group $resourceGroup --is-linux --location $LOCATION --sku $APP_SERVICE_PLAN_SKU

# Create a container registry
echo "Creating $registry"
az acr create --resource-group $resourceGroup --name $registry --sku $REGISTRY_SKU --location $LOCATION --admin-enabled true

# wait 15 minutes for the registry to be created
sleep 900

registryId=$(az acr show --resource-group $resourceGroup --name $registry --query id --output tsv)
registryuser=`az acr credential show -n $registry --query username -o tsv`
registrypassword=`az acr credential show -n $registry --query 'passwords[0].value' -o tsv`



# Deploy webapps
echo "Sending backend image to $registry"
az acr build --registry $registry --resource-group $resourceGroup --image ${backendImage}:${tag} .. --file $backendwebpath/Dockerfile
echo "Creating $backendWebApp"
az webapp create --name $backendWebApp --resource-group $resourceGroup --plan $appServicePlan \
  --assign-identity --deployment-container-image-name $registry.azurecr.io/${backendImage}:${tag} -s $registryuser -w $registrypassword
urlBackend=`az webapp config hostname list --resource-group $resourceGroup --webapp-name $backendWebApp --query '[0].{Value:name}' -o tsv`


echo "Sending background image to $registry"
az acr build --registry $registry --resource-group $resourceGroup --image ${backgroundImage}:${tag} .. --file $backgroundpath/Dockerfile
echo "Creating $backgroundWebApp"
az webapp create --name $backgroundWebApp --resource-group $resourceGroup --plan $appServicePlan \
  --assign-identity --deployment-container-image-name $registry.azurecr.io/${backgroundImage}:${tag} -s $registryuser -w $registrypassword
urlBackground=`az webapp config hostname list --resource-group $resourceGroup --webapp-name $backgroundWebApp --query '[0].{Value:name}' -o tsv`

echo "Sending webapp image to $registry"
az acr build --registry $registry --resource-group $resourceGroup --image ${webappImage}:${tag} $webapppath --build-arg SOCKETIO_URI=https://$urlBackend --build-arg TERMS_URI=$TERMS_URI --build-arg PRIVACY_URI=$PRIVACY_URI --build-arg CHROME_EXTENSION_ID=$CHROME_EXTENSION_ID
echo "Creating $webApp"
az webapp create --name $webApp --resource-group $resourceGroup --plan $appServicePlan \
  --assign-identity --deployment-container-image-name $registry.azurecr.io/${webappImage}:${tag} -s $registryuser -w $registrypassword
urlWebApp=`az webapp config hostname list --resource-group $resourceGroup --webapp-name $webApp --query '[0].{Value:name}' -o tsv`

# Create a container instance for the scheduler
echo "Sending scheduler image to $registry"
az acr build --registry $registry --resource-group $resourceGroup --image ${schedulerImage}:${tag} $schedulerpath --file $schedulerpath/Dockerfile
echo "Creating $schedulerContainerInstance"
az container create --resource-group $resourceGroup --name $schedulerContainerInstance --image $registry.azurecr.io/${schedulerImage}:${tag} --registry-login-server $registry.azurecr.io --registry-username $registryuser --registry-password $registrypassword --environment-variables "MOJODEX_BACKEND_URI=https://$urlBackend" "MOJODEX_SCHEDULER_SECRET=$scheduler_secret"


# Create storage account
echo "Creating storage account"
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group $resourceGroup \
  --location $LOCATION \
  --sku $STORAGE_ACCOUNT_SKU \
  --kind StorageV2
STORAGE_ACCOUNT_KEY=`az storage account keys list -g $resourceGroup -n $STORAGE_ACCOUNT_NAME --query '[0].{Value:value}' -o tsv`

# Create fileshare
echo "Creating fileshare"
az storage share create --account-name $STORAGE_ACCOUNT_NAME --account-key $STORAGE_ACCOUNT_KEY --name $STORAGE_ACCOUNT_NAME-fileshare

# Populate fileshare
echo "Populating fileshare"
az storage file upload-batch --destination $STORAGE_ACCOUNT_NAME-fileshare --source $datalocalpath \
  --account-name $STORAGE_ACCOUNT_NAME --account-key $STORAGE_ACCOUNT_KEY
az storage directory create --name "users" --account-key $STORAGE_ACCOUNT_KEY --account-name $STORAGE_ACCOUNT_NAME --share-name $STORAGE_ACCOUNT_NAME-fileshare

# Add storage account to webapps backend and background as volume (Azure Storage Mount)
echo "Adding storage account to webapps"
az webapp config storage-account add -g $resourceGroup -n $backendWebApp \
  --custom-id CustomId \
  --storage-type AzureFiles \
  --account-name $STORAGE_ACCOUNT_NAME \
  --share-name $STORAGE_ACCOUNT_NAME-fileshare \
  --access-key $STORAGE_ACCOUNT_KEY \
 --mount-path /data

az webapp config storage-account add -g $resourceGroup -n $backgroundWebApp \
  --custom-id CustomId \
  --storage-type AzureFiles \
  --account-name $STORAGE_ACCOUNT_NAME \
  --share-name $STORAGE_ACCOUNT_NAME-fileshare \
  --access-key $STORAGE_ACCOUNT_KEY \
  --mount-path /data

# Create Postgres server
echo "Creating Postgres server"
az postgres flexible-server create --location $LOCATION --resource-group  $resourceGroup \
  --name $PG_SERVER_NAME --admin-user $DB_USER --admin-password $DB_PASS \
  --sku-name $PG_SERVER_SKU  --public-access all  \
  --tier Burstable

# Creating DB
echo "Creating DB"
az postgres flexible-server db create --database-name $DB_NAME --resource-group $resourceGroup --server-name $PG_SERVER_NAME


#defining appsettings
echo "Defining appsettings"
az webapp config appsettings set --resource-group $resourceGroup --name $backendWebApp --settings @azure_env_variables/settingsbackend.json
az webapp config appsettings set --resource-group $resourceGroup --name $backgroundWebApp --settings @azure_env_variables/settingsbackground.json

az webapp config appsettings set --name $webApp --resource-group $resourceGroup --settings MOJODEX_BACKEND_URI="https://$urlBackend"
az webapp config appsettings set --name $backendWebApp --resource-group $resourceGroup --settings BACKGROUND_BACKEND_URI="https://$urlBackground"
az webapp config appsettings set --name $backgroundWebApp --resource-group $resourceGroup --settings MOJODEX_BACKEND_URI="https://$urlBackend"

#echo "Defining log settings"
az webapp log config --resource-group $resourceGroup --name $webApp --application-logging filesystem --docker-container-logging  filesystem --web-server-logging filesystem
az webapp log config --resource-group $resourceGroup --name $backendWebApp --application-logging filesystem --docker-container-logging  filesystem --web-server-logging filesystem
az webapp log config --resource-group $resourceGroup --name $backgroundWebApp --application-logging filesystem --docker-container-logging  filesystem --web-server-logging filesystem

az webapp config appsettings set --name $backendWebApp --resource-group $resourceGroup --settings MOJODEX_SCHEDULER_SECRET=$scheduler_secret

# DB
# then apply creation scripts to DB
echo "Initializing DB"
az postgres flexible-server parameter set --resource-group $resourceGroup  --server-name $PG_SERVER_NAME --name azure.extensions --value VECTOR
az postgres flexible-server execute -n $PG_SERVER_NAME -u $DB_USER -p $DB_PASS -d $DB_NAME --file-path $pgsqlpath/create-mojodex-db.sql
az postgres flexible-server execute -n $PG_SERVER_NAME -u $DB_USER -p $DB_PASS -d $DB_NAME --file-path $pgsqlpath/init-mojodex-data.sql

DB_HOST=`az postgres flexible-server show --resource-group $resourceGroup --name $PG_SERVER_NAME --query fullyQualifiedDomainName -o tsv`

az webapp config appsettings set --name $backendWebApp --resource-group $resourceGroup --settings DBHOST=$DB_HOST
az webapp config appsettings set --name $backendWebApp --resource-group $resourceGroup --settings DBNAME=$DB_NAME
az webapp config appsettings set --name $backendWebApp --resource-group $resourceGroup --settings DBUSER=$DB_USER
az webapp config appsettings set --name $backendWebApp --resource-group $resourceGroup --settings DBPASS=$DB_PASS

az webapp config appsettings set --name $backgroundWebApp --resource-group $resourceGroup --settings DBHOST=$DB_HOST
az webapp config appsettings set --name $backgroundWebApp --resource-group $resourceGroup --settings DBNAME=$DB_NAME
az webapp config appsettings set --name $backgroundWebApp --resource-group $resourceGroup --settings DBUSER=$DB_USER
az webapp config appsettings set --name $backgroundWebApp --resource-group $resourceGroup --settings DBPASS=$DB_PASS


echo "Preparing documentation"
sed -e "s/\[LOCATION\]/$LOCATION/g;
s/\[RESOURCE_GROUP_NAME\]/$resourceGroup/g;
s/\[APP_SERVICE_PLAN_NAME\]/$appServicePlan/g;
s/\[REGISTRY_NAME\]/$registry/g;
s/\[backend_image\]/$backendImage/g;
s/\[BACKEND_APP_SERVICE_NAME\]/$backendWebApp/g;
s/\[background_image\]/$backgroundImage/g;
s/\[BACKGROUND_APP_SERVICE_NAME\]/$backgroundWebApp/g;
s/\[webapp_image\]/$webappImage/g;
s/\[WEBAPP_APP_SERVICE_NAME\]/$webApp/g;
s/\[BACKEND_URL\]/$urlBackend/g;
s/\[DB_HOST\]/$DB_HOST/g;
s/\[DB_SERVER_NAME\]/$PG_SERVER_NAME/g;
s/\[DB_NAME\]/$DB_NAME/g;
s/\[ADMIN_USERNAME\]/$DB_USER/g;
" ./template_deployment_doc.md > ./azure-deployment-commands.md

echo "All done. Please check no problem occurred in previous log. Your personalized documentation is available in ./azure-deployment-commands.md"