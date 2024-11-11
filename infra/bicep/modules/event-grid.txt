param acsName string
//param egWebhookEndpointUrl string
//param location string = resourceGroup().location
param envName string = 'dev'

var egName = 'eg-systopic-${uniqueString(resourceGroup().id)}-${envName}'


resource acs 'Microsoft.Communication/communicationServices@2023-06-01-preview' existing = {
  name: acsName
}

module systemTopic 'br/public:avm/res/event-grid/system-topic:0.4.0' = {
  name: 'systemTopicDeployment'
  params: {
    // Required parameters
    name: egName
    source: acs.id
    topicType: 'Microsoft.Communication.CommunicationServices' 
    // Non-required parameters
    location: 'global'  // needs to be the same region as ACS
//    eventSubscriptions: [
//      { // is this a webhoook in the end???????
//        destination: {
//          endpointType: 'Webhook'
//          properties: {
//            endpointUrl: egWebhookEndpointUrl
//          }
//        }
//      }
//    ]
  }
}
