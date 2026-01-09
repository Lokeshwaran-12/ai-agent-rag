#!/bin/bash

# Azure Deployment Script for AI Agent RAG System
# This script deploys the application to Azure App Service

set -e

echo "=== Azure Deployment Script ==="
echo ""

# Configuration
RESOURCE_GROUP="ai-agent-rg"
LOCATION="eastus"
APP_SERVICE_PLAN="ai-agent-plan"
WEB_APP_NAME="ai-agent-rag-app"  # Must be globally unique
RUNTIME="PYTHON:3.11"

echo "Step 1: Login to Azure"
echo "Run: az login"
echo ""

echo "Step 2: Create Resource Group"
echo "az group create --name $RESOURCE_GROUP --location $LOCATION"
echo ""

echo "Step 3: Create App Service Plan"
echo "az appservice plan create \\"
echo "  --name $APP_SERVICE_PLAN \\"
echo "  --resource-group $RESOURCE_GROUP \\"
echo "  --sku B1 \\"
echo "  --is-linux"
echo ""

echo "Step 4: Create Web App"
echo "az webapp create \\"
echo "  --resource-group $RESOURCE_GROUP \\"
echo "  --plan $APP_SERVICE_PLAN \\"
echo "  --name $WEB_APP_NAME \\"
echo "  --runtime \"$RUNTIME\" \\"
echo "  --deployment-local-git"
echo ""

echo "Step 5: Configure Environment Variables"
echo "az webapp config appsettings set \\"
echo "  --resource-group $RESOURCE_GROUP \\"
echo "  --name $WEB_APP_NAME \\"
echo "  --settings \\"
echo "    AZURE_OPENAI_ENDPOINT=\$AZURE_OPENAI_ENDPOINT \\"
echo "    AZURE_OPENAI_API_KEY=\$AZURE_OPENAI_API_KEY \\"
echo "    AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4 \\"
echo "    AZURE_OPENAI_API_VERSION=2024-02-15-preview \\"
echo "    AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002 \\"
echo "    ENVIRONMENT=production \\"
echo "    LOG_LEVEL=INFO"
echo ""

echo "Step 6: Configure Startup Command"
echo "az webapp config set \\"
echo "  --resource-group $RESOURCE_GROUP \\"
echo "  --name $WEB_APP_NAME \\"
echo "  --startup-file \"uvicorn app.main:app --host 0.0.0.0 --port 8000\""
echo ""

echo "Step 7: Deploy Code"
echo "Option A - Using ZIP deployment:"
echo "  zip -r app.zip app/ data/ requirements.txt"
echo "  az webapp deployment source config-zip \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --name $WEB_APP_NAME \\"
echo "    --src app.zip"
echo ""
echo "Option B - Using Git deployment:"
echo "  git remote add azure \$(az webapp deployment source config-local-git \\"
echo "    --resource-group $RESOURCE_GROUP \\"
echo "    --name $WEB_APP_NAME \\"
echo "    --query url --output tsv)"
echo "  git push azure main"
echo ""

echo "Step 8: Enable Application Insights (Optional)"
echo "az monitor app-insights component create \\"
echo "  --app ai-agent-insights \\"
echo "  --location $LOCATION \\"
echo "  --resource-group $RESOURCE_GROUP"
echo ""

echo "Step 9: Get Application URL"
echo "echo \"Application URL: https://\${WEB_APP_NAME}.azurewebsites.net\""
echo ""

echo "=== Deployment Instructions Complete ==="
echo ""
echo "To execute these commands, copy them one by one or create a script."
echo "Make sure to replace environment variable values with your actual Azure OpenAI credentials."
