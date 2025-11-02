terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-fi30"
    storage_account_name = "terraformstorefi30"
    container_name       = "tfstate"
    key                  = "terraform.tfstate"
    subscription_id      = "70df6e57-6415-415c-a8d9-1a147c26f2e3"
    use_azuread_auth     = true
  }
}
