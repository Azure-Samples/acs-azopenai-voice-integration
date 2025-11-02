
# Variable for AI model deployments
variable "ai_foundry_deployments" {
  description = "(Optional) Specifies the deployments for Azure AI Foundry"
  type = list(object({
    name = string
    model = object({
      format  = string
      name    = string
      version = string
    })
    sku = object({
      name     = string
      capacity = number
    })
  }))
  default = [
    {
      name = "gpt-realtime"
      model = {
        format  = "OpenAI"
        name    = "gpt-4o-realtime-preview"
        version = "2024-10-01"
      }
      sku = {
        name     = "GlobalStandard"
        capacity = 10
      }
    },
    {
      name = "gpt-4o"
      model = {
        format  = "OpenAI"
        name    = "gpt-4o"
        version = "2024-08-06"
      }
      sku = {
        name     = "GlobalStandard"
        capacity = 10
      }
    }
  ]
}

# Deploy Azure AI Services resource (following Microsoft docs pattern)
resource "azurerm_ai_services" "ai_foundry" {
  name                  = "${local.name_prefix}-ai-services-${local.name_suffix}"
  location              = var.openai_location
  resource_group_name   = azurerm_resource_group.rg.name
  sku_name              = "S0"
  custom_subdomain_name = "${local.name_prefix}-ai-services-${local.name_suffix}"
  tags                  = local.default_tags
}

# Create Azure AI Foundry Hub (following Microsoft docs pattern)
resource "azurerm_ai_foundry" "hub" {
  name                = "${local.name_prefix}-ai-hub-${local.name_suffix}"
  location            = var.openai_location
  resource_group_name = azurerm_resource_group.rg.name
  storage_account_id  = azurerm_storage_account.ai_storage.id
  key_vault_id        = azurerm_key_vault.ai_keyvault.id
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = local.default_tags
}

# Create an AI Foundry Project within the AI Foundry Hub
resource "azurerm_ai_foundry_project" "project" {
  name               = "${local.name_prefix}-ai-project"
  location           = var.openai_location
  ai_services_hub_id = azurerm_ai_foundry.hub.id
  
  identity {
    type = "SystemAssigned"
  }
  
  tags = local.default_tags
}

# Storage Account for AI Foundry (name must be 3-24 characters, lowercase, alphanumeric only)
resource "azurerm_storage_account" "ai_storage" {
  name                     = substr(replace(lower("${local.name_prefix}aist${local.name_suffix}"), "-", ""), 0, 24)
  location                 = var.openai_location
  resource_group_name      = azurerm_resource_group.rg.name
  account_tier             = "Standard"
  account_replication_type = "LRS"
  tags                     = local.default_tags
}

# Key Vault for AI Foundry (name must be 3-24 characters)
resource "azurerm_key_vault" "ai_keyvault" {
  name                     = substr(replace("${local.name_prefix}aikv${local.name_suffix}", "-", ""), 0, 24)
  location                 = var.openai_location
  resource_group_name      = azurerm_resource_group.rg.name
  tenant_id                = data.azurerm_client_config.current.tenant_id
  sku_name                 = "standard"
  purge_protection_enabled = true
  tags                     = local.default_tags
}

# Set an access policy for the Key Vault
resource "azurerm_key_vault_access_policy" "ai_policy" {
  key_vault_id = azurerm_key_vault.ai_keyvault.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id
  
  key_permissions = [
    "Create",
    "Get",
    "Delete",
    "Purge",
    "GetRotationPolicy",
  ]
}

# Model deployments on AI Services
resource "azurerm_cognitive_deployment" "ai_foundry_deployments" {
  for_each               = { for deployment in var.ai_foundry_deployments : deployment.name => deployment }
  cognitive_account_id   = azurerm_ai_services.ai_foundry.id
  name                   = each.key
  version_upgrade_option = "OnceNewDefaultVersionAvailable"

  model {
    format  = each.value.model.format
    name    = each.value.model.name
    version = each.value.model.version
  }

  sku {
    name     = each.value.sku.name
    capacity = each.value.sku.capacity
  }
}

# Diagnostic settings for AI Services
resource "azurerm_monitor_diagnostic_setting" "ai_foundry_diagnostic" {
  name                       = "${local.name_prefix}-ai-foundry-diagnostic"
  target_resource_id         = azurerm_ai_services.ai_foundry.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.log_analytics_workspace.id

  metric {
    category = "AllMetrics"
  }

  enabled_log {
    category = "Audit"
  }

  enabled_log {
    category = "RequestResponse"
  }

  enabled_log {
    category = "Trace"
  }
}
