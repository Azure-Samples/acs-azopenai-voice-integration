
output "cognitive_deployment_id" {
  value = azurerm_cognitive_account.CognitiveServices.id
}

output "ai_foundry_hub_id" {
  value = azurerm_ai_foundry.hub.id
}

output "ai_foundry_hub_name" {
  value = azurerm_ai_foundry.hub.name
}

output "ai_foundry_project_id" {
  value = azurerm_ai_foundry_project.project.id
}

output "ai_foundry_project_name" {
  value = azurerm_ai_foundry_project.project.name
}

output "ai_services_endpoint" {
  value = azurerm_ai_services.ai_foundry.endpoint
}

output "ai_foundry_deployments" {
  value = azurerm_cognitive_deployment.ai_foundry_deployments
}
