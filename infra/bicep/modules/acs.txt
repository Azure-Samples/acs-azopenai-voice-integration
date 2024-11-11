param acsName string = 'acs-${uniqueString(resourceGroup().id)}-${envName}'
param envName string = 'dev'


module communicationService 'br/public:avm/res/communication/communication-service:0.2.0' = {
  name: 'communicationServiceDeployment'
  params: {
    // Required parameters
    dataLocation: 'UK'
    name: acsName
    // Non-required parameters
    location: 'global'
  }
}
