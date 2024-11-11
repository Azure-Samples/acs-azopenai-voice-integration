param envName string = 'dev'

@description('The name for your Azure Maps account. This value must be globally unique.')
param accountName string = 'maps-${uniqueString(resourceGroup().id)}-${envName}'

@allowed([
  'northeurope'
  'global'
  'westeurope'
])
@description('Specifies the location for all the resources.')
param location string = 'northeurope'

@description('The pricing tier SKU for the account.')
@allowed([
  'G2'
])
param pricingTier string = 'G2'

@description('The pricing tier for the account.')
@allowed([
  'Gen2'
])
param kind string = 'Gen2'

resource account 'Microsoft.Maps/accounts@2023-06-01' = {
  name: accountName
  location: location
  sku: {
    name: pricingTier
  }
  kind: kind
}
