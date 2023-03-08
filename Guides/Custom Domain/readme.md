## Description
This guide is meant as an example on how to use Azure API Management (APIM) as a gateway with a custom DNS domain in front of Azure Data Manager for Energy (ADME) APIs. The solution allows you to brand your ADME instance with a domain name of your own choice, such as osdu.contoso.com instead of contoso.energy.azure.com.

## Prerequisites
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and logged into the target subscription.
- [Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/get-started-create-service-instance-cli) instance with access to the ADME instance (i.e. VNET integrated if ADME is configured with Private Endpoint).

## Deployment
1. Deploy the custom domain to APIM following the [official documentation](https://learn.microsoft.com/en-us/azure/api-management/configure-custom-domain?tabs=custom).
2. Deploy the APIs to the APIM instance. 
    ```powershell
    # Variables
    $admeHostname = ".energy.azure.com"
    $resourceGroup = "myResourceGroup"
    $apimName = "myApiManagement"

    # Defines the API definitions to load into APIM.
    # Note: These are OSDU M12 API definitions.

    $apis = @(
        "crsConverter",
        "crsCatalog",
        "dataset",
        "entitlements",
        "file",
        "indexer",
        "legal",
        "notification",
        "partition",
        "register",
        "schema",
        "search",
        "seismicDdms",
        "storage",
        "unit",
        "wellboreDdms",
        "wellDeliveryDdms",
        "workflow"
    )

    $apiDefinitions = @{
        crsConverter = @("api/crs/converter","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/crs_converter_openapi.yaml")
        crsCatalog = @("api/crs/catalog/v2","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/crs-catalog-openapi-v2.yaml")
        dataset = @("api/dataset/v1","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/dataset_swagger.yaml")
        entitlements = @("api/entitlements/v2","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/entitlements_openapi.yaml")
        file = @("api/file/v1","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/file_service_openapi.yaml")
        indexer = @("api/indexer/v2","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/indexer_openapi.yaml")
        legal = @("api/legal/v1","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/compliance_openapi.yaml")
        notification = @("api/notification/v1","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/notification_openapi.yaml")
        partition = @("api/partition/v1","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/partition_openapi.yaml")
        register = @("api/register/v1","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/register_openapi.yaml")
        schema = @("api/schema-service/v1","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/schema_openapi.yaml")
        search = @("api/search/v2","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/search_openapi.yaml")
        seismicDdms = @("/seistore-svc","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/seismic_ddms_openapi.yaml")
        storage = @("api/storage/v2","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/storage_openapi.yaml")
        unit = @("api/unit","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/unit_service_openapi_v3.yaml")
        wellboreDdms = @("/","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/wellbore_ddms_openapi.yaml")
        wellDeliveryDdms = @("api/well-delivery","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/welldelivery_ddms_openapi.yaml")
        workflow = @("api/workflow","https://raw.githubusercontent.com/EirikHaughom/ADME/custom-domain/Guides/Custom%20Domain/src/m12/workflow_openapi.yaml")
    }

    foreach ($api in $apis) {
        $serviceUrl = "https://"+$admeHostname+"/"+$apiDefinitions[$api][0]

        Write-Host "Importing $api"
        az apim api import --resource-group $resourceGroup `
            --path $apiDefinitions[$api][0] `
            --service-name $apimName `
            --specification-format OpenApi `
            --specification-url $apiDefinitions[$api][1] `
            --protocols https `
            --service-url $serviceUrl `
            --subscription-required false `
            --output none
    }
    ```