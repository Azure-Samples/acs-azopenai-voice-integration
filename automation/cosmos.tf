# Generate a random complex password
resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "azurerm_cosmosdb_account" "call_session_account" {
  name                = "${local.name_prefix}-callsession-${random_string.unique.result}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"



  consistency_policy {
    consistency_level       = "Session"
    max_interval_in_seconds = 5
    max_staleness_prefix    = 100
  }

  geo_location {
    location          = azurerm_resource_group.rg.location
    failover_priority = 0
    zone_redundant    = false
  }



  is_virtual_network_filter_enabled = false
  public_network_access_enabled     = true
  analytical_storage_enabled        = false
  minimal_tls_version               = "Tls12"

  multiple_write_locations_enabled   = false
  automatic_failover_enabled         = false
  free_tier_enabled                  = false
  access_key_metadata_writes_enabled = false


  backup {
    type                = "Periodic"
    storage_redundancy  = "Geo"
    interval_in_minutes = 240
    retention_in_hours  = 8
  }
  capabilities {
    name = "EnableServerless"
  }

  capacity {
    total_throughput_limit = 4000
  }
  tags = local.default_tags

}

resource "azurerm_cosmosdb_sql_database" "call_session_db" {
  name                = "CallSessionsDB"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.call_session_account.name
}

resource "azurerm_cosmosdb_sql_container" "call_session_container" {
  name                = "CallSessions"
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.call_session_account.name
  database_name       = azurerm_cosmosdb_sql_database.call_session_db.name

  partition_key_paths   = ["/callerId"]
  partition_key_version = 2
  conflict_resolution_policy {
    mode                     = "LastWriterWins"
    conflict_resolution_path = "/_ts"
  }

  indexing_policy {
    indexing_mode = "consistent"
    included_path {
      path = "/*"
    }
    # excluded_path {
    #   path = "/\"_etag\"/?"
    # }
  }
}

resource "azurerm_cosmosdb_sql_role_definition" "data_reader" {
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.call_session_account.name
  name                = "${local.name_prefix}-callsession-reader-role"
  type                = "BuiltInRole"
  assignable_scopes   = [azurerm_cosmosdb_account.call_session_account.id]

  permissions {
    data_actions = ["Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read",
      "Microsoft.DocumentDB/databaseAccounts/readMetadata",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/executeQuery",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/readChangeFeed",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/read"
    ]
  }
}

resource "azurerm_cosmosdb_sql_role_definition" "data_contributor" {
  resource_group_name = azurerm_resource_group.rg.name
  account_name        = azurerm_cosmosdb_account.call_session_account.name
  name                = "${local.name_prefix}-callsession-contributer-role"
  type                = "BuiltInRole"
  assignable_scopes   = [azurerm_cosmosdb_account.call_session_account.id]

  permissions {
    data_actions = [
      "Microsoft.DocumentDB/databaseAccounts/readMetadata",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/*",
      "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*"
    ]
  }
}
