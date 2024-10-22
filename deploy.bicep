param location string = 'eastus'
param cognitiveServicesName string
param acsResourceName string
param searchServiceName string

resource cognitiveServices 'Microsoft.CognitiveServices/accounts@2023-06-01' = {
  name: cognitiveServicesName
  location: location
  kind: 'CognitiveServices'
  sku: {
    name: 'S0'
  }
  properties: {
    apiProperties: {}
  }
}

resource acs 'Microsoft.Communication/communicationServices@2023-03-01-preview' = {
  name: acsResourceName
  location: location
  properties: {}
}

resource searchService 'Microsoft.Search/searchServices@2023-07-01-preview' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    hostingMode: 'default'
    replicaCount: 1
    partitionCount: 1
  }
}
