# Azure Communication Service
resource "azurerm_communication_service" "communication_service" {
  name                = "${local.name_prefix}-acs-${local.name_suffix}"
  data_location       = var.acs_data_location
  resource_group_name = azurerm_resource_group.rg.name
  tags                = local.default_tags
}

resource "null_resource" "assign_identity_acs" {
  depends_on = [azurerm_communication_service.communication_service]
  provisioner "local-exec" {
    command = "az communication identity assign --resource-group ${azurerm_resource_group.rg.name} --name ${azurerm_communication_service.communication_service.name} --system-assigned true"
  }
}

resource "null_resource" "python_script_purchase_phone_number" {
  depends_on = [azurerm_communication_service.communication_service]
  provisioner "local-exec" {
    command = "python ${path.module}/purchase_phone_number.py --connection-string ${azurerm_communication_service.communication_service.primary_connection_string}"
  }
  triggers = {
    always = "${timestamp()}"
  }
}
