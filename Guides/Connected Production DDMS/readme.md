# Connected Production DMS Deployment Guide

This guide provides step-by-step instructions to deploy the Connected Production Domain Data Management Service (DDMS) into Azure. It covers prerequisites, parameter configuration, deployment methods, post-deployment validation, and troubleshooting.

---

## Table of Contents

1. [Overview](#overview)
1. [Prerequisites](#prerequisites)
1. [Deployment Resources](#deployment-resources)
1. [Parameter Configuration](#parameter-configuration)
1. [Deployment Methods](#deployment-methods)
   - [Azure Portal](#azure-portal)
   - [Azure CLI / PowerShell](#azure-cli--powershell)
1. [Post-Deployment Validation](#post-deployment-validation)
1. [Test Data Loading](#test-data-loading)
1. [Troubleshooting](#troubleshooting)
1. [Cleanup](#cleanup)
1. [References](#references)

---

## Overview

The Connected Production DDMS provides a cloud-hosted, scalable, and secure API service for managing production data in the OSDU data model. This solution deploys a set of App Services, Azure PostgreSQL, and supporting resources via an ARM template.

## Prerequisites

Before you begin, ensure you have:

- An active Azure subscription with Contributor or Owner role
- Azure CLI version >= 2.30 or Azure PowerShell Az module >= 6.0 installed
- Owner access to an Azure Resource Group or permission to create new groups
- An Azure Data Manager for Energy instance
- A service principal (client ID and secret) with access to read the ADME Partition API
- (Optional) Service Principal or Managed Identity for automated deployments

## Deployment Resources

The following files are used during deployment:

- `azuredeploy.json`: ARM template defining resources (App Service Plans, Web Apps, Azure PostgreSQL, VNet, etc.)
- `uidefinition.json`: Custom UI definition for Azure Portal parameters
- `parameters.production.json` (you may create this): Parameter file for production settings

### Parameter Reference

In the Azure Portal UI, these fields will be presented for input. When deploying programmatically, you can supply them via a parameters JSON file or CLI/PowerShell flags.

#### Parameters

These parameters have no default values and must be provided:

| Parameter Name               | Type          | Default value                    | Description                                                                                       |
|------------------------------|---------------|----------------------------------|---------------------------------------------------------------------------------------------------|
| name                         | string        |                                  | The base name of the services. Most services will be appended with a service name (e.g., -postgres). |
| containerImageService        | string        |                                  | The container image to use for the main service.                                                  |
| containerImageInit           | string        |                                  | The container image to use for the init container.                                                |
| modelDatabaseName            | string        |                                  | The database to use for the model.                                                                |
| serviceDatabaseName          | string        |                                  | The database to use for the service.                                                              |
| databaseUsername             | string        |                                  | The username to use for the database.                                                             |
| databasePassword             | securestring  |                                  | The password to use for the database.                                                             |
| osduEndpoint                 | string        |                                  | The ADME endpoint to connect to.                                                                  |
| dataPartitionId              | string        |                                  | The ADME data partition ID to use.                                                                |
| admeScope                    | string        |                                  | The ADME scope to use.                                                                            |
| admeLegalTag                 | string        |                                  | The ADME legal tag to use.                                                                        |
| clientID                     | string        |                                  | The client ID to use for the service.                                                             |
| clientSecret                 | securestring  |                                  | The client secret to use for the service.                                                         |
| vnet                         | object        | `{ "name": "vnet" }`             | Virtual network configuration object (name, addressPrefix)                                         |
| virtualNetworkResourceGroup  | string        | N/A                              | Resource group that contains the existing VNet                                                     |
| virtualNetworkNewOrExisting  | string        | N/A                              | Specify `'new'` to create a VNet or `'existing'` to use an existing one                            |
| databaseSubnet               | object        | `{ "name": "databaseSubnet" }`   | Subnet settings object for the database                                                            |
| containerSubnet              | object        | `{ "name": "containerSubnet" }`  | Subnet settings object for the container apps                                                      |
| workloadProfile              | string        | `Consumption`                    | Container App workload profile (e.g., `Consumption` or `D4` for Premium)                            |
| privateEndpointEnabled       | bool          | `false`                          | Enable private endpoint integration for resources                                                 |

## Deployment Methods

Select one of the deployment methods below.

- [Azure Portal](#azure-portal)
- [Azure CLI](#azure-cli)

### Azure Portal

Get started by using the `Deploy to Azure`button.

[![Deploy To Azure](https://docs.microsoft.com/en-us/azure/templates/media/deploy-to-azure.svg)](https://portal.azure.com/#blade/Microsoft_Azure_CreateUIDef/CustomDeploymentBlade/uri/https%3A%2F%2Fraw.githubusercontent.com%2FEirikHaughom%2FADME%2Frefs%2Fheads%2Fmain%2FGuides%2FConnected%2520Production%2520DDMS%2Fazuredeploy.json/uiFormDefinitionUri/https%3A%2F%2Fraw.githubusercontent.com%2FEirikHaughom%2FADME%2Frefs%2Fheads%2Fmain%2FGuides%2FConnected%2520Production%2520DDMS%2Fuidefinition.json)

1. Select or create a Resource Group
1. Fill in parameters in the UI
1. Review and click **Create**
1. Wait ~10–15 minutes for deployment to finish

### Azure CLI

## Parameter Configuration

Create a parameter file (`parameters.production.json`) with values for your environment. Example:

```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "resourcePrefix": { "value": "prod-ddms" },
    "sqlAdminLogin": { "value": "sqladmin" },
    "sqlAdminPassword": { "value": "<YourStrongP@ssword>" },
    "location": { "value": "eastus2" },
    "appServiceSku": { "value": "S1" },
    "vnetSubnetId": { "value": "/subscriptions/.../resourceGroups/rg-network/providers/Microsoft.Network/virtualNetworks/vnet/subnets/ddms" }
  }
}
```

CLI example:

```pwsh
az deployment group create \
  --resource-group <resource-group> \
  --template-file azuredeploy.json \
  --parameters \
    name=prod-ddms \
    containerImageService=<image-url> \
    containerImageInit=<image-url> \
    modelDatabaseName=<dbModel> \
    serviceDatabaseName=<dbService> \
    databaseUsername=<admin> \
    databasePassword=<password> \
    admeScope=<scope> \
    admeLegalTag=<legalTag> \
    clientID=<appId> \
    clientSecret=<secret>
```

PowerShell example:

```pwsh
New-AzResourceGroupDeployment \
  -ResourceGroupName <resource-group> \
  -TemplateFile azuredeploy.json \
  -TemplateParameterFile parameters.production.json
```

Or JSON parameter file:

```json
{
  "name": { "value": "prod-ddms" },
  "containerImageService": { "value": "<image>" },
  /* ... */
}
```

**Using Azure CLI**:

```pwsh
# Login
az login

# Create resource group (if needed)
az group create --name prod-ddms-rg --location eastus2

# Deploy template with parameter file
az deployment group create \
  --resource-group prod-ddms-rg \
  --template-file azuredeploy.json \
  --parameters @parameters.production.json
```

**Using Azure PowerShell**:

```pwsh
# Login
Connect-AzAccount

# Create resource group
define $rg = "prod-ddms-rg"; $loc = "eastus2"
New-AzResourceGroup -Name $rg -Location $loc

# Deploy
New-AzResourceGroupDeployment \
  -ResourceGroupName $rg \
  -TemplateFile "azuredeploy.json" \
  -TemplateParameterFile "parameters.production.json"
```

## Post-Deployment Validation

1. In the Azure Portal, navigate to the resource group and verify:
   - Azure PostgreSQL server and database are provisioned
   - App Service Plan and Web App are running
   - VNet integration configured (if used)
2. Retrieve the Web App URL
3. Test the API's health endpoint (replace `<app-url>`):

```pwsh
Invoke-WebRequest "https://<app-url>/health" -UseBasicParsing
```

Expect HTTP 200 with a JSON status payload.

## Troubleshooting

- **Deployment failures**: Check deployment operations in the Azure Portal under **Deployments** in the resource group.
- **Template validation errors**: Run `az deployment group validate` to pinpoint missing parameters or schema issues.
- **App Service errors**: Review **Log Stream** and **Application Insights** for exceptions.
- **Database connectivity**: Ensure firewall rules on the SQL server allow your client IP or App Service outbound IPs.

## Cleanup

To remove all resources when testing is complete:

```pwsh
az group delete --name prod-ddms-rg --yes --no-wait
```

## References

- [Azure ARM template documentation](https://docs.microsoft.com/azure/azure-resource-manager/templates/overview)
- [OSDU Production Core DDMS Repository](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/production/core/dspdm-services)
- [Azure CLI reference](https://docs.microsoft.com/cli/azure)
