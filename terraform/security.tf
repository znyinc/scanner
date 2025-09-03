# Key Vault
resource "azurerm_key_vault" "main" {
  count                      = var.enable_key_vault ? 1 : 0
  name                       = "kv-${var.app_name}-${var.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  enabled_for_disk_encryption = true
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days = 7
  purge_protection_enabled   = var.environment == "prod" ? true : false
  sku_name                   = "standard"
  tags                       = local.common_tags

  network_acls {
    bypass                     = "AzureServices"
    default_action             = "Deny"
    ip_rules                   = var.allowed_ip_ranges
    virtual_network_subnet_ids = [azurerm_subnet.app.id]
  }

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get", "List", "Update", "Create", "Import", "Delete", "Recover", "Backup", "Restore"
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"
    ]

    certificate_permissions = [
      "Get", "List", "Update", "Create", "Import", "Delete", "Recover", "Backup", "Restore", "ManageContacts", "ManageIssuers", "GetIssuers", "ListIssuers", "SetIssuers", "DeleteIssuers"
    ]
  }

  # Access policy for backend app service managed identity
  access_policy {
    tenant_id = azurerm_linux_web_app.backend.identity[0].tenant_id
    object_id = azurerm_linux_web_app.backend.identity[0].principal_id

    secret_permissions = [
      "Get", "List"
    ]
  }

  # Access policy for frontend app service managed identity
  access_policy {
    tenant_id = azurerm_linux_web_app.frontend.identity[0].tenant_id
    object_id = azurerm_linux_web_app.frontend.identity[0].principal_id

    secret_permissions = [
      "Get", "List"
    ]
  }
}

# Database Connection String Secret
resource "azurerm_key_vault_secret" "database_connection_string" {
  count        = var.enable_key_vault ? 1 : 0
  name         = "database-connection-string"
  value        = "postgresql://${var.db_admin_username}:${var.db_admin_password}@${azurerm_postgresql_flexible_server.main.fqdn}:5432/${azurerm_postgresql_flexible_server_database.main.name}?sslmode=require"
  key_vault_id = azurerm_key_vault.main[0].id
  tags         = local.common_tags

  depends_on = [azurerm_key_vault.main]
}

# API Secret Key
resource "azurerm_key_vault_secret" "api_secret_key" {
  count        = var.enable_key_vault ? 1 : 0
  name         = "api-secret-key"
  value        = random_password.secret_key.result
  key_vault_id = azurerm_key_vault.main[0].id
  tags         = local.common_tags

  depends_on = [azurerm_key_vault.main]
}

# Container Registry Admin Password
resource "azurerm_key_vault_secret" "acr_admin_password" {
  count        = var.enable_key_vault && var.enable_container_registry ? 1 : 0
  name         = "acr-admin-password"
  value        = azurerm_container_registry.main[0].admin_password
  key_vault_id = azurerm_key_vault.main[0].id
  tags         = local.common_tags

  depends_on = [azurerm_key_vault.main]
}

# Redis Connection String
resource "azurerm_key_vault_secret" "redis_connection_string" {
  count        = var.enable_key_vault && var.enable_redis ? 1 : 0
  name         = "redis-connection-string"
  value        = "redis://${azurerm_redis_cache.main[0].hostname}:${azurerm_redis_cache.main[0].ssl_port}?password=${azurerm_redis_cache.main[0].primary_access_key}&ssl=true"
  key_vault_id = azurerm_key_vault.main[0].id
  tags         = local.common_tags

  depends_on = [azurerm_key_vault.main]
}

# Application Insights Instrumentation Key
resource "azurerm_key_vault_secret" "appinsights_instrumentation_key" {
  count        = var.enable_key_vault && var.enable_application_insights ? 1 : 0
  name         = "appinsights-instrumentation-key"
  value        = azurerm_application_insights.main[0].instrumentation_key
  key_vault_id = azurerm_key_vault.main[0].id
  tags         = local.common_tags

  depends_on = [azurerm_key_vault.main]
}

# SSL Certificate (if provided)
resource "azurerm_key_vault_certificate" "ssl_certificate" {
  count        = var.enable_key_vault && var.ssl_certificate_path != "" ? 1 : 0
  name         = "ssl-certificate"
  key_vault_id = azurerm_key_vault.main[0].id
  tags         = local.common_tags

  certificate {
    contents = filebase64(var.ssl_certificate_path)
    password = var.ssl_certificate_password
  }

  certificate_policy {
    issuer_parameters {
      name = "Self"
    }

    key_properties {
      exportable = true
      key_size   = 2048
      key_type   = "RSA"
      reuse_key  = true
    }

    lifetime_action {
      action {
        action_type = "AutoRenew"
      }

      trigger {
        days_before_expiry = 30
      }
    }

    secret_properties {
      content_type = "application/x-pkcs12"
    }

    x509_certificate_properties {
      key_usage = [
        "cRLSign",
        "dataEncipherment",
        "digitalSignature",
        "keyAgreement",
        "keyEncipherment",
        "keyCertSign",
      ]

      subject            = "CN=${var.custom_domain}"
      validity_in_months = 12

      subject_alternative_names {
        dns_names = [var.custom_domain, "www.${var.custom_domain}"]
      }
    }
  }

  depends_on = [azurerm_key_vault.main]
}

# Diagnostic Settings for Key Vault
resource "azurerm_monitor_diagnostic_setting" "key_vault" {
  count                      = var.enable_key_vault ? 1 : 0
  name                       = "diag-kv-${var.environment}"
  target_resource_id         = azurerm_key_vault.main[0].id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id

  enabled_log {
    category = "AuditEvent"
  }

  enabled_log {
    category = "AzurePolicyEvaluationDetails"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

# Additional variables for security
variable "github_token" {
  description = "GitHub token for webhook authentication"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ssl_certificate_password" {
  description = "Password for SSL certificate"
  type        = string
  default     = ""
  sensitive   = true
}

variable "alert_email_address" {
  description = "Email address for alerts"
  type        = string
  default     = "admin@company.com"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications"
  type        = string
  default     = ""
  sensitive   = true
}