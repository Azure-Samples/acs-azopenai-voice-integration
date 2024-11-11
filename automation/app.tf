# ------------------------------------------------------------------------------------------------------
# Deploy application insights
# ------------------------------------------------------------------------------------------------------
module "applicationinsights" {
  source           = "./modules/applicationinsights"
  location         = var.location
  rg_name          = azurerm_resource_group.rg.name
  environment_name = var.environment
  workspace_id     = module.loganalytics.LOGANALYTICS_WORKSPACE_ID
  tags             = local.default_tags
  resource_token   = "${local.name_prefix}-appinsights"
}

# ------------------------------------------------------------------------------------------------------
# Deploy log analytics
# ------------------------------------------------------------------------------------------------------
module "loganalytics" {
  source         = "./modules/loganalytics"
  location       = var.location
  rg_name        = azurerm_resource_group.rg.name
  tags           = local.default_tags
  resource_token = "${local.name_prefix}-loganalytics"
}

# ------------------------------------------------------------------------------------------------------
# Deploy app service plan
# ------------------------------------------------------------------------------------------------------
module "appserviceplan" {
  source         = "./modules/appserviceplan"
  location       = var.location
  rg_name        = azurerm_resource_group.rg.name
  tags           = local.default_tags
  resource_token = "${local.name_prefix}-appserviceplan"
  sku_name       = "B3"
}

# ------------------------------------------------------------------------------------------------------
# Deploy app service api
# ------------------------------------------------------------------------------------------------------
module "api" {
  source             = "./modules/appservicepython"
  location           = var.location
  rg_name            = azurerm_resource_group.rg.name
  resource_token     = "${local.name_prefix}-api"
  tags               = merge(local.default_tags, { "api" = "api" })
  service_name       = "api"
  appservice_plan_id = module.appserviceplan.APPSERVICE_PLAN_ID
  app_settings = {
    # "AZURE_COSMOS_CONNECTION_STRING_KEY" = local.cosmos_connection_string_key
    # "AZURE_COSMOS_DATABASE_NAME"         = module.cosmos.AZURE_COSMOS_DATABASE_NAME
    "SCM_DO_BUILD_DURING_DEPLOYMENT" = "true"
    # "AZURE_KEY_VAULT_ENDPOINT"              = module.keyvault.AZURE_KEY_VAULT_ENDPOINT
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = module.applicationinsights.APPLICATIONINSIGHTS_CONNECTION_STRING
  }
  health_check_path = "/api/health"
  app_command_line  = local.api_command_line
  identity = [{
    type = "SystemAssigned"
  }]
}

# Workaround: set API_ALLOW_ORIGINS to the web app URI
resource "null_resource" "api_set_allow_origins" {
  # triggers = {
  #   web_uri = module.web.URI
  # }

  provisioner "local-exec" {
    # command = "az webapp config appsettings set --resource-group ${azurerm_resource_group.rg.name} --name ${module.api.APPSERVICE_NAME} --settings API_ALLOW_ORIGINS=${module.web.URI}"
    command = "az webapp config appsettings set --resource-group ${azurerm_resource_group.rg.name} --name ${module.api.APPSERVICE_NAME} --settings API_ALLOW_ORIGINS=*"
  }
}
