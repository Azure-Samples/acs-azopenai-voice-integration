terraform {
  required_providers {
    azurerm = {
      version = "4.9.0"
      source  = "hashicorp/azurerm"
    }
    azurecaf = {
      source  = "aztfmod/azurecaf"
      version = "~>1.2.24"
    }
  }
}
# ------------------------------------------------------------------------------------------------------
# Deploy app service web app
# ------------------------------------------------------------------------------------------------------
resource "azurecaf_name" "web_name" {
  name          = "${var.service_name}-${var.resource_token}"
  resource_type = "azurerm_app_service"
  random_length = 0
  clean_input   = true
}

resource "azurerm_linux_web_app" "web" {
  name                                           = var.resource_token
  location                                       = var.location
  resource_group_name                            = var.rg_name
  service_plan_id                                = var.appservice_plan_id
  https_only                                     = true
  tags                                           = var.tags
  ftp_publish_basic_authentication_enabled       = true
  webdeploy_publish_basic_authentication_enabled = true
  site_config {
    always_on         = var.always_on
    use_32_bit_worker = var.use_32_bit_worker
    ftps_state        = "FtpsOnly"
    app_command_line  = var.app_command_line
    application_stack {
      python_version = var.python_version
    }



  }

  app_settings = var.app_settings

  dynamic "identity" {
    for_each = { for k, v in var.identity : k => v if var.identity != [] }
    content {
      type = identity.value["type"]
    }
  }

  logs {
    application_logs {
      file_system_level = "Verbose"
    }
    detailed_error_messages = true
    failed_request_tracing  = true
    http_logs {
      file_system {
        retention_in_days = 1
        retention_in_mb   = 35
      }
    }
  }
  lifecycle {
    ignore_changes = [
      ftp_publish_basic_authentication_enabled,
      webdeploy_publish_basic_authentication_enabled
    ]
  }
}

# This is a temporary solution until the azurerm provider supports the basicPublishingCredentialsPolicies resource type
resource "null_resource" "webapp_basic_auth_disable" {
  triggers = {
    account = azurerm_linux_web_app.web.name
  }

  provisioner "local-exec" {
    command = "az resource update --resource-group ${var.rg_name} --name ftp --namespace Microsoft.Web --resource-type basicPublishingCredentialsPolicies --parent sites/${azurerm_linux_web_app.web.name} --set properties.allow=false && az resource update --resource-group ${var.rg_name} --name scm --namespace Microsoft.Web --resource-type basicPublishingCredentialsPolicies --parent sites/${azurerm_linux_web_app.web.name} --set properties.allow=false"
  }
}
