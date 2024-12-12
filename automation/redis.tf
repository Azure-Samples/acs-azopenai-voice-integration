# Redis Cache resource
resource "azurerm_redis_cache" "redis" {
  name                = "${local.name_prefix}-callsession-${random_string.unique.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  zones               = ["1", "2", "3"]

  redis_version = "6"
  sku_name      = "Premium"
  family        = "P"
  capacity      = 1


  non_ssl_port_enabled = false
  minimum_tls_version  = "1.2"

  public_network_access_enabled = true
  shard_count                   = 1
  replicas_per_master           = 3
  replicas_per_primary          = 3

  #access_keys_authentication_enabled = false

  redis_configuration {
    maxmemory_reserved              = 642
    maxfragmentationmemory_reserved = 642
    maxmemory_delta                 = 642
    maxmemory_policy                = "volatile-lru"
  }
}
