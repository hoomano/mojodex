# Azure deployment

## Services
To deploy Mojodex on Azure Cloud, here is a list of required services:

### Azure Container Registry
Your registry will contain the Docker images of Mojodex:
- backend
- background
- webapp

### App Service Plan
The App Service Plan will be useful to create 3 App Services - cf next section.

### App Services
3 App Services will be created:
- backend
- background
- webapp

### Container instances
A container instance will be created to run the scheduler.

### Storage Account (File Share)
A storage account will be used as volume for the backend and background services.
It will store users data.

### PostgreSQL flexible server
A PostgreSQL flexible server will be used for Mojodex database.

## Deploying on Azure for the first time

### Pre-requesites
- Install Azure CLI
- Login to your Azure account
```bash
az login
```
- Set your active subscription
```bash
az account set --subscription <subscription_id>
```

To deploy on Azure for the first time, we've made a script for you. Here is the process:

1. Check environment variables defined in `deployment/azure_env_variables` files. Set your secrets.
2. Set your own models providers credentials in models confs files.
3. In the script `deployment/azure_deployment_script.sh`, check that every names and sku fit your needs.
4. Launch the script from deployment folder
```bash
cd deployment
sh azure_deployment_script.sh
```

> You will be prompted for: 
> - DATABASE password
> - Scheduler secret
> Other secrets are defined in environment variables files.

After the script is done, you may have to restart the services from the portal to ensure everything is up and running with full configuration.
When everything is up, you can access the webapp from its url.

## Updating the existing Azure deployment
The documentation to update your existing Azure deployment is available in `deployment/azure-deployment-commands.md` once you've run the first deployment script.