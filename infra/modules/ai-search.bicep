param location string = 'northeurope'

//param kvName string

param envName string = 'dev'

param aiSeachName string = 'ai-search-${uniqueString(resourceGroup().id)}-${envName}'

@allowed([
  'free'
  'disabled'
  'standard'
])
@description('Configuration for semantic search, dependent on region and SKU')
param semanticSearchConfig string = 'free'

//resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing ={
//  name: kvName
//}

module searchService 'br/public:avm/res/search/search-service:0.7.0' = {
  name: 'searchServiceDeployment'
  params: {
    // Required parameters
    name: aiSeachName
    // Non-required parameters
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    disableLocalAuth: false
    location: location
    semanticSearch: semanticSearchConfig
    publicNetworkAccess: 'Enabled'
 //   secretsExportConfiguration: {
 //     keyVaultResourceId: kv.id
 //     primaryAdminKeyName: 'Primary-Admin-Key'
 //     secondaryAdminKeyName: 'Secondary-Admin-Key'
 //   }
  }
}
