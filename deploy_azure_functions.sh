# Azure Functions deployment (Alternative to App Service)
# This is a serverless option for the AI Agent

# Function App Configuration
FUNCTION_APP_NAME=ai-agent-function
STORAGE_ACCOUNT=aiagentstorage
RESOURCE_GROUP=ai-agent-rg
LOCATION=eastus

# Create Storage Account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP \
  --sku Standard_LRS

# Create Function App
az functionapp create \
  --resource-group $RESOURCE_GROUP \
  --consumption-plan-location $LOCATION \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name $FUNCTION_APP_NAME \
  --storage-account $STORAGE_ACCOUNT \
  --os-type Linux

# Configure App Settings
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group $RESOURCE_GROUP \
  --settings \
    AZURE_OPENAI_ENDPOINT=$AZURE_OPENAI_ENDPOINT \
    AZURE_OPENAI_API_KEY=$AZURE_OPENAI_API_KEY \
    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4 \
    AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Deploy
func azure functionapp publish $FUNCTION_APP_NAME
