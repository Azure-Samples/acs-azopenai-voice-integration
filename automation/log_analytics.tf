resource "azurerm_log_analytics_workspace" "log_analytics_workspace" {
  name                = "${local.name_prefix}-law"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = var.log_analytics_sku
  tags                = local.default_tags
  retention_in_days   = var.log_analytics_retention_days

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}