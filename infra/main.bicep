// main.bicep

targetScope = 'resourceGroup'

// Parameters
param location string = resourceGroup().location
param envName string = 'dev'
param acsName string = 'acs-${uniqueString(resourceGroup().id)}-${envName}'
param egWebhookEndpointUrl string = '<http placeholder>'

param aiLocation string = 'swedencentral'

@description('AOAI gpt 4o deployment config')
param aoaiGptDeployment object = {
  name: 'gpt-4o'
  model: {
    format: 'OpenAI'
    name: 'gpt-4o'
    version: '2024-08-06'
  }
  sku: {
    name: 'Standard'
    capacity: 10
  }
}

@description('AOAI ada embeddings deployment config')
param aoaiEmbeddingsDeployment object = {
  name: 'text-embedding-ada-002'
  model: {
    format: 'OpenAI'
    name: 'text-embedding-ada-002'
    version: '2'
  }
  sku: {
    name: 'Standard'
    capacity: 10
  }
}

var aiServDeployments = [
  aoaiGptDeployment
  aoaiEmbeddingsDeployment
  //speechAiDeployment
]

// Modules
module aoai 'modules/aoai.bicep' = {
  name: 'deployAoai'
  params: {
    aiServDeployments: aiServDeployments
    envName: envName
    aoaiLocation: aiLocation
  }
}

module aiSpeech 'modules/ai-services.bicep' = {
  name: 'deploySpeechService'
}

module maps 'modules/maps.bicep' = {
  name: 'deployMaps'
  params: {
    location: 'northeurope' // maps has limited locations so defaulting to northeurope
    envName: envName
  }
}

module acs 'modules/acs.bicep' = {
  name: 'deployAcs'
  params: {
    envName: envName
  }
}

module aiSearch 'modules/ai-search.bicep' = {
  name: 'deployAiSearch'
  params: {
    envName: envName
    //location: location
  }
}

module eg 'modules/event-grid.bicep' = {
  name: 'deployEventGrid'
  params: {
    acsName: acsName
    envName: envName
  }
  dependsOn: [
    acs
  ]
}

module redis 'modules/redis.bicep' = {
  name: 'redisDeployment'
  params: {
    envName: envName
    location: location
  }
}
