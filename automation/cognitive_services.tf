#Speech, CognitiveServices
resource "azurerm_cognitive_account" "CognitiveServices" {
  resource_group_name           = azurerm_resource_group.rg.name
  custom_subdomain_name         = "${local.name_prefix}-ai-voice-${local.name_suffix}"
  kind                          = "CognitiveServices"
  local_auth_enabled            = true
  location                      = var.voice_location
  name                          = "${local.name_prefix}-ai-voice-${local.name_suffix}"
  public_network_access_enabled = true
  sku_name                      = var.speech_sku
  tags                          = local.default_tags
  identity {
    type = "SystemAssigned"
  }

  lifecycle {
    ignore_changes = [
      tags
    ]
  }
}
