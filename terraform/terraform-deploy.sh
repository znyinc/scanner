#!/bin/bash

# Terraform Azure Deployment Script for Stock Scanner
# Usage: ./terraform-deploy.sh [environment] [action]

set -e

# Configuration
ENVIRONMENT=${1:-"dev"}
ACTION=${2:-"plan"}
TERRAFORM_VERSION="1.5.0"

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

show_usage() {
    echo "Usage: $0 [environment] [action]"
    echo ""
    echo "Arguments:"
    echo "  environment: dev, staging, or prod (default: dev)"
    echo "  action: plan, apply, destroy, init (default: plan)"
    echo ""
    echo "Examples:"
    echo "  $0 dev plan       # Plan deployment for dev environment"
    echo "  $0 prod apply     # Apply deployment for prod environment"
    echo "  $0 dev destroy    # Destroy dev environment"
    echo ""
}

# Validate parameters
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment. Must be 'dev', 'staging', or 'prod'"
    show_usage
    exit 1
fi

if [[ ! "$ACTION" =~ ^(plan|apply|destroy|init|validate)$ ]]; then
    log_error "Invalid action. Must be 'plan', 'apply', 'destroy', 'init', or 'validate'"
    show_usage
    exit 1
fi

# Check if tfvars file exists
TFVARS_FILE="terraform.tfvars.$ENVIRONMENT"
if [ ! -f "$TFVARS_FILE" ]; then
    log_error "Terraform variables file '$TFVARS_FILE' not found"
    exit 1
fi

log_info "Starting Terraform $ACTION for environment: $ENVIRONMENT"

# Check prerequisites
log_info "Checking prerequisites..."

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    log_error "Terraform is not installed. Please install Terraform $TERRAFORM_VERSION or later."
    exit 1
fi

# Check Terraform version
CURRENT_VERSION=$(terraform version -json | jq -r '.terraform_version')
log_info "Terraform version: $CURRENT_VERSION"

# Check if Azure CLI is installed and user is logged in
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed. Please install Azure CLI."
    exit 1
fi

if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run 'az login' first."
    exit 1
fi

# Get current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
log_info "Using subscription: $SUBSCRIPTION ($SUBSCRIPTION_ID)"

# Set backend configuration
BACKEND_RESOURCE_GROUP="terraform-state-rg"
BACKEND_STORAGE_ACCOUNT="terraformstate$ENVIRONMENT$(echo $SUBSCRIPTION_ID | cut -c1-6)"
BACKEND_CONTAINER="tfstate"
BACKEND_KEY="stockscanner-$ENVIRONMENT.terraform.tfstate"

# Create backend storage if it doesn't exist
log_info "Setting up Terraform backend..."

if ! az group show --name "$BACKEND_RESOURCE_GROUP" &> /dev/null; then
    log_info "Creating backend resource group: $BACKEND_RESOURCE_GROUP"
    az group create --name "$BACKEND_RESOURCE_GROUP" --location "East US 2"
fi

if ! az storage account show --name "$BACKEND_STORAGE_ACCOUNT" --resource-group "$BACKEND_RESOURCE_GROUP" &> /dev/null; then
    log_info "Creating backend storage account: $BACKEND_STORAGE_ACCOUNT"
    az storage account create \
        --name "$BACKEND_STORAGE_ACCOUNT" \
        --resource-group "$BACKEND_RESOURCE_GROUP" \
        --location "East US 2" \
        --sku Standard_LRS \
        --kind StorageV2
fi

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
    --resource-group "$BACKEND_RESOURCE_GROUP" \
    --account-name "$BACKEND_STORAGE_ACCOUNT" \
    --query [0].value -o tsv)

# Create container if it doesn't exist
if ! az storage container show --name "$BACKEND_CONTAINER" --account-name "$BACKEND_STORAGE_ACCOUNT" --account-key "$STORAGE_KEY" &> /dev/null; then
    log_info "Creating backend container: $BACKEND_CONTAINER"
    az storage container create \
        --name "$BACKEND_CONTAINER" \
        --account-name "$BACKEND_STORAGE_ACCOUNT" \
        --account-key "$STORAGE_KEY"
fi

# Export backend configuration
export ARM_ACCESS_KEY="$STORAGE_KEY"

