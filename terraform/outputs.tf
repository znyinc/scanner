# Application URLs
output "backend_url" {
  description = "Backend application URL"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
  sensitive   = false
}

output "frontend_url" {
  description = "Frontend application URL"
  value       = "https://${azurerm_linux_web_app.frontend.default_hostname}"
  sensitive   = false
}

output "backend_staging_url" {
  description = "Backend staging slot URL"
  value       = "https://${azurerm_linux_web_app.backend.default_hostname}"
  sensitive   = false
}

# Database Information
output "database_fqdn" {
  description = "Database fully qualified domain name"
  value       = azurerm_postgresql_flexible_server.main.fqdn
  sensitive   = false
}

output "database_name" {
  description = "Database name"
  value       = azurerm_postgresql_flexible_server_database.main.name
  sensitive   = false
}

output "database_read_replica_fqdn" {
  description = "Database read replica FQDN"
  value       = var.environment == "prod" ? azurerm_postgresql_flexible_server.read_replica[0].fqdn : null
  sensitive   = false
}

# Container Registry Information
output "container_registry_url" {
  description = "Container registry login server URL"
  value       = var.enable_container_registry ? azurerm_container_registry.main[0].login_server : null
  sensitive   = false
}

output "container_registry_admin_username" {
  description = "Container registry admin username"
  value       = var.enable_container_registry ? azurerm_container_registry.main[0].admin_username : null
  sensitive   = false
}

output "container_registry_admin_password" {
  description = "Container registry admin password"
  value       = var.enable_container_registry ? azurerm_container_registry.main[0].admin_password : null
  sensitive   = true
}

# Key Vault Information
output "key_vault_name" {
  description = "Key Vault name"
  value       = var.enable_key_vault ? azurerm_key_vault.main[0].name : null
  sensitive   = false
}

output "key_vault_uri" {
  description = "Key Vault URI"
  value       = var.enable_key_vault ? azurerm_key_vault.main[0].vault_uri : null
  sensitive   = false
}

# Monitoring Information
output "log_analytics_workspace_id" {
  description = "Log Analytics workspace ID"
  value       = azurerm_log_analytics_workspace.main.workspace_id
  sensitive   = false
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = var.enable_application_insights ? azurerm_application_insights.main[0].instrumentation_key : null
  sensitive   = true
}

output "application_insights_app_id" {
  description = "Application Insights application ID"
  value       = var.enable_application_insights ? azurerm_application_insights.main[0].app_id : null
  sensitive   = false
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = var.enable_application_insights ? azurerm_application_insights.main[0].connection_string : null
  sensitive   = true
}

# Redis Information
output "redis_hostname" {
  description = "Redis cache hostname"
  value       = var.enable_redis ? azurerm_redis_cache.main[0].hostname : null
  sensitive   = false
}

output "redis_port" {
  description = "Redis cache SSL port"
  value       = var.enable_redis ? azurerm_redis_cache.main[0].ssl_port : null
  sensitive   = false
}

output "redis_primary_access_key" {
  description = "Redis cache primary access key"
  value       = var.enable_redis ? azurerm_redis_cache.main[0].primary_access_key : null
  sensitive   = true
}

# Network Information
output "virtual_network_id" {
  description = "Virtual network ID"
  value       = azurerm_virtual_network.main.id
  sensitive   = false
}

output "app_subnet_id" {
  description = "Application subnet ID"
  value       = azurerm_subnet.app.id
  sensitive   = false
}

output "database_subnet_id" {
  description = "Database subnet ID"
  value       = azurerm_subnet.db.id
  sensitive   = false
}

# Resource Group Information
output "resource_group_name" {
  description = "Resource group name"
  value       = azurerm_resource_group.main.name
  sensitive   = false
}

output "resource_group_location" {
  description = "Resource group location"
  value       = azurerm_resource_group.main.location
  sensitive   = false
}

# App Service Information
output "app_service_plan_id" {
  description = "App Service plan ID"
  value       = azurerm_service_plan.main.id
  sensitive   = false
}

output "backend_principal_id" {
  description = "Backend app service managed identity principal ID"
  value       = azurerm_linux_web_app.backend.identity[0].principal_id
  sensitive   = false
}

output "frontend_principal_id" {
  description = "Frontend app service managed identity principal ID"
  value       = azurerm_linux_web_app.frontend.identity[0].principal_id
  sensitive   = false
}

# Scaling Information
output "autoscale_setting_id" {
  description = "Autoscale setting resource ID"
  value       = azurerm_monitor_autoscale_setting.main.id
  sensitive   = false
}

output "current_capacity" {
  description = "Current autoscale capacity settings"
  value = {
    default = var.autoscale_default_capacity
    minimum = var.autoscale_min_capacity
    maximum = var.autoscale_max_capacity
  }
  sensitive = false
}

# Deployment Information
output "deployment_commands" {
  description = "Commands to deploy Docker images"
  value = var.enable_container_registry ? {
    backend_push  = "docker tag stockscanner-backend:latest ${azurerm_container_registry.main[0].login_server}/backend:latest && docker push ${azurerm_container_registry.main[0].login_server}/backend:latest"
    frontend_push = "docker tag stockscanner-frontend:latest ${azurerm_container_registry.main[0].login_server}/frontend:latest && docker push ${azurerm_container_registry.main[0].login_server}/frontend:latest"
    acr_login     = "az acr login --name ${azurerm_container_registry.main[0].name}"
  } : null
  sensitive = false
}

# Connection Strings (for application configuration)
output "connection_strings" {
  description = "Connection strings for application configuration"
  value = {
    database = var.enable_key_vault ? "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main[0].name};SecretName=database-connection-string)" : "postgresql://${var.db_admin_username}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}?sslmode=require"
    redis    = var.enable_redis && var.enable_key_vault ? "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main[0].name};SecretName=redis-connection-string)" : (var.enable_redis ? "redis://${azurerm_redis_cache.main[0].hostname}:${azurerm_redis_cache.main[0].ssl_port}?password=${azurerm_redis_cache.main[0].primary_access_key}&ssl=true" : null)
  }
  sensitive = true
}

# Health Check URLs
output "health_check_urls" {
  description = "Health check URLs for monitoring"
  value = {
    backend_health  = "https://${azurerm_linux_web_app.backend.default_hostname}/health"
    frontend_health = "https://${azurerm_linux_web_app.frontend.default_hostname}/"
  }
  sensitive = false
}

# Cost Information
output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (USD)"
  value = {
    app_service_plan = var.app_service_sku_name == "S2" ? 73 : (var.app_service_sku_name == "P1v3" ? 146 : 36)
    database        = var.db_sku_name == "GP_Standard_D2s_v3" ? 160 : (var.db_sku_name == "B_Standard_B1ms" ? 25 : 320)
    container_registry = var.enable_container_registry ? (var.acr_sku == "Standard" ? 20 : (var.acr_sku == "Premium" ? 50 : 5)) : 0
    redis           = var.enable_redis ? (var.environment == "prod" ? 400 : 15) : 0
    log_analytics   = 5
    total_estimated = (var.app_service_sku_name == "S2" ? 73 : (var.app_service_sku_name == "P1v3" ? 146 : 36)) + (var.db_sku_name == "GP_Standard_D2s_v3" ? 160 : (var.db_sku_name == "B_Standard_B1ms" ? 25 : 320)) + (var.enable_container_registry ? (var.acr_sku == "Standard" ? 20 : (var.acr_sku == "Premium" ? 50 : 5)) : 0) + (var.enable_redis ? (var.environment == "prod" ? 400 : 15) : 0) + 5
  }
  sensitive = false
}