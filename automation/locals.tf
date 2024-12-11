locals {
  name_prefix    = "${var.prefix}${var.name}-${var.environment}"
  sha            = base64encode(sha256("${local.name_prefix}${var.environment}${var.location}${data.azurerm_client_config.current.subscription_id}"))
  resource_token = substr(replace(lower(local.sha), "[^A-Za-z0-9_]", ""), 0, 13)
  # api_command_line = "uvicorn main:app --host 0.0.0.0 --port 8000"
  api_command_line = "hypercorn --bind 0.0.0.0 main:app"

  default_tags = {
    Region      = var.location
    Environment = var.environment
    Owner       = "AI-TEAM"
    Project     = "AI-TRANSLATOR"
    Stage       = "TRANSLATION-SERVICE"
    ManagedBy   = "TERRAFORM"
    CostCenter  = "AI-TEAM"
  }
}
