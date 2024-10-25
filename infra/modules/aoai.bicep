@description('AOAI deployments array, defaults to one GPT-4o in Sweden Central')
param aoaiDeployments array = [
  {
    location: 'swedencentral'
    format: 'OpenAI'
    name: 'gpt-4o'
    version: '2024-08-06'
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
  {
    location: 'swedencentral'
    format: 'OpenAI'
    name: 'text-embedding-ada-002'
    version: '2'
    sku: {
      name: 'Standard'
      capacity: 10
    }
  }
]

@description('Environment name, dev')
param envName string = 'dev'

@description('Key Vaylt name')
param kvName string

@description('AI Services account name')
param aiServAccName string = 'ai-acc-${uniqueString(resourceGroup().id)}-${envName}'


// key 1 value name
var keyOneName = 'csakv001-accessKey1'




// connect to existing kv
resource kv 'Microsoft.KeyVault/vaults@2024-04-01-preview' existing = {
  name: kvName
}

// deploy ai account with openai and kv keys mappings from AVM
module aiAccoutAoai 'br/public:avm/res/cognitive-services/account:0.8.0' = [for model in aoaiDeployments: {
  name: 'aiServAccAoai${model.name}'
  params: {
    // Required parameters
    kind: 'AIServices'
    name: aiServAccName
    // Non-required parameters
    deployments: [
      {
        model: {
          format: model.format
          name: model.name
          version: model.version
        }
        name: model.format
        sku: {
          capacity: model.sku.capacity
          name: model.sku.name
        }
      }
    ]
    location: model.location
    secretsExportConfiguration: {
      accessKey1Name: 'csakv001-accessKey1'
      accessKey2Name: 'csakv001-accessKey2'
      keyVaultResourceId: kv.id
    }
  }
}]




output kv1 string = keyOneName
