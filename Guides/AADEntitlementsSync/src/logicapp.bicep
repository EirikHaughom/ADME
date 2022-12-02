// Parameters
param logicAppName string
param clientId string
param dataPartitionId string
param hostName string
param azureAdGroup string
param entitlementsGroup string
param o365ConnectionName string = '${logicAppName}-o365conn'
param location string = resourceGroup().location


// Office 365 Connection

resource o365connection 'Microsoft.Web/connections@2016-06-01' = {
  name: o365ConnectionName
  location: location
  kind: 'V1'
  properties: {
    displayName: o365ConnectionName
    api: { 
      id: subscriptionResourceId('Microsoft.Web/locations/managedApis', location, 'office365groups')
    }
    parameterValueType: 'Alternative'
    alternativeParameterValues: {}
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
      definition: {
        '$schema': 'https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json#'
        contentVersion: '1.0.0.0'
        parameters: {
          '$connections': {
            defaultValue: {}
            type: 'Object'
          }
          client_id: {
            defaultValue: clientId
            type: 'String'
          }
          datapartition_id: {
            defaultValue: dataPartitionId
            type: 'String'
          }
          hostname: {
            defaultValue: hostName
            type: 'String'
          }
          synced_entitlements_group: {
            defaultValue: entitlementsGroup
            type: 'String'
          }
          synced_azuread_group: {
            defaultValue: azureAdGroup
            type: 'String'
          }
        }
        triggers: {
          When_a_group_member_is_added_or_removed: {
            recurrence: {
              frequency: 'Minute'
              interval: 1
            }
            evaluatedRecurrence: {
              frequency: 'Minute'
              interval: 1
            }
            splitOn: '@triggerBody()'
            type: 'ApiConnection'
            inputs: {
              host: {
                connection: {
                  name: '@parameters(\'$connections\')[\'office365groups\'][\'connectionId\']'
                }
              }
              method: 'get'
              path: '/trigger/v1.0/groups/delta'
              queries: {
                '$select': 'members'
                groupId: '@parameters(\'synced_azuread_group\')'
              }
            }
          }
        }
        actions: {
          Condition: {
            actions: {
              HTTP: {
                runAfter: {
                  Set_Added_Users: [
                    'Succeeded'
                  ]
                }
                type: 'Http'
                inputs: {
                  authentication: {
                    audience: '@parameters(\'client_id\')'
                    type: 'ManagedServiceIdentity'
                  }
                  body: {
                    email: '@{variables(\'Added users\')}'
                    role: 'MEMBER'
                  }
                  headers: {
                    'Content-Type': 'application/json'
                    accept: 'application/json'
                    'data-partition-id': '@parameters(\'datapartition_id\')'
                  }
                  method: 'POST'
                  uri: 'https://@{parameters(\'hostname\')}/api/entitlements/v2/groups/@{parameters(\'synced_entitlements_group\')}%40@{parameters(\'datapartition_id\')}.dataservices.energy/members'
                }
              }
              Set_Added_Users: {
                runAfter: {
                }
                type: 'SetVariable'
                inputs: {
                  name: 'Added users'
                  value: '@triggerBody()?[\'id\']'
                }
              }
            }
            runAfter: {
              'Initialize_variable_-_Removed_users': [
                'Succeeded'
              ]
            }
            else: {
              actions: {
                HTTP_2: {
                  runAfter: {
                    Set_Removed_Users: [
                      'Succeeded'
                    ]
                  }
                  type: 'Http'
                  inputs: {
                    authentication: {
                      audience: '@parameters(\'client_id\')'
                      type: 'ManagedServiceIdentity'
                    }
                    headers: {
                      accept: 'application/json'
                      'data-partition-id': '@parameters(\'datapartition_id\')'
                    }
                    method: 'DELETE'
                    uri: 'https://@{parameters(\'hostname\')}/api/entitlements/v2/groups/@{parameters(\'synced_entitlements_group\')}%40@{parameters(\'datapartition_id\')}.dataservices.energy/members/@{variables(\'Removed users\')}'
                  }
                }
                Set_Removed_Users: {
                  runAfter: {
                  }
                  type: 'SetVariable'
                  inputs: {
                    name: 'Removed users'
                    value: '@triggerBody()?[\'id\']'
                  }
                }
              }
            }
            expression: {
              and: [
                {
                  equals: [
                    '@empty(triggerBody()?[\'@removed\']?[\'reason\'])'
                    '@true'
                  ]
                }
              ]
            }
            type: 'If'
          }
          'Initialize_variable_-_Added_users': {
            runAfter: {
            }
            type: 'InitializeVariable'
            inputs: {
              variables: [
                {
                  name: 'Added users'
                  type: 'string'
                }
              ]
            }
          }
          'Initialize_variable_-_Removed_users': {
            runAfter: {
              'Initialize_variable_-_Added_users': [
                'Succeeded'
              ]
            }
            type: 'InitializeVariable'
            inputs: {
              variables: [
                {
                  name: 'Removed users'
                  type: 'string'
                }
              ]
            }
          }
        }
        outputs: {
        }
      }
      parameters: {
        '$connections': {
          value: {
            office365groups: {
              connectionId: o365connection.id
              connectionName: 'office365groups'
              connectionProperties: {
                authentication: {
                  type: 'ManagedServiceIdentity'
                }
              }
              id: subscriptionResourceId('Microsoft.Web/locations/managedApis', location, 'office365groups')
            }
          }
        }
      }
    }
}
