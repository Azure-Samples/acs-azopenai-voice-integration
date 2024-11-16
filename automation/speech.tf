#Speech, CognitiveServices
resource "azurerm_cognitive_account" "CognitiveServices" {
  resource_group_name           = azurerm_resource_group.rg.name
  custom_subdomain_name         = "${local.name_prefix}-ai-voice-${random_string.unique.result}"
  kind                          = "CognitiveServices"
  local_auth_enabled            = true
  location                      = var.voice_location
  name                          = "${local.name_prefix}-ai-voice"
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

output "cognitive_deployment_id" {
  value = azurerm_cognitive_account.CognitiveServices.id
}
