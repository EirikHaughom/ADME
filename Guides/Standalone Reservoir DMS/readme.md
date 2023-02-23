## Overview
The Reservoir Model DMS (RDDMS) is currently an experimental feature of OSDU and not part of Microsoft Energy Data Services.

This guide will explain how you can deploy a standalone version of the RDDMS on Azure Container Instance (ACI) with an Azure Database for PostgreSQL (PaaS), and secured with Azure AD authentication.

RDDMS consists of 3 main components:
1. OpenETPServer: Server component which interprets calls from the OpenETPClient.
2. Database (PostgreSQL): Database which stores the binary reservoir model files.
3. OpenETPClient: REST API and C++ client which interacts with OpenETPServer.

<br>

> ℹ️ A standalone RDDMS server will have no connection towards your OSDU or MEDS instance, and is solely mean to be used to test the RDDMS capabilities itself, such as data ingestion, consumption etc.

<br>

## Details
In the [official documentation](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/reservoir/open-etp-server/-/tree/main), the RDDMS server (openETPServer), as well as the PostgreSQL database and RDDMS REST API (openETPClient), are deployed in a Docker instance. I have recompiled the images to ACI-compliant container image to host the RDDMS server and REST API, along with a PaaS Azure Db for PostgreSQL:
- Less management overhead (eliminates IaaS VM to host Docker)
- Simplified deployment using a generalized container image
- Database on PaaS for better resiliency, performance and less management overhead

In addition there are security concerns as the username (foo) and password (bar) is hardcoded on the OpenETPServer. Companies are therefore reluctant to expose the RDDMS over internet or even internally outside an isolated environment, and thus may hamper user testing and experience. To combat this, we will:
- Use Azure API Management (APIM) as the API gateway, which means we can isolate the server to only reply to requests coming through the API gateway.
- Use APIM to authenticate requests using Azure AD by using JWT Token validation.
<br><br>

## Phases
The deployment is divided into two phases.

**Phase 1**
- Deploy the RDDMS Server container in a private Virtual Network (VNET) for internal consumption.

**Phase 2**
- Deploy the RDDMS REST API container in the same private VNET as the RDDMS Server.
- Deploy Azure API Management for public access to both the RDDMS Server and REST API.
- Integrate authentication with Azure AD using Azure API Management.
<br><br>

# Phase 1

