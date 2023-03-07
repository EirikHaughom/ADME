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

    # Defines the API definitions to load into APIM.
    # Note: These are OSDU M12 API definitions.

    $apiDefinitions = @{
        crsConverter = @("/api/crs/converter","")
        crsCatalog = @("/api/crs/catalog/v2","")
        dataset = @("/api/dataset/v1","")
        entitlements = @("/api/entitlements/v2","")
        file = @("/api/file/v1","")
        indexer = @("/api/indexer/v2","")
        legal = @("/api/legal/v1","")
        notification = @("/api/notification/v1","")
        partition = @("/api/partition/v1","")
        register = @("/api/register/v1","")
        schema = @("/api/schema-service/v1","")
        search = @("/api/search/v2","")
        seismicDdms = @("/seistore-svc","")
        storage = @("/api/storage/v2","")
        unit = @("/api/unit","")
        wellboreDdms = @("","")
        wellDeliveryDdms = @("/api/well-delivery","")
        workflow = @("/api/workflow","")
    }
    ```