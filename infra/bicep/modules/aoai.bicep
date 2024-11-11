@description('AOAI deployments array, defaults to one GPT-4o in Sweden Central')
param aiServDeployments array
param aoaiLocation string = 'swedencentral'

@description('Environment name, dev')
param envName string = 'dev'

// @description('Key Vaylt name')
// param kvName string

@description('AI Services account name')
param aiServAccName string = 'ai-acc-${uniqueString(resourceGroup().id)}-${envName}'

// key 1 value name
// var keyOneName = 'csakv001-accessKey1'

// connect to existing kv
//resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
//  name: kvName
//}

// deploy ai account with openai and kv keys mappings from AVM
module aiServAccModule 'br/public:avm/res/cognitive-services/account:0.8.0' = {
  name: aiServAccName
  params: {
    // Required parameters
    kind: 'OpenAI'
    name: aiServAccName
    // Non-required parameters
    deployments: aiServDeployments
    location: aoaiLocation
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
    //    secretsExportConfiguration: {
    //      accessKey1Name: 'csakv001-accessKey1'
    //      accessKey2Name: 'csakv001-accessKey2'
    //      keyVaultResourceId: kv.id
    //    }
  }
}

//output kv1 string = keyOneName
