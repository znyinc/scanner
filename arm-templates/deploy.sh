#!/bin/bash

# Azure Stock Scanner Deployment Script
# Usage: ./deploy.sh [environment] [resource-group-name]

set -e

# Configuration
ENVIRONMENT=${1:-"dev"}
RESOURCE_GROUP=${2:-"rg-stockscanner-$ENVIRONMENT"}
LOCATION=${3:-"eastus2"}
TEMPLATE_FILE="azuredeploy.json"
PARAMETERS_FILE="azuredeploy.parameters.$ENVIRONMENT.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate parameters
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment. Must be 'dev', 'staging', or 'prod'"
    exit 1
fi

# Check if parameters file exists
if [ ! -f "$PARAMETERS_FILE" ]; then
    log_error "Parameters file '$PARAMETERS_FILE' not found"
    exit 1
fi

log_info "Starting deployment for environment: $ENVIRONMENT"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "Location: $LOCATION"

# Check if user is logged in to Azure
if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Get current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
log_info "Using subscription: $SUBSCRIPTION"

# Confirm deployment
read -p "$(echo -e ${YELLOW}Are you sure you want to deploy to $ENVIRONMENT environment? [y/N]: ${NC})" -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log_info "Deployment cancelled"
    exit 0
fi

# Create resource group if it doesn't exist
log_info "Checking if resource group exists..."
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    log_info "Creating resource group: $RESOURCE_GROUP"
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    log_success "Resource group created"
else
    log_info "Resource group already exists"
fi

# Validate ARM template
log_info "Validating ARM template..."
az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$TEMPLATE_FILE" \
    --parameters "@$PARAMETERS_FILE"

if [ $? -eq 0 ]; then
    log_success "Template validation passed"
else
    log_error "Template validation failed"
    exit 1
fi

# Deploy the template
log_info "Starting deployment..."
DEPLOYMENT_NAME="stockscanner-deployment-$(date +%Y%m%d-%H%M%S)"

az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$TEMPLATE_FILE" \
    --parameters "@$PARAMETERS_FILE" \
    --name "$DEPLOYMENT_NAME" \
    --verbose

if [ $? -eq 0 ]; then
    log_success "Deployment completed successfully!"
    
    # Get deployment outputs
    log_info "Retrieving deployment outputs..."
    
    BACKEND_URL=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$DEPLOYMENT_NAME" \
        --query properties.outputs.backendUrl.value -o tsv)
    
    FRONTEND_URL=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$DEPLOYMENT_NAME" \
        --query properties.outputs.frontendUrl.value -o tsv)
    
    DATABASE_FQDN=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$DEPLOYMENT_NAME" \
        --query properties.outputs.databaseFqdn.value -o tsv)
    
    CONTAINER_REGISTRY_URL=$(az deployment group show \
        --resource-group "$RESOURCE_GROUP" \
        --name "$DEPLOYMENT_NAME" \
        --query properties.outputs.containerRegistryUrl.value -o tsv)
    
    # Display results
    echo
    log_success "Deployment Summary:"
    echo "===================="
    echo "Environment: $ENVIRONMENT"
    echo "Resource Group: $RESOURCE_GROUP"
    echo "Backend URL: $BACKEND_URL"
    echo "Frontend URL: $FRONTEND_URL"
    echo "Database FQDN: $DATABASE_FQDN"
    echo "Container Registry: $CONTAINER_REGISTRY_URL"
    echo
    
    # Post-deployment steps
    log_info "Post-deployment steps:"
    echo "1. Build and push Docker images to the container registry"
    echo "2. Configure custom domain if needed"
    echo "3. Set up SSL certificates"
    echo "4. Configure monitoring alerts"
    echo "5. Test application functionality"
    echo
    
    # Check application health
    log_info "Checking application health (this may take a few minutes)..."
    sleep 30
    
    if curl -f -s "$BACKEND_URL/health" > /dev/null; then
        log_success "Backend health check passed"
    else
        log_warning "Backend health check failed - this is normal for new deployments"
    fi
    
    if curl -f -s "$FRONTEND_URL" > /dev/null; then
        log_success "Frontend availability check passed"
    else
        log_warning "Frontend availability check failed - this is normal for new deployments"
    fi
    
else
    log_error "Deployment failed"
    exit 1
fi

log_success "Deployment script completed!"