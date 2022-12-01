// Parameters
param location string = resourceGroup().location
param logicAppName string
param logicAppFile object

// Office 365 Connection

resource o365connection 'Microsoft.Web/connections@2016-06-01' = {
  name: 'office365groups-1000'
  location: location
  properties: {
    api: {
      id: subscriptionResourceId('Microsoft.Web/locations/managedApis', location, 'office365groups')
      type: 'Microsoft.Web/locations/managedApis'
    }
    displayName: 'office365groups-1000'
  }
}

// Logic App
resource logicApp 'Microsoft.Logic/workflows@2019-05-01' = {
    name: logicAppName
    location: location
    identity: {
      type: 'SystemAssigned'
    }
    properties: {
      state: 'Enabled'
      definition: logicAppFile.definition
      parameters: logicAppFile.parameters
    }
}
