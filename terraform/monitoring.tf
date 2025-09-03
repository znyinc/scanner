# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.resource_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.log_analytics_retention_days
  tags                = local.common_tags
}

# Application Insights
resource "azurerm_application_insights" "main" {
  count               = var.enable_application_insights ? 1 : 0
  name                = "appi-${local.resource_prefix}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = local.common_tags
}

# Action Group for Alerts
resource "azurerm_monitor_action_group" "main" {
  name                = "ag-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = substr("${var.app_name}${var.environment}", 0, 12)
  tags                = local.common_tags

  email_receiver {
    name          = "admin-email"
    email_address = var.alert_email_address
  }

  webhook_receiver {
    name        = "slack-webhook"
    service_uri = var.slack_webhook_url
  }
}

# CPU Alert for App Service
resource "azurerm_monitor_metric_alert" "cpu_alert" {
  name                = "alert-cpu-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_service_plan.main.id]
  description         = "High CPU usage detected"
  severity            = 2
  window_size         = "PT5M"
  frequency           = "PT1M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.Web/serverfarms"
    metric_name      = "CpuPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Memory Alert for App Service
resource "azurerm_monitor_metric_alert" "memory_alert" {
  name                = "alert-memory-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_service_plan.main.id]
  description         = "High memory usage detected"
  severity            = 2
  window_size         = "PT5M"
  frequency           = "PT1M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.Web/serverfarms"
    metric_name      = "MemoryPercentage"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Response Time Alert for Backend
resource "azurerm_monitor_metric_alert" "response_time_alert" {
  name                = "alert-response-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "High response time detected"
  severity            = 2
  window_size         = "PT5M"
  frequency           = "PT1M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "AverageResponseTime"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 5 # 5 seconds
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# HTTP 5xx Errors Alert
resource "azurerm_monitor_metric_alert" "http_5xx_alert" {
  name                = "alert-http5xx-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_web_app.backend.id]
  description         = "High number of HTTP 5xx errors detected"
  severity            = 1
  window_size         = "PT5M"
  frequency           = "PT1M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.Web/sites"
    metric_name      = "Http5xx"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 10
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Database Connection Alert
resource "azurerm_monitor_metric_alert" "db_connection_alert" {
  name                = "alert-db-connections-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_postgresql_flexible_server.main.id]
  description         = "High database connection usage detected"
  severity            = 2
  window_size         = "PT5M"
  frequency           = "PT1M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.DBforPostgreSQL/flexibleServers"
    metric_name      = "active_connections"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 150 # 75% of max_connections (200)
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Database CPU Alert
resource "azurerm_monitor_metric_alert" "db_cpu_alert" {
  name                = "alert-db-cpu-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_postgresql_flexible_server.main.id]
  description         = "High database CPU usage detected"
  severity            = 2
  window_size         = "PT10M"
  frequency           = "PT5M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.DBforPostgreSQL/flexibleServers"
    metric_name      = "cpu_percent"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Database Storage Alert
resource "azurerm_monitor_metric_alert" "db_storage_alert" {
  name                = "alert-db-storage-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_postgresql_flexible_server.main.id]
  description         = "High database storage usage detected"
  severity            = 1
  window_size         = "PT15M"
  frequency           = "PT5M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.DBforPostgreSQL/flexibleServers"
    metric_name      = "storage_percent"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 85
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Availability Test for Frontend
resource "azurerm_application_insights_web_test" "frontend_availability" {
  count                   = var.enable_application_insights ? 1 : 0
  name                    = "webtest-frontend-${var.environment}"
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  application_insights_id = azurerm_application_insights.main[0].id
  kind                    = "ping"
  frequency               = 300 # 5 minutes
  timeout                 = 30
  enabled                 = true
  geo_locations           = ["us-va-ash-azr", "us-ca-sjc-azr", "us-tx-sn1-azr"]
  tags                    = local.common_tags

  configuration = <<XML
<WebTest Name="Frontend Availability Test" Id="ABD48585-0831-40CB-9069-682A25A54A6B" Enabled="True" CssProjectStructure="" CssIteration="" Timeout="30" WorkItemIds="" xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010" Description="" CredentialUserName="" CredentialPassword="" PreAuthenticate="True" Proxy="default" StopOnError="False" RecordedResultFile="" ResultsLocale="">
  <Items>
    <Request Method="GET" Guid="a5f10126-e4cd-570d-961c-cea43999a200" Version="1.1" Url="https://${azurerm_linux_web_app.frontend.default_hostname}" ThinkTime="0" Timeout="30" ParseDependentRequests="False" FollowRedirects="True" RecordResult="True" Cache="False" ResponseTimeGoal="0" Encoding="utf-8" ExpectedHttpStatusCode="200" ExpectedResponseUrl="" ReportingName="" IgnoreHttpStatusCode="False" />
  </Items>
</WebTest>
XML
}

# Availability Test for Backend API
resource "azurerm_application_insights_web_test" "backend_availability" {
  count                   = var.enable_application_insights ? 1 : 0
  name                    = "webtest-backend-${var.environment}"
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  application_insights_id = azurerm_application_insights.main[0].id
  kind                    = "ping"
  frequency               = 300 # 5 minutes
  timeout                 = 30
  enabled                 = true
  geo_locations           = ["us-va-ash-azr", "us-ca-sjc-azr", "us-tx-sn1-azr"]
  tags                    = local.common_tags

  configuration = <<XML
<WebTest Name="Backend API Availability Test" Id="ABD48585-0831-40CB-9069-682A25A54A6C" Enabled="True" CssProjectStructure="" CssIteration="" Timeout="30" WorkItemIds="" xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010" Description="" CredentialUserName="" CredentialPassword="" PreAuthenticate="True" Proxy="default" StopOnError="False" RecordedResultFile="" ResultsLocale="">
  <Items>
    <Request Method="GET" Guid="a5f10126-e4cd-570d-961c-cea43999a201" Version="1.1" Url="https://${azurerm_linux_web_app.backend.default_hostname}/health" ThinkTime="0" Timeout="30" ParseDependentRequests="False" FollowRedirects="True" RecordResult="True" Cache="False" ResponseTimeGoal="0" Encoding="utf-8" ExpectedHttpStatusCode="200" ExpectedResponseUrl="" ReportingName="" IgnoreHttpStatusCode="False" />
  </Items>
</WebTest>
XML
}

# Availability Alert for Frontend
resource "azurerm_monitor_metric_alert" "frontend_availability_alert" {
  count               = var.enable_application_insights ? 1 : 0
  name                = "alert-frontend-availability-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights_web_test.frontend_availability[0].id]
  description         = "Frontend availability is below threshold"
  severity            = 1
  window_size         = "PT5M"
  frequency           = "PT1M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.Insights/webtests"
    metric_name      = "availabilityResults/availabilityPercentage"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 90
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}

# Availability Alert for Backend
resource "azurerm_monitor_metric_alert" "backend_availability_alert" {
  count               = var.enable_application_insights ? 1 : 0
  name                = "alert-backend-availability-${local.resource_prefix}"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_application_insights_web_test.backend_availability[0].id]
  description         = "Backend API availability is below threshold"
  severity            = 1
  window_size         = "PT5M"
  frequency           = "PT1M"
  tags                = local.common_tags

  criteria {
    metric_namespace = "Microsoft.Insights/webtests"
    metric_name      = "availabilityResults/availabilityPercentage"
    aggregation      = "Average"
    operator         = "LessThan"
    threshold        = 95
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }
}