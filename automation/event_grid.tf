resource "azurerm_eventgrid_system_topic" "system_topic" {
  name                   = "${local.name_prefix}-event-grid-${random_string.unique.result}"
  location               = "global"
  resource_group_name    = azurerm_resource_group.rg.name
  source_arm_resource_id = azurerm_communication_service.communication_service.id
  topic_type             = "Microsoft.Communication.CommunicationServices"

  # Uncomment and modify if using Webhook Event Subscription
  # event_subscription {
  #   webhook_endpoint {
  #     url = var.egWebhookEndpointUrl
  #   }
  # }
}
