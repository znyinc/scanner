# Azure Container Registry
resource "azurerm_container_registry" "main" {
  count               = var.enable_container_registry ? 1 : 0
  name                = "${var.app_name}acr${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.acr_sku
  admin_enabled       = true
  tags                = local.common_tags

  dynamic "georeplications" {
    for_each = var.acr_sku == "Premium" ? [1] : []
    content {
      location                = "West US 2"
      zone_redundancy_enabled = true
      tags                    = local.common_tags
    }
  }

  dynamic "network_rule_set" {
    for_each = var.acr_sku == "Premium" ? [1] : []
    content {
      default_action = "Deny"
      
      ip_rule {
        action   = "Allow"
        ip_range = var.allowed_ip_ranges[0]
      }
      
      virtual_network {
        action    = "Allow"
        subnet_id = azurerm_subnet.app.id
      }
    }
  }
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "plan-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.app_service_sku_name
  tags                = local.common_tags
}

# Backend App Service
resource "azurerm_linux_web_app" "backend" {
  name                = "${local.resource_prefix}-backend"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_service_plan.main.location
  service_plan_id     = azurerm_service_plan.main.id
  tags                = local.common_tags

  site_config {
    always_on = true
    
    application_stack {
      docker_image_name   = var.enable_container_registry ? "${azurerm_container_registry.main[0].login_server}/backend:latest" : "stockscanner/backend:latest"
      docker_registry_url = var.enable_container_registry ? "https://${azurerm_container_registry.main[0].login_server}" : "https://index.docker.io"
      docker_registry_username = var.enable_container_registry ? azurerm_container_registry.main[0].admin_username : null
      docker_registry_password = var.enable_container_registry ? azurerm_container_registry.main[0].admin_password : null
    }

    health_check_path = "/health"
    
    cors {
      allowed_origins     = ["https://${local.resource_prefix}-frontend.azurewebsites.net"]
      support_credentials = false
    }
  }

  app_settings = {
    "WEBSITES_PORT"                = "8000"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "DOCKER_ENABLE_CI"            = "true"
    "DATABASE_URL"                = var.enable_key_vault ? "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main[0].name};SecretName=database-connection-string)" : "postgresql://${var.db_admin_username}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}"
    "SECRET_KEY"                  = var.enable_key_vault ? "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main[0].name};SecretName=api-secret-key)" : random_password.secret_key.result
    "DEBUG"                       = var.environment == "prod" ? "false" : "true"
    "LOG_LEVEL"                   = var.environment == "prod" ? "WARNING" : "INFO"
    "CORS_ORIGINS"                = "https://${local.resource_prefix}-frontend.azurewebsites.net"
    "APPINSIGHTS_INSTRUMENTATIONKEY" = var.enable_application_insights ? azurerm_application_insights.main[0].instrumentation_key : ""
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = var.enable_application_insights ? azurerm_application_insights.main[0].connection_string : ""
  }

  identity {
    type = "SystemAssigned"
  }

  virtual_network_subnet_id = azurerm_subnet.app.id

  logs {
    detailed_error_messages = true
    failed_request_tracing  = true
    
    application_logs {
      file_system_level = "Information"
    }
    
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 100
      }
    }
  }
}

# Frontend App Service
resource "azurerm_linux_web_app" "frontend" {
  name                = "${local.resource_prefix}-frontend"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_service_plan.main.location
  service_plan_id     = azurerm_service_plan.main.id
  tags                = local.common_tags

  site_config {
    always_on = true
    
    application_stack {
      docker_image_name   = var.enable_container_registry ? "${azurerm_container_registry.main[0].login_server}/frontend:latest" : "stockscanner/frontend:latest"
      docker_registry_url = var.enable_container_registry ? "https://${azurerm_container_registry.main[0].login_server}" : "https://index.docker.io"
      docker_registry_username = var.enable_container_registry ? azurerm_container_registry.main[0].admin_username : null
      docker_registry_password = var.enable_container_registry ? azurerm_container_registry.main[0].admin_password : null
    }

    health_check_path = "/"
  }

  app_settings = {
    "WEBSITES_PORT"                = "80"
    "WEBSITES_ENABLE_APP_SERVICE_STORAGE" = "false"
    "DOCKER_ENABLE_CI"            = "true"
    "REACT_APP_API_URL"           = "https://${local.resource_prefix}-backend.azurewebsites.net/api"
    "REACT_APP_ENVIRONMENT"       = var.environment
  }

  identity {
    type = "SystemAssigned"
  }

  virtual_network_subnet_id = azurerm_subnet.app.id

  logs {
    detailed_error_messages = true
    failed_request_tracing  = true
    
    http_logs {
      file_system {
        retention_in_days = 7
        retention_in_mb   = 50
      }
    }
  }
}

# Auto-scaling for App Service Plan
resource "azurerm_monitor_autoscale_setting" "main" {
  name                = "autoscale-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  target_resource_id  = azurerm_service_plan.main.id
  tags                = local.common_tags

  profile {
    name = "default"

    capacity {
      default = var.autoscale_default_capacity
      minimum = var.autoscale_min_capacity
      maximum = var.autoscale_max_capacity
    }

    # Scale out when CPU > 70%
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
        cooldown  = "PT5M"
      }
    }

    # Scale in when CPU < 30%
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
        cooldown  = "PT10M"
      }
    }

    # Scale out when Memory > 80%
    rule {
      metric_trigger {
        metric_name        = "MemoryPercentage"
        metric_resource_id = azurerm_service_plan.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 80
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "2"
        cooldown  = "PT5M"
      }
    }

    # Scale out when HTTP queue length > 25
    rule {
      metric_trigger {
        metric_name        = "HttpQueueLength"
        metric_resource_id = azurerm_service_plan.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 25
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT5M"
      }
    }
  }

  # Weekend profile with reduced capacity
  profile {
    name = "weekend"

    capacity {
      default = 1
      minimum = 1
      maximum = 5
    }

    recurrence {
      timezone = "UTC"
      days     = ["Saturday", "Sunday"]
      hours    = [0]
      minutes  = [0]
    }

    rule {
      metric_trigger {
        metric_name        = "CpuPercentage"
        metric_resource_id = azurerm_service_plan.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT10M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 80
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT10M"
      }
    }
  }
}

# Random password for secret key
resource "random_password" "secret_key" {
  length  = 50
  special = true
}

# Generate backend webhook for continuous deployment
resource "azurerm_source_control_token" "github" {
  count = var.enable_container_registry ? 1 : 0
  type  = "GitHub"
  token = var.github_token
}

# Webhook for backend container updates
resource "azurerm_container_registry_webhook" "backend" {
  count               = var.enable_container_registry ? 1 : 0
  name                = "webhook-backend-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  registry_name       = azurerm_container_registry.main[0].name
  location            = azurerm_resource_group.main.location

  service_uri = "https://${azurerm_linux_web_app.backend.site_credential[0].name}:${azurerm_linux_web_app.backend.site_credential[0].password}@${azurerm_linux_web_app.backend.default_hostname}/docker/hook"
  status      = "enabled"
  scope       = "backend:latest"
  actions     = ["push"]
  
  custom_headers = {
    "Content-Type" = "application/json"
  }
}