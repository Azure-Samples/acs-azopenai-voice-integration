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

data "archive_file" "api_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../api"
  output_path = "${path.module}/api_zip.zip"
  excludes    = [".vscode", "__pycache__"]
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
    "SCM_DO_BUILD_DURING_DEPLOYMENT"        = "true"
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = module.applicationinsights.APPLICATIONINSIGHTS_CONNECTION_STRING
    #ACS
    "ACS_CONNECTION_STRING"      = azurerm_communication_service.communication_service.primary_connection_string
    "COGNITIVE_SERVICE_ENDPOINT" = azurerm_cognitive_account.CognitiveServices.endpoint
    "AGENT_PHONE_NUMBER"         = "AGENT_PHONE_NUMBER"
    "VOICE_NAME"                 = "en-US-AvaMultilingualNeural"
    # Azure OpenAI
    "AZURE_OPENAI_SERVICE_KEY"         = azurerm_cognitive_account.openai.primary_access_key
    AZURE_OPENAI_SERVICE_ENDPOINT      = azurerm_cognitive_account.openai.endpoint
    AZURE_OPENAI_DEPLOYMENT_MODEL_NAME = azurerm_cognitive_deployment.openai_deployments["gpt-4o"].model[0].name
    AZURE_OPENAI_DEPLOYMENT_MODEL      = azurerm_cognitive_deployment.openai_deployments["gpt-4o"].model[0].name
    # Application Settings
    CALLBACK_URI_HOST   = "https://${local.name_prefix}-api.azurewebsites.net"
    CALLBACK_EVENTS_URI = "https://${local.name_prefix}-api.azurewebsites.net/api/callbacks"
    END_SILENCE_TIMEOUT = "0.5"

  }
  health_check_path = "/api/health"
  app_command_line  = local.api_command_line
  identity = [{
    type = "SystemAssigned"
  }]


}

# Workaround: set API_ALLOW_ORIGINS to the web app URI
resource "null_resource" "api_set_allow_origins" {
  depends_on = [module.api]
  provisioner "local-exec" {
    # command = "az webapp config appsettings set --resource-group ${azurerm_resource_group.rg.name} --name ${module.api.APPSERVICE_NAME} --settings API_ALLOW_ORIGINS=${module.web.URI}"
    command = "az webapp config appsettings set --resource-group ${azurerm_resource_group.rg.name} --name ${module.api.APPSERVICE_NAME} --settings API_ALLOW_ORIGINS=*"
  }
}

resource "null_resource" "deploy_app" {
  depends_on = [null_resource.api_set_allow_origins]
  provisioner "local-exec" {
    command = "az webapp deployment source config-zip --resource-group ${azurerm_resource_group.rg.name} --name ${module.api.APPSERVICE_NAME} --src ${data.archive_file.api_zip.output_path}"
  }
}
