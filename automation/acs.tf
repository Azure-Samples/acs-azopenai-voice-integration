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


## Communication Services - Phone Numbers
# resource "azurerm_communication_service_phone_number" "phone_number" {
#   communication_service_id = azurerm_communication_service.communication_service.id
#   phone_number             = var.phone_number
#   phone_number_type        = "Calling"
# }
# output "phone_number_id" {
#   value = azurerm_communication_service_phone_number.phone_number.id
# }
# output "phone_number" {
#   value = azurerm_communication_service_phone_number.phone_number.phone_number
# }
# output "phone_number_type" {
#   value = azurerm_communication_service_phone_number.phone_number.phone_number_type
# }
# output "phone_number_capabilities" {
#   value = azurerm_communication_service_phone_number.phone_number.capabilities
# }
# output "phone_number_country_code" {
#   value = azurerm_communication_service_phone_number.phone_number.country_code
# }
# output "phone_number_city" {
#   value = azurerm_communication_service_phone_number.phone_number.city
# }
# output "phone_number_state" {
#   value = azurerm_communication_service_phone_number.phone_number.state
# }
# output "phone_number_postal_code" {
#   value = azurerm_communication_service_phone_number.phone_number.postal_code
# } output "phone_number_toll_free" {
# value = azurerm_communication_service_phone_number.phone_number.toll_free
# }
# output "phone_number_sms_capable" {
#   value = azurerm_communication_service_phone_number.phone_number.sms_capable
# }
# output "phone_number_voice_capable" {
#   value = azurerm_communication_service_phone_number.phone_number.voice_capable
# }
# output "phone_number_phone_number_type" {
#   value = azurerm_communication_service_phone_number.phone_number.phone_number_type
# }

# Cognitive Service connect with ACS
# Enable Identity role for ACS

