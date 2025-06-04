# Deploy Schema Upgrade Tool

This guide describes how to deploy the Schema Upgrade Tool as an Azure Container App using the provided ARM template and UI form definition. The Schema Upgrade Tool automates version upgrades of OSDU schemas in your ADME (Azure Data Management Environment) instance.

## Overview

The solution consists of:

- `azuredeploy.json` – ARM template to provision a Container App (and optionally a virtual network and private endpoints).
- `uidefinition.json` – UI form definition for Azure Portal Custom Deployment experience.

Upon deployment, you will have a running container instance hosting REST endpoints for schema upgrade operations, along with a Swagger UI to explore the API.

## Prerequisites

- An Azure subscription with Contributor or Resource Group Contributor rights.
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli) installed and logged in.
- (Optional) An existing virtual network and subnet if you enable private endpoint connectivity.

## Deployment

### Quickstart

Automated deployment through Azure Portal experience.

[![Deploy To Azure](https://docs.microsoft.com/en-us/azure/templates/media/deploy-to-azure.svg)](https://portal.azure.com/#blade/Microsoft_Azure_CreateUIDef/CustomDeploymentBlade/uri/https%3A%2F%2Fraw.githubusercontent.com%2FEirikHaughom%2FADME%2Frefs%2Fheads%2Fmain%2FGuides%2FSchema%2520Upgrade%2520Tool%2Fazuredeploy.json/uiFormDefinitionUri/https%3A%2F%2Fraw.githubusercontent.com%2FEirikHaughom%2FADME%2Frefs%2Fheads%2Fmain%2FGuides%2FSchema%2520Upgrade%2520Tool%2Fuidefinition.json)

### Azure Portal

1. Navigate to your target resource group in the Azure Portal.
2. Click **Deploy** > **Custom deployment**.
3. **Build your own template in the editor** and upload `azuredeploy.json`.
4. (Optional) Click **Load file** under **Artifact source** to upload `uidefinition.json` for a guided UI.
5. Fill in the parameters:
   - **Container App name**: Unique name (3–24 chars).
   - **Container image**: (Default: latest Schema Upgrade Tool image).
   - **ADME endpoint**: Base URL of your ADME instance (e.g. `https://my-adme.energy.azure.com/`).
   - **Workload profile**: `Consumption` or `Premium`.
   - **Use private network?**: Toggle to enable VNet, then configure or select a VNet and subnet.
   - **Tags**: (Optional) Resource tags.
6. Click **Review + Create** and then **Create**.
7. Monitor the deployment progress in **Notifications**.

### Azure CLI

```bash
# Variables
RG="<resource-group>"
TEMPLATE="./Guides/Schema Upgrade Tool/azuredeploy.json"
PARAMS=( 
  name="schema-upgrade"
  containerImage="community.opengroup.org:5555/osdu/platform/system/reference/schema-upgrade/schema-upgrade-v0-27-1:latest"
  osduEndpoint="https://<your-adme-instance>.energy.azure.com/"
  workloadProfile="Consumption"
  privateEndpointEnabled=false
)

# Deploy
az deployment group create \
  --resource-group $RG \
  --template-file $TEMPLATE \
  --parameters "${PARAMS[@]}"
```  

If you enable `privateEndpointEnabled=true`, add parameters for `vnet.name`, `virtualNetworkNewOrExisting`, and `containerSubnet.addressPrefix`.

## Parameters

| Name                       | Description                                                                                 | Default                                                                         |
| -------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `name`                     | The Container App name (3–24 characters).                                                   | N/A                                                                             |
| `containerImage`           | Docker image for the Schema Upgrade Tool.                                                    | `community.opengroup.org:5555/.../schema-upgrade-v0-27-1:latest`                |
| `osduEndpoint`             | Base URL of your ADME instance (must end with `/`).                                          | `https://<your-adme-instance>.energy.azure.com/`                                |
| `workloadProfile`          | `Consumption` or `Premium` workload profile.                                                 | `Consumption`                                                                   |
| `privateEndpointEnabled`   | Deploy with private endpoint and VNet integration.                                           | `false`                                                                         |
| `vnet`                     | VNet object: `name` and `addressPrefix`. Visible when private networking is enabled.        | `{ name: "vnet" }`                                                             |
| `virtualNetworkNewOrExisting` | `new` to create VNet, `existing` to use an existing one.                                   | `new`                                                                           |
| `containerSubnet`          | Subnet object: `name` and `addressPrefix`.                                                   | `{ name: "containerSubnet", addressPrefix: "10.0.1.0/24" }`                  |
| `tags`                     | Tags to apply to all resources.                                                              | `{}`                                                                             |

## Outputs

- **Swagger Endpoint**: URL to access the Swagger UI (e.g. `https://<fqdn>/api/schemaupgrade/v2/swagger-ui/index.html`).
- **Is it publicly accessible?**: Indicates if the tool is internet-accessible or requires private network access.

## Troubleshooting

- Ensure the `osduEndpoint` ends with a `/`.
- Check Azure Container Apps logs:

```bash
az containerapp logs show --name <containerAppName> --resource-group <rg>
```

- Validate networking configuration if you enable private endpoints.
- For container image issues, confirm the image tag exists in the [OSDU Schema Upgrade Tool registry](https://community.opengroup.org/osdu/platform/system/reference/schema-upgrade/container_registry/).

## Next Steps

- Use the Schema Upgrade Tool REST API to manage and run schema upgrades, [learn more](https://osdu.pages.opengroup.org/platform/system/reference/schema-upgrade/).
