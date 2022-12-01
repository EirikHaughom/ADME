// Parameters
param location string = resourceGroup().location
param logicAppName string
param logicAppFile object

// Basic logic app
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
