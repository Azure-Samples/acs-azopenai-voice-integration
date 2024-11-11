# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "${local.name_prefix}-${var.resource_group_name}"
  location = var.location
  tags     = local.default_tags

}
