# Azure Deployment and Scaling Guide

This guide covers deploying and scaling the Stock Scanner application on Microsoft Azure using various Azure services for optimal performance and cost-effectiveness.

## Table of Contents

1. [Overview](#overview)
2. [Azure Service Options](#azure-service-options)
3. [Azure Container Instances (ACI)](#azure-container-instances-aci)
4. [Azure App Service](#azure-app-service)
5. [Azure Kubernetes Service (AKS)](#azure-kubernetes-service-aks)
6. [Azure Database for PostgreSQL](#azure-database-for-postgresql)
7. [Auto-scaling Configuration](#auto-scaling-configuration)
8. [Load Balancing](#load-balancing)
9. [Monitoring and Logging](#monitoring-and-logging)
10. [Infrastructure as Code](#infrastructure-as-code)
11. [Cost Optimization](#cost-optimization)
12. [Security Best Practices](#security-best-practices)

## Overview

The Stock Scanner application can be deployed on Azure using multiple approaches, each offering different levels of scalability, management overhead, and cost:

| Service | Best For | Scaling | Management | Cost |
|---------|----------|---------|------------|------|
| **Azure Container Instances** | Simple deployments, dev/test | Manual | Low | Low |
| **Azure App Service** | Web applications, quick deployment | Automatic | Low | Medium |
| **Azure Kubernetes Service** | Complex applications, microservices | Advanced | High | Variable |

## Azure Service Options

### Architecture Comparison

#### Option 1: Container Instances (Simplest)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐
│   Azure Front  │    │  Container      │    │  Azure Database     │
│   Door          │◄──►│  Instances      │◄──►│  for PostgreSQL    │
│                 │    │  (Frontend +    │    │                     │
│   Load Balancer │    │   Backend)      │    │  Managed Service    │
└─────────────────┘    └─────────────────┘    └─────────────────────┘
```

#### Option 2: App Service (Recommended for most cases)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐
│   Azure Front  │    │  App Service    │    │  Azure Database     │
│   Door          │◄──►│  Plan           │◄──►│  for PostgreSQL    │
│                 │    │                 │    │                     │
│   CDN + WAF     │    │  Auto-scaling   │    │  Read Replicas      │
└─────────────────┘    └─────────────────┘    └─────────────────────┘
```

#### Option 3: Kubernetes (Enterprise/High-scale)
```
┌─────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Application   │    │   Azure Kubernetes  │    │  Azure Database     │
│   Gateway       │◄──►│   Service (AKS)     │◄──►│  for PostgreSQL    │
│                 │    │                     │    │                     │
│   Ingress       │    │  Pods + Services    │    │  High Availability  │
└─────────────────┘    └─────────────────────┘    └─────────────────────┘
```

## Azure Container Instances (ACI)

### Prerequisites

- Azure CLI installed and configured
- Docker images built and pushed to Azure Container Registry

### Setup Azure Container Registry

```bash
# Create resource group
az group create --name rg-stock-scanner --location eastus2

# Create Azure Container Registry
az acr create --resource-group rg-stock-scanner \
              --name stockscanneracr \
              --sku Standard \
              --admin-enabled true

# Get ACR login server
az acr show --name stockscanneracr --query loginServer --output table

# Login to ACR
az acr login --name stockscanneracr
```

### Build and Push Images

```bash
# Tag and push backend image
docker tag stockscanner-backend:latest stockscanneracr.azurecr.io/backend:latest
docker push stockscanneracr.azurecr.io/backend:latest

# Tag and push frontend image
docker tag stockscanner-frontend:latest stockscanneracr.azurecr.io/frontend:latest
docker push stockscanneracr.azurecr.io/frontend:latest
```

### Deploy Container Instances

```bash
# Get ACR credentials
ACR_SERVER=$(az acr show --name stockscanneracr --query loginServer --output tsv)
ACR_USERNAME=$(az acr credential show --name stockscanneracr --query username --output tsv)
ACR_PASSWORD=$(az acr credential show --name stockscanneracr --query passwords[0].value --output tsv)

# Deploy backend container
az container create \
  --resource-group rg-stock-scanner \
  --name backend-container \
  --image $ACR_SERVER/backend:latest \
  --registry-login-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label stockscanner-backend \
  --ports 8000 \
  --memory 2 \
  --cpu 1 \
  --environment-variables \
    DATABASE_URL="postgresql://username:password@server.postgres.database.azure.com:5432/stockscanner" \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    DEBUG=false

# Deploy frontend container
az container create \
  --resource-group rg-stock-scanner \
  --name frontend-container \
  --image $ACR_SERVER/frontend:latest \
  --registry-login-server $ACR_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --dns-name-label stockscanner-frontend \
  --ports 80 \
  --memory 1 \
  --cpu 0.5
```

### Container Instances Scaling

```bash
# Scale containers by updating CPU and memory
az container update \
  --resource-group rg-stock-scanner \
  --name backend-container \
  --cpu 2 \
  --memory 4

# Create multiple container instances for load distribution
for i in {1..3}; do
  az container create \
    --resource-group rg-stock-scanner \
    --name backend-container-$i \
    --image $ACR_SERVER/backend:latest \
    --registry-login-server $ACR_SERVER \
    --registry-username $ACR_USERNAME \
    --registry-password $ACR_PASSWORD \
    --ports 8000 \
    --memory 2 \
    --cpu 1
done
```

## Azure App Service

### Setup App Service Plan

```bash
# Create App Service Plan with scaling capability
az appservice plan create \
  --name stockscanner-plan \
  --resource-group rg-stock-scanner \
  --sku S2 \
  --is-linux \
  --location eastus2

# Enable auto-scaling (requires Standard tier or higher)
az monitor autoscale create \
  --resource-group rg-stock-scanner \
  --resource stockscanner-plan \
  --resource-type Microsoft.Web/serverfarms \
  --name stockscanner-autoscale \
  --min-count 1 \
  --max-count 10 \
  --count 2
```

### Deploy Backend App Service

```bash
# Create backend web app
az webapp create \
  --resource-group rg-stock-scanner \
  --plan stockscanner-plan \
  --name stockscanner-backend \
  --deployment-container-image-name $ACR_SERVER/backend:latest

# Configure container registry
az webapp config container set \
  --name stockscanner-backend \
  --resource-group rg-stock-scanner \
  --docker-custom-image-name $ACR_SERVER/backend:latest \
  --docker-registry-server-url https://$ACR_SERVER \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Configure application settings
az webapp config appsettings set \
  --resource-group rg-stock-scanner \
  --name stockscanner-backend \
  --settings \
    DATABASE_URL="postgresql://username:password@server.postgres.database.azure.com:5432/stockscanner" \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    DEBUG=false \
    WEBSITES_PORT=8000
```

### Deploy Frontend App Service

```bash
# Create frontend web app
az webapp create \
  --resource-group rg-stock-scanner \
  --plan stockscanner-plan \
  --name stockscanner-frontend \
  --deployment-container-image-name $ACR_SERVER/frontend:latest

# Configure container registry
az webapp config container set \
  --name stockscanner-frontend \
  --resource-group rg-stock-scanner \
  --docker-custom-image-name $ACR_SERVER/frontend:latest \
  --docker-registry-server-url https://$ACR_SERVER \
  --docker-registry-server-user $ACR_USERNAME \
  --docker-registry-server-password $ACR_PASSWORD

# Configure application settings
az webapp config appsettings set \
  --resource-group rg-stock-scanner \
  --name stockscanner-frontend \
  --settings \
    REACT_APP_API_URL="https://stockscanner-backend.azurewebsites.net/api" \
    WEBSITES_PORT=80
```

### App Service Auto-scaling Rules

```bash
# Scale out when CPU > 70% for 5 minutes
az monitor autoscale rule create \
  --resource-group rg-stock-scanner \
  --autoscale-name stockscanner-autoscale \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1

# Scale in when CPU < 30% for 10 minutes
az monitor autoscale rule create \
  --resource-group rg-stock-scanner \
  --autoscale-name stockscanner-autoscale \
  --condition "Percentage CPU < 30 avg 10m" \
  --scale in 1

# Scale out when memory > 80% for 5 minutes
az monitor autoscale rule create \
  --resource-group rg-stock-scanner \
  --autoscale-name stockscanner-autoscale \
  --condition "Memory Percentage > 80 avg 5m" \
  --scale out 2

# Scale out based on HTTP queue length
az monitor autoscale rule create \
  --resource-group rg-stock-scanner \
  --autoscale-name stockscanner-autoscale \
  --condition "Http Queue Length > 25 avg 1m" \
  --scale out 1
```

## Azure Kubernetes Service (AKS)

### Create AKS Cluster

```bash
# Create AKS cluster with auto-scaling enabled
az aks create \
  --resource-group rg-stock-scanner \
  --name stockscanner-aks \
  --node-count 2 \
  --enable-addons monitoring \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10 \
  --node-vm-size Standard_D2s_v3 \
  --attach-acr stockscanneracr \
  --generate-ssh-keys

# Get AKS credentials
az aks get-credentials --resource-group rg-stock-scanner --name stockscanner-aks
```

### Kubernetes Manifests

#### Namespace
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: stockscanner
```

#### Backend Deployment
```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: stockscanner
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: stockscanneracr.azurecr.io/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: connection-string
        - name: API_HOST
          value: "0.0.0.0"
        - name: API_PORT
          value: "8000"
        - name: DEBUG
          value: "false"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: stockscanner
spec:
  selector:
    app: backend
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
```

#### Frontend Deployment
```yaml
# k8s/frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: stockscanner
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: stockscanneracr.azurecr.io/frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: stockscanner
spec:
  selector:
    app: frontend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 80
  type: ClusterIP
```

#### Horizontal Pod Autoscaler
```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: stockscanner
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: frontend-hpa
  namespace: stockscanner
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: frontend
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

#### Ingress with Application Gateway
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: stockscanner-ingress
  namespace: stockscanner
  annotations:
    kubernetes.io/ingress.class: azure/application-gateway
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
    appgw.ingress.kubernetes.io/backend-path-prefix: "/"
spec:
  rules:
  - host: stockscanner.yourdomain.com
    http:
      paths:
      - path: /api/*
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8000
      - path: /*
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  tls:
  - hosts:
    - stockscanner.yourdomain.com
    secretName: stockscanner-tls
```

### Deploy to AKS

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create database secret
kubectl create secret generic database-secret \
  --from-literal=connection-string="postgresql://username:password@server.postgres.database.azure.com:5432/stockscanner" \
  --namespace=stockscanner

# Deploy applications
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml

# Verify deployments
kubectl get pods -n stockscanner
kubectl get services -n stockscanner
kubectl get hpa -n stockscanner
```

## Azure Database for PostgreSQL

### Create Managed PostgreSQL

```bash
# Create Azure Database for PostgreSQL Flexible Server
az postgres flexible-server create \
  --name stockscanner-db \
  --resource-group rg-stock-scanner \
  --location eastus2 \
  --admin-user stockscanner_admin \
  --admin-password "YourSecurePassword123!" \
  --sku-name Standard_D2s_v3 \
  --tier GeneralPurpose \
  --storage-size 128 \
  --version 15

# Configure firewall rules
az postgres flexible-server firewall-rule create \
  --resource-group rg-stock-scanner \
  --name stockscanner-db \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0

# Enable high availability
az postgres flexible-server update \
  --resource-group rg-stock-scanner \
  --name stockscanner-db \
  --high-availability Enabled \
  --standby-availability-zone 2

# Create database
az postgres flexible-server db create \
  --resource-group rg-stock-scanner \
  --server-name stockscanner-db \
  --database-name stockscanner
```

### Database Scaling Configuration

```bash
# Scale up compute
az postgres flexible-server update \
  --resource-group rg-stock-scanner \
  --name stockscanner-db \
  --sku-name Standard_D4s_v3

# Scale storage
az postgres flexible-server update \
  --resource-group rg-stock-scanner \
  --name stockscanner-db \
  --storage-size 512

# Configure backup retention
az postgres flexible-server update \
  --resource-group rg-stock-scanner \
  --name stockscanner-db \
  --backup-retention 30

# Create read replica for read scaling
az postgres flexible-server replica create \
  --replica-name stockscanner-db-read-replica \
  --resource-group rg-stock-scanner \
  --source-server stockscanner-db \
  --location eastus
```

### Connection Pooling Configuration

```bash
# Enable connection pooling with PgBouncer
az postgres flexible-server parameter set \
  --resource-group rg-stock-scanner \
  --server-name stockscanner-db \
  --name shared_preload_libraries \
  --value "pg_stat_statements,pgbouncer"

# Configure max connections
az postgres flexible-server parameter set \
  --resource-group rg-stock-scanner \
  --server-name stockscanner-db \
  --name max_connections \
  --value 200
```

## Auto-scaling Configuration

### Application Gateway Auto-scaling

```bash
# Create Application Gateway with auto-scaling
az network application-gateway create \
  --name stockscanner-appgw \
  --location eastus2 \
  --resource-group rg-stock-scanner \
  --capacity 2 \
  --max-capacity 10 \
  --min-capacity 1 \
  --sku Standard_v2 \
  --vnet-name stockscanner-vnet \
  --subnet appgw-subnet \
  --public-ip-address stockscanner-pip \
  --http-settings-cookie-based-affinity Disabled \
  --frontend-port 80 \
  --http-settings-port 80 \
  --http-settings-protocol Http
```

### Virtual Machine Scale Sets (Alternative)

```bash
# Create VMSS for custom scaling scenarios
az vmss create \
  --resource-group rg-stock-scanner \
  --name stockscanner-vmss \
  --image UbuntuLTS \
  --upgrade-policy-mode automatic \
  --instance-count 2 \
  --admin-username azureuser \
  --generate-ssh-keys \
  --load-balancer stockscanner-lb

# Enable auto-scaling for VMSS
az monitor autoscale create \
  --resource-group rg-stock-scanner \
  --resource stockscanner-vmss \
  --resource-type Microsoft.Compute/virtualMachineScaleSets \
  --name stockscanner-vmss-autoscale \
  --min-count 1 \
  --max-count 10 \
  --count 2

# Add scaling rules
az monitor autoscale rule create \
  --resource-group rg-stock-scanner \
  --autoscale-name stockscanner-vmss-autoscale \
  --condition "Percentage CPU > 75 avg 5m" \
  --scale out 2

az monitor autoscale rule create \
  --resource-group rg-stock-scanner \
  --autoscale-name stockscanner-vmss-autoscale \
  --condition "Percentage CPU < 25 avg 10m" \
  --scale in 1
```

## Load Balancing

### Azure Load Balancer Configuration

```bash
# Create public IP for load balancer
az network public-ip create \
  --resource-group rg-stock-scanner \
  --name stockscanner-lb-pip \
  --sku Standard

# Create load balancer
az network lb create \
  --resource-group rg-stock-scanner \
  --name stockscanner-lb \
  --sku Standard \
  --public-ip-address stockscanner-lb-pip \
  --frontend-ip-name stockscanner-frontend \
  --backend-pool-name stockscanner-backend-pool

# Create health probe
az network lb probe create \
  --resource-group rg-stock-scanner \
  --lb-name stockscanner-lb \
  --name health-probe \
  --protocol http \
  --port 8000 \
  --path /health

# Create load balancing rule
az network lb rule create \
  --resource-group rg-stock-scanner \
  --lb-name stockscanner-lb \
  --name http-rule \
  --protocol tcp \
  --frontend-port 80 \
  --backend-port 8000 \
  --frontend-ip-name stockscanner-frontend \
  --backend-pool-name stockscanner-backend-pool \
  --probe-name health-probe
```

### Azure Front Door Configuration

```bash
# Create Azure Front Door for global load balancing
az network front-door create \
  --resource-group rg-stock-scanner \
  --name stockscanner-frontdoor \
  --backend-address stockscanner-backend.azurewebsites.net \
  --frontend-host-name stockscanner.azurefd.net

# Add additional backend pools for multi-region deployment
az network front-door backend-pool create \
  --resource-group rg-stock-scanner \
  --front-door-name stockscanner-frontdoor \
  --pool-name backend-pool-east \
  --backend-address stockscanner-east.azurewebsites.net \
  --backend-host-header stockscanner-east.azurewebsites.net

az network front-door backend-pool create \
  --resource-group rg-stock-scanner \
  --front-door-name stockscanner-frontdoor \
  --pool-name backend-pool-west \
  --backend-address stockscanner-west.azurewebsites.net \
  --backend-host-header stockscanner-west.azurewebsites.net
```

## Monitoring and Logging

### Azure Monitor Configuration

```bash
# Create Log Analytics workspace
az monitor log-analytics workspace create \
  --resource-group rg-stock-scanner \
  --workspace-name stockscanner-logs \
  --location eastus2

# Get workspace ID and key
WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group rg-stock-scanner \
  --workspace-name stockscanner-logs \
  --query customerId -o tsv)

WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group rg-stock-scanner \
  --workspace-name stockscanner-logs \
  --query primarySharedKey -o tsv)

# Enable Container Insights for AKS
az aks enable-addons \
  --resource-group rg-stock-scanner \
  --name stockscanner-aks \
  --addons monitoring \
  --workspace-resource-id /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/Microsoft.OperationalInsights/workspaces/stockscanner-logs
```

### Application Insights

```bash
# Create Application Insights
az monitor app-insights component create \
  --app stockscanner-insights \
  --location eastus2 \
  --resource-group rg-stock-scanner \
  --workspace /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/Microsoft.OperationalInsights/workspaces/stockscanner-logs

# Get instrumentation key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app stockscanner-insights \
  --resource-group rg-stock-scanner \
  --query instrumentationKey -o tsv)

# Configure App Service to use Application Insights
az webapp config appsettings set \
  --resource-group rg-stock-scanner \
  --name stockscanner-backend \
  --settings \
    APPINSIGHTS_INSTRUMENTATIONKEY=$INSTRUMENTATION_KEY \
    APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$INSTRUMENTATION_KEY"
```

### Alerting Rules

```bash
# Create CPU usage alert
az monitor metrics alert create \
  --name "High CPU Usage" \
  --resource-group rg-stock-scanner \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/Microsoft.Web/sites/stockscanner-backend \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-ids /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/microsoft.insights/actionGroups/stockscanner-alerts

# Create memory usage alert
az monitor metrics alert create \
  --name "High Memory Usage" \
  --resource-group rg-stock-scanner \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/Microsoft.Web/sites/stockscanner-backend \
  --condition "avg Memory Percentage > 85" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-ids /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/microsoft.insights/actionGroups/stockscanner-alerts

# Create response time alert
az monitor metrics alert create \
  --name "High Response Time" \
  --resource-group rg-stock-scanner \
  --scopes /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/Microsoft.Web/sites/stockscanner-backend \
  --condition "avg Response Time > 5" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-ids /subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-stock-scanner/providers/microsoft.insights/actionGroups/stockscanner-alerts
```

## Infrastructure as Code

### Azure Resource Manager (ARM) Template

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "appName": {
      "type": "string",
      "defaultValue": "stockscanner",
      "metadata": {
        "description": "Name of the application"
      }
    },
    "environment": {
      "type": "string",
      "defaultValue": "prod",
      "allowedValues": ["dev", "staging", "prod"],
      "metadata": {
        "description": "Environment name"
      }
    },
    "dbAdminPassword": {
      "type": "securestring",
      "metadata": {
        "description": "Database administrator password"
      }
    }
  },
  "variables": {
    "resourceGroupName": "[concat('rg-', parameters('appName'), '-', parameters('environment'))]",
    "appServicePlanName": "[concat(parameters('appName'), '-plan-', parameters('environment'))]",
    "backendAppName": "[concat(parameters('appName'), '-backend-', parameters('environment'))]",
    "frontendAppName": "[concat(parameters('appName'), '-frontend-', parameters('environment'))]",
    "databaseServerName": "[concat(parameters('appName'), '-db-', parameters('environment'))]",
    "containerRegistryName": "[concat(parameters('appName'), 'acr', parameters('environment'))]"
  },
  "resources": [
    {
      "type": "Microsoft.Web/serverfarms",
      "apiVersion": "2021-02-01",
      "name": "[variables('appServicePlanName')]",
      "location": "[resourceGroup().location]",
      "sku": {
        "name": "S2",
        "tier": "Standard",
        "capacity": 2
      },
      "kind": "linux",
      "properties": {
        "reserved": true
      }
    },
    {
      "type": "Microsoft.Web/sites",
      "apiVersion": "2021-02-01",
      "name": "[variables('backendAppName')]",
      "location": "[resourceGroup().location]",
      "dependsOn": [
        "[resourceId('Microsoft.Web/serverfarms', variables('appServicePlanName'))]"
      ],
      "properties": {
        "serverFarmId": "[resourceId('Microsoft.Web/serverfarms', variables('appServicePlanName'))]",
        "siteConfig": {
          "linuxFxVersion": "DOCKER|stockscanneracr.azurecr.io/backend:latest",
          "appSettings": [
            {
              "name": "WEBSITES_PORT",
              "value": "8000"
            },
            {
              "name": "DATABASE_URL",
              "value": "[concat('postgresql://stockscanner_admin:', parameters('dbAdminPassword'), '@', variables('databaseServerName'), '.postgres.database.azure.com:5432/stockscanner')]"
            }
          ]
        }
      }
    },
    {
      "type": "Microsoft.DBforPostgreSQL/flexibleServers",
      "apiVersion": "2021-06-01",
      "name": "[variables('databaseServerName')]",
      "location": "[resourceGroup().location]",
      "sku": {
        "name": "Standard_D2s_v3",
        "tier": "GeneralPurpose"
      },
      "properties": {
        "administratorLogin": "stockscanner_admin",
        "administratorLoginPassword": "[parameters('dbAdminPassword')]",
        "version": "15",
        "storage": {
          "storageSizeGB": 128
        },
        "backup": {
          "backupRetentionDays": 30,
          "geoRedundantBackup": "Enabled"
        },
        "highAvailability": {
          "mode": "ZoneRedundant"
        }
      }
    }
  ],
  "outputs": {
    "backendUrl": {
      "type": "string",
      "value": "[concat('https://', variables('backendAppName'), '.azurewebsites.net')]"
    },
    "frontendUrl": {
      "type": "string",
      "value": "[concat('https://', variables('frontendAppName'), '.azurewebsites.net')]"
    }
  }
}
```

### Terraform Configuration

```hcl
# terraform/main.tf
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Variables
variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "stockscanner"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US 2"
}

variable "db_admin_password" {
  description = "Database administrator password"
  type        = string
  sensitive   = true
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.app_name}-${var.environment}"
  location = var.location
}

# Container Registry
resource "azurerm_container_registry" "main" {
  name                = "${var.app_name}acr${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  sku                = "Standard"
  admin_enabled      = true
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "${var.app_name}-plan-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  os_type            = "Linux"
  sku_name           = "S2"
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${var.app_name}-db-${var.environment}"
  resource_group_name    = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  version               = "15"
  administrator_login    = "stockscanner_admin"
  administrator_password = var.db_admin_password
  zone                  = "1"
  
  storage_mb = 131072
  
  sku_name = "GP_Standard_D2s_v3"
  
  backup_retention_days = 30
  geo_redundant_backup_enabled = true
  
  high_availability {
    mode = "ZoneRedundant"
    standby_availability_zone = "2"
  }
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = "stockscanner"
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# Backend App Service
resource "azurerm_linux_web_app" "backend" {
  name                = "${var.app_name}-backend-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_service_plan.main.location
  service_plan_id    = azurerm_service_plan.main.id

  site_config {
    application_stack {
      docker_image_name = "${azurerm_container_registry.main.login_server}/backend:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
      docker_registry_username = azurerm_container_registry.main.admin_username
      docker_registry_password = azurerm_container_registry.main.admin_password
    }
  }

  app_settings = {
    "WEBSITES_PORT" = "8000"
    "DATABASE_URL" = "postgresql://${azurerm_postgresql_flexible_server.main.administrator_login}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}"
    "DEBUG" = "false"
  }
}

# Frontend App Service
resource "azurerm_linux_web_app" "frontend" {
  name                = "${var.app_name}-frontend-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_service_plan.main.location
  service_plan_id    = azurerm_service_plan.main.id

  site_config {
    application_stack {
      docker_image_name = "${azurerm_container_registry.main.login_server}/frontend:latest"
      docker_registry_url = "https://${azurerm_container_registry.main.login_server}"
      docker_registry_username = azurerm_container_registry.main.admin_username
      docker_registry_password = azurerm_container_registry.main.admin_password
    }
  }

  app_settings = {
    "WEBSITES_PORT" = "80"
    "REACT_APP_API_URL" = "https://${azurerm_linux_web_app.backend.default_hostname}/api"
  }
}

# Auto-scaling for App Service Plan
resource "azurerm_monitor_autoscale_setting" "main" {
  name                = "${var.app_name}-autoscale-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location           = azurerm_resource_group.main.location
  target_resource_id = azurerm_service_plan.main.id

  profile {
    name = "default"

    capacity {
      default = 2
      minimum = 1
      maximum = 10
    }

    rule {
      metric_trigger {
        metric_name        = "CpuPercentage"
        metric_resource_id = azurerm_service_plan.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 70
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT1M"
      }
    }

    rule {
      metric_trigger {
        metric_name        = "CpuPercentage"
        metric_resource_id = azurerm_service_plan.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT10M"
        time_aggregation   = "Average"
        operator           = "LessThan"
        threshold          = 30
      }

      scale_action {
        direction = "Decrease"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT1M"
      }
    }
  }
}

# Outputs
output "backend_url" {
  value = "https://${azurerm_linux_web_app.backend.default_hostname}"
}

output "frontend_url" {
  value = "https://${azurerm_linux_web_app.frontend.default_hostname}"
}

output "database_fqdn" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}
```

## Cost Optimization

### Pricing Tiers Comparison

| Service | Basic | Standard | Premium | Estimated Monthly Cost |
|---------|-------|----------|---------|----------------------|
| **App Service** | B1 (1 core, 1.75GB) | S2 (2 cores, 3.5GB) | P1v3 (2 cores, 8GB) | $55 - $220 |
| **PostgreSQL** | B1ms (1 vCore, 2GB) | GP_D2s_v3 (2 vCores, 8GB) | MO_D4s_v3 (4 vCores, 16GB) | $25 - $400 |
| **Container Registry** | Basic (10GB) | Standard (100GB) | Premium (500GB) | $5 - $50 |
| **Application Gateway** | Standard_v2 | WAF_v2 | - | $25 - $85 |

### Cost Optimization Strategies

#### 1. Reserved Instances
```bash
# Purchase reserved instances for predictable workloads
az reservations reservation-order purchase \
  --reserved-resource-type VirtualMachines \
  --sku Standard_D2s_v3 \
  --location eastus2 \
  --quantity 2 \
  --term P1Y \
  --billing-scope /subscriptions/your-subscription-id
```

#### 2. Azure Hybrid Benefit
```bash
# Apply Azure Hybrid Benefit for Windows VMs
az vm update \
  --resource-group rg-stock-scanner \
  --name stockscanner-vm \
  --license-type Windows_Server
```

#### 3. Auto-shutdown for Dev/Test
```bash
# Create auto-shutdown policy for development environments
az vm auto-shutdown create \
  --resource-group rg-stock-scanner-dev \
  --name stockscanner-vm-dev \
  --time 1900 \
  --email user@company.com
```

#### 4. Spot Instances for AKS
```yaml
# Use spot instances for non-critical workloads
apiVersion: v1
kind: Node
metadata:
  labels:
    kubernetes.azure.com/scalesetpriority: spot
spec:
  taints:
  - key: kubernetes.azure.com/scalesetpriority
    value: spot
    effect: NoSchedule
```

### Cost Monitoring

```bash
# Set up budget alerts
az consumption budget create \
  --budget-name stockscanner-budget \
  --amount 500 \
  --time-grain Monthly \
  --time-period start-date=2024-01-01 \
  --notification-enabled true \
  --contact-emails admin@company.com \
  --threshold 80
```

## Security Best Practices

### Network Security

#### Virtual Network Configuration
```bash
# Create VNet with subnets
az network vnet create \
  --resource-group rg-stock-scanner \
  --name stockscanner-vnet \
  --address-prefixes 10.0.0.0/16 \
  --subnet-name app-subnet \
  --subnet-prefixes 10.0.1.0/24

# Create database subnet
az network vnet subnet create \
  --resource-group rg-stock-scanner \
  --vnet-name stockscanner-vnet \
  --name db-subnet \
  --address-prefixes 10.0.2.0/24 \
  --service-endpoints Microsoft.Storage Microsoft.Sql

# Create Network Security Group
az network nsg create \
  --resource-group rg-stock-scanner \
  --name stockscanner-nsg

# Add NSG rules
az network nsg rule create \
  --resource-group rg-stock-scanner \
  --nsg-name stockscanner-nsg \
  --name AllowHTTPS \
  --priority 1000 \
  --source-address-prefixes '*' \
  --source-port-ranges '*' \
  --destination-address-prefixes '*' \
  --destination-port-ranges 443 \
  --access Allow \
  --protocol Tcp
```

### Identity and Access Management

#### Azure AD Integration
```bash
# Create Azure AD app registration
az ad app create \
  --display-name "Stock Scanner" \
  --web-redirect-uris "https://stockscanner.yourdomain.com/auth/callback"

# Assign managed identity to App Service
az webapp identity assign \
  --resource-group rg-stock-scanner \
  --name stockscanner-backend

# Grant Key Vault access to managed identity
az keyvault set-policy \
  --name stockscanner-keyvault \
  --resource-group rg-stock-scanner \
  --object-id $(az webapp identity show --resource-group rg-stock-scanner --name stockscanner-backend --query principalId -o tsv) \
  --secret-permissions get list
```

### Key Vault Integration

```bash
# Create Key Vault
az keyvault create \
  --name stockscanner-keyvault \
  --resource-group rg-stock-scanner \
  --location eastus2 \
  --sku standard

# Store secrets
az keyvault secret set \
  --vault-name stockscanner-keyvault \
  --name "database-connection-string" \
  --value "postgresql://username:password@server.postgres.database.azure.com:5432/stockscanner"

az keyvault secret set \
  --vault-name stockscanner-keyvault \
  --name "api-secret-key" \
  --value "your-super-secret-key"

# Configure App Service to use Key Vault
az webapp config appsettings set \
  --resource-group rg-stock-scanner \
  --name stockscanner-backend \
  --settings \
    DATABASE_URL="@Microsoft.KeyVault(VaultName=stockscanner-keyvault;SecretName=database-connection-string)" \
    SECRET_KEY="@Microsoft.KeyVault(VaultName=stockscanner-keyvault;SecretName=api-secret-key)"
```

### SSL/TLS Configuration

```bash
# Upload SSL certificate
az webapp config ssl upload \
  --resource-group rg-stock-scanner \
  --name stockscanner-frontend \
  --certificate-file path/to/certificate.pfx \
  --certificate-password certificate-password

# Bind SSL certificate
az webapp config ssl bind \
  --resource-group rg-stock-scanner \
  --name stockscanner-frontend \
  --certificate-thumbprint certificate-thumbprint \
  --ssl-type SNI
```

---

This comprehensive Azure deployment guide provides multiple scaling options for the Stock Scanner application, from simple container deployments to advanced Kubernetes orchestration. Choose the approach that best fits your scalability requirements, technical expertise, and budget constraints.

For additional support and updates to this guide, please refer to the official Azure documentation and the Stock Scanner project repository.