resource "azurerm_eventgrid_system_topic" "system_topic" {
  name                   = "${local.name_prefix}-event-grid-${random_string.unique.result}"
  location               = "global"
  resource_group_name    = azurerm_resource_group.rg.name
  source_arm_resource_id = azurerm_communication_service.communication_service.id
  topic_type             = "Microsoft.Communication.CommunicationServices"
}

resource "azurerm_eventgrid_system_topic_event_subscription" "webapp_event_subscription" {
  depends_on          = [module.api, azurerm_eventgrid_system_topic.system_topic]
  name                = "${local.name_prefix}-acs-api-event-sub-${random_string.unique.result}"
  system_topic        = azurerm_eventgrid_system_topic.system_topic.name
  resource_group_name = azurerm_resource_group.rg.name

  webhook_endpoint {
    url = "https://${local.name_prefix}-api.azurewebsites.net/api/incomingCall"
  }
}
