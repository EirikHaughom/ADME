# Description
This guide will help you create a Logic App which synchronizes changes made to an Azure AD group into an Entitlements group in [Microsoft Energy Data Services](https://azure.microsoft.com/en-us/products/energy-data-services/#overview).

The solution supports the [Azure AD Dynamic group assignment](https://learn.microsoft.com/en-us/azure/active-directory/enterprise-users/groups-dynamic-membership) for a policy-driven permission assignment. 

While this guide is written for Microsoft Energy Data Services, it should work with any OSDU instance.

# Overview
![Logic App for Azure AD group sync to Microsoft Energy Data Services](img/logicapp-concept.png)

# Prerequisites
<details>
<summary>OSDU CLI</summary>

1. Generate a [Refresh Token](https://learn.microsoft.com/en-us/azure/energy-data-services/how-to-generate-refresh-token) for your Microsoft Energy Data Services instance.
2. Download [OSDU CLI](https://community.opengroup.org/osdu/platform/data-flow/data-loading/osdu-cli) from the Open Source Community.
3. Authenticate to your Microsoft Energy Data Services instance by running the following command.
```Powershell
osdu config update
```
4. Enter all the instance details, see example below.
    <details>
    <summary>Example input</summary>

    ```conf
    server = https://<instance-name>.energy.azure.com
    crs_catalog_url = /api/crs/catalog/v2/
    crs_converter_url = /api/crs/converter/v2/
    entitlements_url = /api/entitlements/v2/
    file_url = /api/file/v2/
    legal_url = /api/legal/v1/
    schema_url = /api/schema-service/v1/
    search_url = /api/search/v2/
    storage_url = /api/storage/v2/
    unit_url = /api/unit/v3/
    workflow_url = /api/workflow/v1/
    data_partition_id = <data-partition-id>
    legal_tag = <legal-tag-id>
    acl_viewer = data.default.viewers@<data-partition-id>.dataservices.energy
    acl_owner = data.default.owners@<data-partition-id>.dataservices.energy
    authentication_mode = refresh_token
    token_endpoint = https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token
    refresh_token = 0.ARoBv4j5cvDGr0GRqy18...
    client_id = <meds-appreg-client-id>
    client_secret =
    ```
5. Make sure that it is authenticated to your instance by running the following command.

    ```powershell
    osdu status
    ```

    This should return the following output:
    ```powershell
    PS C:\Users\admin> osdu status
    CRS Catalog service  200         OK
    CRS Converter service 200        OK
    File service         200         OK
    Entitlements Service 200         OK
    Legal service        200         OK
    Schema service       200         OK
    Search service       200         OK
    Storage service      200         OK
    Unit service         200         OK
    Workflow service     200         OK
    ```
</details>

<details>
<summary>Azure CLI</summary>

Download from [aka.ms/azurecli](https://aka.ms/azurecli).  
Login to the Azure CLI using the command below, and your user with subscription owner rights:
```Powershell
az login
```
Verify that the right subscription is selected:
```Powershell
az account show
```
If the correct subscription is not selected, run the following command:
```Powershell
az account set --subscription <subscription-id>
```
</details>

<details>
<summary>Azure CLI Logic App Extension</summary>

1. Install the module
    ```Powershell
    az extension add --name logic
    ```
</details>

<details>
<summary>Azure CLI Logic App Extension</summary>

1. Install the module
    ```Powershell
    az extension add --name logic
    ```
</details>


# Deploy

1. Create an Entitlements group using the OSDU CLI called meds-users.
```powershell
osdu entitlements groups add -g meds-users -d "User group synced from Azure AD by Logic App"
```
2. Create an M365 Azure AD group that will be the used as the source, we'll be using the Graph API for this step, but feel free to use Azure Portal or similar.

    Note the Object ID output.

    ```powershell
    # Define Graph API access token with Directory.ReadWrite.All and Group.ReadWrite.All
    $accessToken = "eyJ0eXAiOiJKV1QiL..."

    # Create request header
    $headers = @{
    "Authorization" = "Bearer $accessToken"
    }

    # Create request body with M365 group properties
    $groupBody = 
    '{
        "displayName": "meds-users",
        "mailEnabled": true,
        "mailNickname": "meds-users",
        "description": "User group synced to Microsoft Energy Data Services by Logic App",
        "securityEnabled": true,
        "groupTypes": [
            "Unified"
        ]
    }'

    # Invoke Graph service to create group
    $newGroup = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/groups" -ContentType "application/json" -Method POST -Headers $headers -Body $groupBody

    echo $newGroup.id
    ```
3. Run the following command to deploy the Logic App
    ```Powershell
    # Define the variables below
    $logicAppName = "meds-entitlements-sync1002"
    $bicepFile = "C:\temp\logicapp.bicep"
    $azureAdGroup = $newgroup.id # Unless you used the method above to create the Azure AD Group, replace with the ObjectID of said group
    $entitlementsGroup = "meds-users" # Target group name in MEDS Entitlements API
    $instanceName = "platform2368.energy.azure.com"
    $clientId = "354425f4-145b-4d95-b150-81d0fc1a9e5f"
    $dataPartitionId = "platform2368-opendes"

    # Downloads the logicapp.bicep file to the path specified in $bicepFile
    Invoke-WebRequest -Uri https://raw.githubusercontent.com/EirikHaughom/MicrosoftEnergyDataServices/main/Guides/AADEntitlementsSync/src/logicapp.bicep -OutFile $bicepFile

    # Run deployment
    az deployment group create `
        --resource-group $resourceGroup `
        --template-file $bicepFile `
        --parameters logicAppName=$logicAppName `
        --parameters dataPartitionId=$dataPartitionId `
        --parameters hostName=$instanceName `
        --parameters clientId=$clientId `
        --parameters azureAdGroup=$azureAdGroup `
        --parameters entitlementsGroup=$entitlementsGroup
    ```

# Test and verify



2. Create Logic App w/Managed Identity
3. Grant Managed Identity group reader access in AD
4. Grant Managed Identity AppID OWNER access to target Entitlements group
5. Configure Logic App