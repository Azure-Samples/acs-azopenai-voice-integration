# Resource Group
resource "azurerm_resource_group" "rg" {
  name     = "${local.name_prefix}-${var.resource_group_name}-${local.name_suffix}"
  location = var.location
  tags     = local.default_tags

}
