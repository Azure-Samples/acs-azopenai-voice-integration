param acsName string
param egWebhookEndpointUrl string
param location string = resourceGroup().location


resource acs 'Microsoft.Communication/communicationServices@2023-06-01-preview' existing = {
  name: acsName
}

module systemTopic 'br/public:avm/res/event-grid/system-topic:0.4.0' = {
  name: 'systemTopicDeployment'
  params: {
    // Required parameters
    name: 'egstmin001'
    source: acs.id
    topicType: 'Microsoft.Storage.StorageAccounts' //PLACEHOLDER
    // Non-required parameters
    location: location
    eventSubscriptions: [
      {
        destination: {
          endpointType: 'Webhook'
          properties: {
            endpointUrl: egWebhookEndpointUrl
          }
        }
      }
    ]
  }
}