## Prerequisites
[Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and logged into the target subscription.

## Preparation
1. Define variables
    ```ps
    ### RESOURCE GROUP ###
    $resourceGroup = "eirikrddms" # name of the resource group (will be created if it doesn't exist)
    $location = "westeurope" # location where to deploy all resources

    ### RDDMS SERVER AND REST API ###
    $jwtSecret = "osdu-rddms" # This is the default secret in RDDMS, please change to create a stronger signature for the JWT tokens.
    $rddmsServerName = "rddms-server" # Name of the ACI container hosting the RDDMS Server
    $rddmsServerPort = "9002" # This is the default port for the RDDMS Server, change if needed
    $rddmsApiName = "rddms-restapi" # Name of the ACI container hosting the RDDMS REST API 
    $rddmsApiPort = "8003" # This is the default port for the RDDMS REST API, change if needed
    $containerRegistryName = "" # [Unique] Name of the Azure Container Registry

    ### POSTGRESQL SERVER ###
    $dbServerName = "rddms-db" # [Unique] Name of the Azure Db for PostgreSQL server
    $dbServerUsername = "azureuser" # Username of the database admin
    $dbServerPassword = "" # Password of the database user
    
    ### AZURE API MANAGEMENT ###
    $apiName = "" # [Unique] Name of the Azure API Management instance 
    $apiPublisherEmail = "user@contoso.com" # Email to receive notifications about the APIM instance
    $apiPublisherName = "Jane Doe" # Name to receive notifications

    ```
2. Azure Virtual Network with three subnets (ACI, db and APIM)
    ```ps
    # Create Resource Group if it doesn't exist
    if ((az group exists --resource-group $resourceGroup) -eq "false") {
        az group create --resource-group $resourceGroup --location $location
    }

    # Create Virtual Network
    $vnet = az network vnet create --resource-group $resourceGroup `
    --name myName `
    --address-prefix 10.1.0.0/16
    $vnet = ($vnet | convertfrom-json).newvnet

    # Create subnet for the containers
    $containerSubnet = az network vnet subnet create --resource-group $resourceGroup `
    --name containerSubnet `
    --address-prefix 10.1.0.0/24 `
    --vnet-name $vnet.name `
    --delegations Microsoft.ContainerInstance/containerGroups
    $containerSubnet = $containerSubnet | convertfrom-json

    # Create subnet for the database
    $dbSubnet = az network vnet subnet create --resource-group $resourceGroup `
    --name dbSubnet `
    --address-prefix 10.1.1.0/24 `
    --vnet-name $vnet.name
    $dbSubnet = $dbSubnet | convertfrom-json

    # Create subnet for the Azure API Management
    $apiSubnet = az network vnet subnet create --resource-group $resourceGroup `
    --name apiSubnet `
    --address-prefix 10.1.2.0/24 `
    --vnet-name $vnet.name
    $apiSubnet = $apiSubnet | convertfrom-json
    ```
<br>

## Deploying the PostgreSQL Database
1. Create a new Azure Database for PostgreSQL server.
    ```ps
    $dbServer = az postgres server create --resource-group $resourceGroup `
    --name $dbServerName `
    --admin-user $dbServerUsername `
    --admin-password $dbServerPassword `
    --sku-name GP_Gen5_2 `
    --public-network-access disabled `
    --ssl-enforcement disabled `
    --version 11
    $dbServer = $dbServer | convertfrom-json
    ```
2. Create Private Link and Private DNS Zone for the PostgreSQL server.
    ```ps
    $nicName = $dbServer.name+"-nic"
    $connName = $dbServer.name+"-privateEndpoint"
    $privateLinkName = $vnet.name+"-postgres-dnslink"

    # Create Private Endpoint
    $privateEndpoint = az network private-endpoint create --resource-group $resourceGroup `
    --name $nicName `
    --vnet-name $vnet.name `
    --subnet $dbSubnet.name `
    --private-connection-resource-id $dbServer.id `
    --group-id postgresqlServer `
    --connection-name $connName
    $privateEndpoint = $privateEndpoint | convertfrom-json

    # Create Private DNS Zone
    az network private-dns zone create --resource-group $resourceGroup `
    --name  "privatelink.postgres.database.azure.com" 

    # Link Private DNS Zone to VNET
    az network private-dns link vnet create --resource-group eirikrddms `
    --zone-name  "privatelink.postgres.database.azure.com" `
    --name $privateLinkName `
    --virtual-network $vnet.name `
    --registration-enabled false

    # Create a-record in the Private DNS Zone
    az network private-dns record-set a create --resource-group $resourceGroup `
    --name $dbServer.name `
    --zone-name privatelink.postgres.database.azure.com 

    # Add Private IP address to the a-record
    az network private-dns record-set a add-record --resource-group $resourceGroup `
    --record-set-name $dbServer.name `
    --zone-name privatelink.postgres.database.azure.com `
    -a $privateEndpoint.customDnsConfigs.ipAddresses
    ```
3. Create a database on the PostgreSQL server.
    ```ps
    $db = az postgres db create --resource-group $resourceGroup `
    --name rddms `
    --server-name $dbServer.name
    $db = $db | convertfrom-json
    ```
<br><br>

## Deploying the RDDMS Server
1. Create an Azure Container Registry (ACR) to host the Container Image.
    ```ps
    $acr = az acr create --resource-group $resourceGroup `
    --name $containerRegistryName `
    --sku Basic `
    --admin-enabled true
    $acr = $acr | convertfrom-json

    # Gets admin credentials for the AC, to be used when creating container later on.
    $acrCreds = az acr credential show --name $acr.name
    $acrCreds = $acrCreds | convertfrom-json
    $acrUsername = $acrCreds.username
    $acrPassword = $acrCreds.passwords.value[0]    
    ```
2. Pull the image from public repository into your ACR.
    ```ps
    az acr import -n $acr.name `
    --source rddms.azurecr.io/open-etp-server-eihaugho-aci:latest
    ```
3. Create Azure Container Instance based on the image.
    ```ps
    $containerImage = $acr.loginServer+"/open-etp-server-eihaugho-aci:latest"
    $connString = "host="+$dbServer.fullyQualifiedDomainName+" port=5432 dbname="+$db.name+" user="+$dbServer.administratorlogin+"@"+$dbServer.name+" password="+$dbServer.password
    $cmd = "openETPServer server --start --port "+$rddmsServerPort+" --jwt-secret "+$jwtSecret

    $rddmsServer = az container create --resource-group $resourceGroup `
    --name $rddmsServerName `
    --dns-name-label $rddmsServerName `
    --image $containerImage `
    --registry-username $acrUsername `
    --registry-password $acrPassword `
    --ports $rddmsServerPort `
    --environment-variables `
    RDMS_DATA_PARTITION_MODE=single `
    POSTGRESQL_CONN_STRING=$connString `
    --command-line $cmd `
    --ip-address Public
    $rddmsServer = $rddmsServer | convertfrom-json

    $rddmsServerUrl = "ws://"+$rddmsServer.ipAddress.ip+":"+$rddmsServerPort

    Write-Host "The RDDMS Server is now accessible internally on $rddmsServerUrl" -ForegroundColor green 
    Write-Host "Proceed with Phase 2 to deploy the API Gateway and REST API for public access" -ForegroundColor green 
    ```
<br>

# Phase 2

## Deploying Azure API Management
1. Create a new Azure API Management (APIM) instance.
    ```ps
    $nicName = $apiName+"-nic"
    $connName = $apiName+"-privateEndpoint"
    $privateLinkName = $vnet.name+"-api-dnslink"

    az apim create --resource-group $resourceGroup `
    --name $apiName `
    --publisher-email $apiPublisherEmail `
    --publisher-name $apiPublisherName `
    --public-network-access true `
    --sku-name Developer `
    --virtual-network External
    ```

2. ⚠️ **Wait until the APIM instance is activated before you continue.** This may take ~1 hour to complete. You will receive an email (to the one specified in $apiPublisherEmail) once it is activated.
    ```ps
    # Get the details from the provisioned APIM instance
    $api = az apim show --name $apiName --resource-group $resourceGroup | convertfrom-json

    $apiId = $api.id
    $apiSubnetId = $apiSubnet.id

    # Add subnet configuration to the APIM resource
    az resource update --ids $apiId --set properties.virtualNetworkConfiguration.subnetResourceId=$apiSubnetId --set properties.virtualNetworkType=External
    ```
    <br>

## Deploying the RDDMS Client (REST API)
1. Pull the image from public repository into your ACR.
    ```ps
    az acr import -n $acr.name `
    --source rddms.azurecr.io/open-etp-restapi-eihaugho-aci:latest
    ```

2. Create Azure Container Instance based on the image.
    ```ps
    $containerImage = $acr.loginServer+"/open-etp-restapi-eihaugho-aci:latest"
    $rmdsRestMainUrl = $api.gatewayUrl
    $rdmsEtpHost = $rddmsServer.ipAddress.ip

    az container create --resource-group $resourceGroup `
    --name $rddmsApiName `
    --image $containerImage `
    --registry-username $acrUsername `
    --registry-password $acrPassword `
    --ports $rddmsApiPort `
    --environment-variables `
    RDMS_ETP_HOST=$rdmsEtpHost `
    RDMS_ETP_PROTOCOL=ws `
    RDMS_ETP_PORT=$rddmsServerPort `
    RDMS_REST_PORT=$rddmsApiPort `
    RDMS_JWT_SECRET=$jwtSecret `
    RDMS_AUTHENTICATION_KEY_BASE=0000000-0000-0000-0000-000000000000 `
    RDMS_REST_ROOT_PATH=/Reservoir/v2 `
    RDMS_REST_MAIN_URL=$rmdsRestMainUrl `
    RDMS_DATA_PARTITION_MODE=single `
    --ip-address Private `
    --vnet $vnet.name `
    --subnet $containerSubnet.id
    ```
    <br>

## Deploy RDDMS Server to APIM and add Azure AD authentication
1. Deploy the RDDMS Server Websocket API to APIM
    ```ps 
    $serviceUrl = "ws://"+$rddmsServer.ipAddress.ip+":"+$rddmsServerPort

    az apim api create --resource-group $resourceGroup `
    --api-id $rddmsServerName `
    --display-name $rddmsServerName `
    --path "/" `
    --service-name $api.name `
    --api-type websocket `
    --service-url $serviceUrl

    # Configure JWT token Azure AD validation


    ```


Auth option 1 (preferred): User tokens (requires tenant admin consent)

Auth option 2: App Registration (client ID and secret)