# Initialize Terraform if needed or if init action is specified
if [ ! -d ".terraform" ] || [ "$ACTION" = "init" ]; then
    log_info "Initializing Terraform..."
    terraform init \
        -backend-config="resource_group_name=$BACKEND_RESOURCE_GROUP" \
        -backend-config="storage_account_name=$BACKEND_STORAGE_ACCOUNT" \
        -backend-config="container_name=$BACKEND_CONTAINER" \
        -backend-config="key=$BACKEND_KEY"
    
    if [ $? -eq 0 ]; then
        log_success "Terraform initialization completed"
    else
        log_error "Terraform initialization failed"
        exit 1
    fi
fi

# Generate secrets for sensitive variables
log_info "Generating secrets..."

# Generate random database password if not provided
if [ -z "$TF_VAR_db_admin_password" ]; then
    export TF_VAR_db_admin_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
    log_info "Generated database password"
fi

# Validate Terraform configuration
if [ "$ACTION" = "validate" ] || [ "$ACTION" = "plan" ] || [ "$ACTION" = "apply" ]; then
    log_info "Validating Terraform configuration..."
    terraform validate
    
    if [ $? -eq 0 ]; then
        log_success "Terraform validation passed"
    else
        log_error "Terraform validation failed"
        exit 1
    fi
fi

# Execute Terraform action
case "$ACTION" in
    "plan")
        log_info "Running Terraform plan..."
        terraform plan \
            -var-file="$TFVARS_FILE" \
            -var="db_admin_password=$TF_VAR_db_admin_password" \
            -out="tfplan-$ENVIRONMENT"
        ;;
    
    "apply")
        # Check if plan file exists
        if [ -f "tfplan-$ENVIRONMENT" ]; then
            log_info "Applying Terraform plan..."
            terraform apply "tfplan-$ENVIRONMENT"
        else
            log_warning "No plan file found. Running plan and apply..."
            terraform plan \
                -var-file="$TFVARS_FILE" \
                -var="db_admin_password=$TF_VAR_db_admin_password" \
                -out="tfplan-$ENVIRONMENT"
            
            # Confirm apply
            read -p "$(echo -e ${YELLOW}Do you want to apply these changes? [y/N]: ${NC})" -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                terraform apply "tfplan-$ENVIRONMENT"
            else
                log_info "Apply cancelled"
                exit 0
            fi
        fi
        
        if [ $? -eq 0 ]; then
            log_success "Terraform apply completed successfully!"
            
            # Display outputs
            log_info "Deployment outputs:"
            terraform output
            
            # Save important outputs
            echo "# Terraform Outputs for $ENVIRONMENT" > "outputs-$ENVIRONMENT.txt"
            echo "# Generated on $(date)" >> "outputs-$ENVIRONMENT.txt"
            echo "" >> "outputs-$ENVIRONMENT.txt"
            terraform output >> "outputs-$ENVIRONMENT.txt"
            
            log_success "Outputs saved to outputs-$ENVIRONMENT.txt"
            
        else
            log_error "Terraform apply failed"
            exit 1
        fi
        ;;
    
    "destroy")
        log_warning "This will destroy all resources in the $ENVIRONMENT environment!"
        read -p "$(echo -e ${RED}Are you absolutely sure? Type 'yes' to confirm: ${NC})" -r
        echo
        if [ "$REPLY" = "yes" ]; then
            log_info "Destroying Terraform infrastructure..."
            terraform destroy \
                -var-file="$TFVARS_FILE" \
                -var="db_admin_password=$TF_VAR_db_admin_password" \
                -auto-approve
            
            if [ $? -eq 0 ]; then
                log_success "Terraform destroy completed"
            else
                log_error "Terraform destroy failed"
                exit 1
            fi
        else
            log_info "Destroy cancelled"
            exit 0
        fi
        ;;
    
    "init")
        log_success "Terraform initialization completed"
        ;;
esac

# Post-deployment tasks
if [ "$ACTION" = "apply" ]; then
    log_info "Post-deployment recommendations:"
    echo "1. Push Docker images to the container registry"
    echo "2. Configure application settings"
    echo "3. Set up monitoring and alerts"
    echo "4. Configure custom domains"
    echo "5. Run integration tests"
    echo ""
    
    # Get important URLs
    BACKEND_URL=$(terraform output -raw backend_url 2>/dev/null || echo "Not available")
    FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "Not available")
    
    if [ "$BACKEND_URL" != "Not available" ]; then
        echo "Backend URL: $BACKEND_URL"
        echo "Frontend URL: $FRONTEND_URL"
        echo ""
    fi
fi

log_success "Terraform $ACTION completed successfully!"