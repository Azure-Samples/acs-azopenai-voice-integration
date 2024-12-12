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


resource "null_resource" "python_script_purchase_phone_number" {
  depends_on = [azurerm_communication_service.communication_service]
  provisioner "local-exec" {
    command = "python ${path.module}/purchase_phone_number.py --connection-string ${azurerm_communication_service.communication_service.primary_connection_string}"
  }
}

data "local_file" "phone_number" {
  depends_on = [null_resource.python_script_purchase_phone_number]
  filename   = "${path.module}/phone_number_result.json"
}

locals {
  phone_result = jsondecode(data.local_file.phone_number.content)
  # Extract just the phone number string from the parsed JSON
  phone_number_value = local.phone_result.phone_number
}
