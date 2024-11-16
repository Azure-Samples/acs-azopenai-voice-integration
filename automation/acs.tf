# Azure Communication Service
resource "azurerm_communication_service" "communication_service" {
  name                = "${local.name_prefix}-acs-${random_string.unique.result}"
  data_location       = var.acs_data_location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = local.default_tags
}


output "acs_id" {
  value = azurerm_communication_service.communication_service.id
}

output "connection_string" {
  value     = azurerm_communication_service.communication_service.primary_connection_string
  sensitive = true

}
output "acs_key" {
  value     = azurerm_communication_service.communication_service.primary_key
  sensitive = true
}
