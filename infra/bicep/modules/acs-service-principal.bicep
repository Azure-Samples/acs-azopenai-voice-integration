@description('The name of the Azure AD application')
param applicationName string

@description('The name of the ACS resource')
param acsName string

var contributorRoleId = '87a39d53-fc1b-424a-814c-f7e04687dc9e' // Azure Communication Services role ID

// Use an API version with available type definitions
resource acsApplication 'Microsoft.Resources/deploymentScripts@2020-10-01' = {
  name: '${applicationName}-script'
  location: resourceGroup().location
  kind: 'AzurePowerShell'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      uami.id: {}
    }
  }
properties: {
azPowerShellVersion: '7.0'
timeout: 'PT30M'
arguments: '-applicationName "${applicationName}"'
scriptContent: '''
        param([string] $applicationName)

        # Authentication is handled by the managed identity
        $app = New-AzADApplication -DisplayName $applicationName
        $sp = New-AzADServicePrincipal -ApplicationId $app.ApplicationId

        $output = @{
          clientId = $app.ApplicationId   
          objectId = $sp.Id
          appId = $app.ApplicationId
        }

        $DeploymentScriptOutputs = $output | ConvertTo-Json
      '''
retentionInterval: 'P1D'
}
}

resource uami 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${applicationName}-identity'
  location: resourceGroup().location
}

// Assign the Application Administrator role to the managed identity (must be done manually in Azure AD)

// Reference the existing ACS resource
resource communicationService 'Microsoft.Communication/communicationServices@2023-06-01-preview' existing = {
  name: acsName
}

// Assign Contributor role to the service principal
resource roleAssignment 'Microsoft.Authorization/roleAssignments@2020-10-01-preview' = {
  name: guid(communicationService.id, acsApplication.name, contributorRoleId)
  scope: communicationService
  properties: {
    principalId: acsApplication.properties.outputs.objectId
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', contributorRoleId)
    principalType: 'ServicePrincipal'
  }
}

// Output the service principal details
output servicePrincipalId string = acsApplication.properties.outputs.objectId
output applicationId string = acsApplication.properties.outputs.appId
output clientId string = acsApplication.properties.outputs.clientId
