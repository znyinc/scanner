# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "${local.resource_prefix}-db"
  resource_group_name    = azurerm_resource_group.main.name
  location              = azurerm_resource_group.main.location
  version               = "15"
  delegated_subnet_id   = azurerm_subnet.db.id
  private_dns_zone_id   = azurerm_private_dns_zone.postgres.id
  administrator_login    = var.db_admin_username
  administrator_password = var.db_admin_password
  zone                  = "1"
  
  storage_mb                   = var.db_storage_mb
  storage_tier                = "P4"
  auto_grow_enabled           = true
  
  sku_name = var.db_sku_name
  
  backup_retention_days        = var.db_backup_retention_days
  geo_redundant_backup_enabled = var.environment == "prod" ? true : false
  
  dynamic "high_availability" {
    for_each = var.enable_high_availability ? [1] : []
    content {
      mode                      = "ZoneRedundant"
      standby_availability_zone = "2"
    }
  }

  dynamic "maintenance_window" {
    for_each = var.environment == "prod" ? [1] : []
    content {
      day_of_week  = 0  # Sunday
      start_hour   = 2  # 2 AM
      start_minute = 0
    }
  }

  tags = local.common_tags

  depends_on = [azurerm_private_dns_zone_virtual_network_link.postgres]
}

# PostgreSQL Database
resource "azurerm_postgresql_flexible_server_database" "main" {
  name      = var.app_name
  server_id = azurerm_postgresql_flexible_server.main.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

# PostgreSQL Configuration
resource "azurerm_postgresql_flexible_server_configuration" "max_connections" {
  name      = "max_connections"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "200"
}

resource "azurerm_postgresql_flexible_server_configuration" "shared_preload_libraries" {
  name      = "shared_preload_libraries"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "pg_stat_statements"
}

resource "azurerm_postgresql_flexible_server_configuration" "log_statement" {
  name      = "log_statement"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = var.environment == "prod" ? "none" : "all"
}

resource "azurerm_postgresql_flexible_server_configuration" "log_min_duration_statement" {
  name      = "log_min_duration_statement"
  server_id = azurerm_postgresql_flexible_server.main.id
  value     = "1000" # Log queries taking more than 1 second
}

# Read Replica (for production only)
resource "azurerm_postgresql_flexible_server" "read_replica" {
  count                         = var.environment == "prod" ? 1 : 0
  name                         = "${local.resource_prefix}-db-replica"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = "West US 2" # Different region for disaster recovery
  create_mode                  = "Replica"
  source_server_id             = azurerm_postgresql_flexible_server.main.id
  
  tags = local.common_tags
}

# Azure Cache for Redis
resource "azurerm_redis_cache" "main" {
  count               = var.enable_redis ? 1 : 0
  name                = "${local.resource_prefix}-redis"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = var.environment == "prod" ? 2 : 1
  family              = var.environment == "prod" ? "P" : "C"
  sku_name            = var.environment == "prod" ? "Premium" : "Standard"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"
  
  dynamic "patch_schedule" {
    for_each = var.environment == "prod" ? [1] : []
    content {
      day_of_week    = "Sunday"
      start_hour_utc = 2
    }
  }

  redis_configuration {
    enable_authentication = true
    maxmemory_reserved     = var.environment == "prod" ? 200 : 50
    maxmemory_delta        = var.environment == "prod" ? 200 : 50
    maxmemory_policy       = "allkeys-lru"
  }

  tags = local.common_tags
}

# Redis Firewall Rules
resource "azurerm_redis_firewall_rule" "app_service" {
  count               = var.enable_redis ? 1 : 0
  name                = "AllowAppService"
  redis_cache_name    = azurerm_redis_cache.main[0].name
  resource_group_name = azurerm_resource_group.main.name
  start_ip            = azurerm_linux_web_app.backend.outbound_ip_address_list[0]
  end_ip              = azurerm_linux_web_app.backend.outbound_ip_address_list[0]
}