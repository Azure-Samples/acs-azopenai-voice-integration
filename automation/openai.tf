
variable "openai_deployments" {
  description = "(Optional) Specifies the deployments of the Azure OpenAI Service"
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
      # tier     = string
    })
  }))
  default = [
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
    },
    {
      name = "text-embedding-ada-002"
      model = {
        format  = "OpenAI"
        name    = "text-embedding-ada-002"
        version = "2"
      }
      sku = {
        name     = "Standard"
        capacity = 10
      }
    }
  ]
}

resource "azurerm_cognitive_account" "openai" {
  resource_group_name           = azurerm_resource_group.rg.name
  custom_subdomain_name         = "${local.name_prefix}-openai-${random_string.unique.result}"
  kind                          = "OpenAI"
  local_auth_enabled            = true
  location                      = var.openai_location
  name                          = "${local.name_prefix}-openai"
  public_network_access_enabled = true
  sku_name                      = var.openai_sku
  tags                          = local.default_tags
  identity {
    type = "SystemAssigned"
  }

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}

resource "azurerm_cognitive_deployment" "openai_deployments" {
  for_each               = { for deployment in var.openai_deployments : deployment.name => deployment }
  cognitive_account_id   = azurerm_cognitive_account.openai.id
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
    # tier     = each.value.sku.tier
  }

}

resource "azurerm_monitor_diagnostic_setting" "settings" {
  name                       = "${local.name_prefix}-openai-diagnostic"
  target_resource_id         = azurerm_cognitive_account.openai.id
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


# output "openai_deployment_dev_id" {
#   value = azurerm_cognitive_deployment.gpt_4o["dev"].id
# # }

# ####==========Create AI Search Service ======#####
# resource "azurerm_search_service" "ai-search-service" {
#   name                = var.ai_search_name
#   resource_group_name = azurerm_resource_group.rg.name
#   location            = var.location
#   sku                 = var.ai_search_sku

#   local_authentication_enabled = true
#   authentication_failure_mode  = "http403"
# }
