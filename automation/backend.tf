terraform {
  backend "azurerm" {
    resource_group_name  = "terraform"
    storage_account_name = "terraform9999"
    container_name       = "aivoice"
    key                  = "terraform.tfstate"
    use_azuread_auth     = true
  }
}
