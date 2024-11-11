# # # Outputs


# # Outputs
# output "storage_account_name" {
#   value = azurerm_storage_account.storage.name
# }

# output "storage_account_primary_access_key" {
#   value     = azurerm_storage_account.storage.primary_access_key
#   sensitive = true
# }

# output "storage_account_primary_blob_endpoint" {
#   value = azurerm_storage_account.storage.primary_blob_endpoint
# }

# output "storage_container_name" {
#   value = azurerm_storage_container.container.name
# }

# output "sas_url_query_string" {
#   value = ""#data.azurerm_storage_account_sas.storage_sas_token.sas
#   sensitive = true
# }
# ##### OpenAI
# output "cognitive_account_identity" {
#   value = {
#     principal_id = azurerm_cognitive_account.openai.identity[0].principal_id
#     tenant_id    = azurerm_cognitive_account.openai.identity[0].tenant_id
#   }
# }
# output "openai_endpoint" {
#   value = azurerm_cognitive_account.openai.endpoint
# }
# output "openai_id" {
#   value = azurerm_cognitive_account.openai.id
# }
# output "openai_primary_key" {
#   value     = azurerm_cognitive_account.openai.primary_access_key
#   sensitive = true

# }
# output "openai_secondary_key" {
#   value     = azurerm_cognitive_account.openai.secondary_access_key
#   sensitive = true

# }
# output "openai_subdomain" {
#   value = azurerm_cognitive_account.openai.custom_subdomain_name
# }

# ## AI Translator
# # A primary access key which can be used to connect to the Cognitive Service Account.
# output "subscription_key" {
#   value     = azurerm_cognitive_account.translator.primary_access_key
#   sensitive = true
# }

# #The endpoint used to connect to the Cognitive Service Account
# output "document_translation_endpoint" {
#   value = azurerm_cognitive_account.translator.endpoint
# }

# output "document_translation_custom_subdomain_name" {
#   value = azurerm_cognitive_account.translator.custom_subdomain_name
# }


# #The ID of the Cognitive Service Account
# output "document_translation_id" {
#   value = azurerm_cognitive_account.translator.id
# }

# #identity - An identity block as defined below.
# output "document_translation_identity" {
#   value = azurerm_cognitive_account.translator.identity
# }

# output "translate_document_endpoint" {
#   value = "https://${azurerm_cognitive_account.translator.custom_subdomain_name}.cognitiveservices.azure.com"
# }

# # Output the site credentials (publishing credentials)
# output "upload_function_site_credential" {
#   value = {
#     username = azurerm_linux_function_app.upload_function.site_credential[0].name
#     password = azurerm_linux_function_app.upload_function.site_credential[0].password
#   }
#   sensitive = true
# }


# # Output the generated password (marked as sensitive)
# output "db_admin_password" {
#   value     = random_password.db_password.result
#   sensitive = true
# }

# # Output the connection string
# output "postgresql_connection_string" {
#   value     = "postgresql://${azurerm_postgresql_flexible_server.translator_db.administrator_login}:${random_password.db_password.result}@${azurerm_postgresql_flexible_server.translator_db.fqdn}:5432/${azurerm_postgresql_flexible_server_database.citus_db.name}?sslmode=require"
#   sensitive = true
# }

# # Output the server name
# output "postgresql_server_name" {
#   value = azurerm_postgresql_flexible_server.translator_db.name
# }

# # Output the server ID
# output "postgresql_server_id" {
#   value = azurerm_postgresql_flexible_server.translator_db.id
# }

# # Output the database name
# output "postgresql_database_name" {
#   value = azurerm_postgresql_flexible_server_database.citus_db.name
# }

# output "postgresql_fqdn" {
#   value = azurerm_postgresql_flexible_server.translator_db.fqdn
# }

# output "postgresql_server_admin" {
#   value = var.postgres_administrator_login
# }
