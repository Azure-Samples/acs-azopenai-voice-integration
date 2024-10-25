param redisName string = 'redis-${uniqueString(resourceGroup().id)}'
param envName string = 'dev'
param location string = resourceGroup().location


module redis 'br/public:avm/res/cache/redis:0.7.0' = {
  name: 'redisDeploymentTwo'
  params: {
    // Required parameters
    name: redisName
    // Non-required parameters
    location: location
    enableNonSslPort: false
    publicNetworkAccess: 'Enabled'
  }
}
