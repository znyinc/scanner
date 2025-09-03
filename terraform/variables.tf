# General Variables
variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "stockscanner"
  
  validation {
    condition     = can(regex("^[a-z0-9]+$", var.app_name))
    error_message = "App name must contain only lowercase letters and numbers."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "location" {
  description = "Azure region for resources"
  type        = string
  default     = "East US 2"
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "Platform Team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "Engineering"
}

# Database Variables
variable "db_admin_username" {
  description = "Database administrator username"
  type        = string
  default     = "stockscanner_admin"
}

variable "db_admin_password" {
  description = "Database administrator password"
  type        = string
  sensitive   = true
  
  validation {
    condition     = length(var.db_admin_password) >= 12
    error_message = "Database password must be at least 12 characters long."
  }
}

variable "db_sku_name" {
  description = "Database SKU name"
  type        = string
  default     = "GP_Standard_D2s_v3"
  
  validation {
    condition = contains([
      "B_Standard_B1ms", "B_Standard_B2s", 
      "GP_Standard_D2s_v3", "GP_Standard_D4s_v3", "GP_Standard_D8s_v3",
      "MO_Standard_E2s_v3", "MO_Standard_E4s_v3", "MO_Standard_E8s_v3"
    ], var.db_sku_name)
    error_message = "Invalid database SKU name."
  }
}

variable "db_storage_mb" {
  description = "Database storage in MB"
  type        = number
  default     = 131072 # 128GB
  
  validation {
    condition     = var.db_storage_mb >= 32768 && var.db_storage_mb <= 33554432
    error_message = "Database storage must be between 32GB and 32TB."
  }
}

variable "db_backup_retention_days" {
  description = "Database backup retention period in days"
  type        = number
  default     = 30
  
  validation {
    condition     = var.db_backup_retention_days >= 7 && var.db_backup_retention_days <= 35
    error_message = "Backup retention must be between 7 and 35 days."
  }
}

variable "enable_high_availability" {
  description = "Enable high availability for database"
  type        = bool
  default     = true
}

# App Service Variables
variable "app_service_sku_name" {
  description = "App Service plan SKU"
  type        = string
  default     = "S2"
  
  validation {
    condition = contains([
      "B1", "B2", "B3",
      "S1", "S2", "S3",
      "P1v2", "P2v2", "P3v2",
      "P1v3", "P2v3", "P3v3"
    ], var.app_service_sku_name)
    error_message = "Invalid App Service SKU name."
  }
}

# Auto-scaling Variables
variable "autoscale_min_capacity" {
  description = "Minimum number of instances for auto-scaling"
  type        = number
  default     = 1
  
  validation {
    condition     = var.autoscale_min_capacity >= 1 && var.autoscale_min_capacity <= 10
    error_message = "Minimum capacity must be between 1 and 10."
  }
}

variable "autoscale_max_capacity" {
  description = "Maximum number of instances for auto-scaling"
  type        = number
  default     = 10
  
  validation {
    condition     = var.autoscale_max_capacity >= 1 && var.autoscale_max_capacity <= 30
    error_message = "Maximum capacity must be between 1 and 30."
  }
}

variable "autoscale_default_capacity" {
  description = "Default number of instances for auto-scaling"
  type        = number
  default     = 2
  
  validation {
    condition     = var.autoscale_default_capacity >= 1 && var.autoscale_default_capacity <= 10
    error_message = "Default capacity must be between 1 and 10."
  }
}

# Container Registry Variables
variable "acr_sku" {
  description = "Azure Container Registry SKU"
  type        = string
  default     = "Standard"
  
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.acr_sku)
    error_message = "ACR SKU must be Basic, Standard, or Premium."
  }
}

# Monitoring Variables
variable "log_analytics_retention_days" {
  description = "Log Analytics workspace retention period in days"
  type        = number
  default     = 30
  
  validation {
    condition     = var.log_analytics_retention_days >= 30 && var.log_analytics_retention_days <= 730
    error_message = "Log retention must be between 30 and 730 days."
  }
}

# Network Variables
variable "vnet_address_space" {
  description = "Virtual network address space"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "app_subnet_address_prefixes" {
  description = "Application subnet address prefixes"
  type        = list(string)
  default     = ["10.0.1.0/24"]
}

variable "db_subnet_address_prefixes" {
  description = "Database subnet address prefixes"
  type        = list(string)
  default     = ["10.0.2.0/24"]
}

variable "appgw_subnet_address_prefixes" {
  description = "Application Gateway subnet address prefixes"
  type        = list(string)
  default     = ["10.0.3.0/24"]
}

# Security Variables
variable "allowed_ip_ranges" {
  description = "List of IP ranges allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Change this for production
}

variable "enable_waf" {
  description = "Enable Web Application Firewall"
  type        = bool
  default     = true
}

# Feature Flags
variable "enable_container_registry" {
  description = "Enable Azure Container Registry"
  type        = bool
  default     = true
}

variable "enable_key_vault" {
  description = "Enable Azure Key Vault"
  type        = bool
  default     = true
}

variable "enable_application_insights" {
  description = "Enable Application Insights"
  type        = bool
  default     = true
}

variable "enable_front_door" {
  description = "Enable Azure Front Door"
  type        = bool
  default     = false
}

variable "enable_redis" {
  description = "Enable Azure Cache for Redis"
  type        = bool
  default     = true
}

# Domain Variables
variable "custom_domain" {
  description = "Custom domain name for the application"
  type        = string
  default     = ""
}

variable "ssl_certificate_path" {
  description = "Path to SSL certificate file"
  type        = string
  default     = ""
}