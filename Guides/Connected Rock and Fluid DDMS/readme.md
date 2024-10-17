# Deploying a Connected Rock and Fluid Sample DDMS on Azure Data Manager for Energy (ADME)

This guide will walk you through deploying a Rock and Fluid Sample (RAFS) DDMS connected to an Azure Data Manager for Energy (ADME) instance using Azure Container Apps (Quick-deploy) or Azure Kubernetes Service (AKS).

> **DISCLAIMER**: The RAFS DDMS is provided as a sample only. meant for functional testing. The RAFS DDMS is an integration of the OSDU Forum RAFS DDMS release with ADME. This RAFS DDMS is not intended for production use or performance testing, and has not undergone additional security testing apart from what's done in the OSDU Forum as part of their releases. The RAFS DDMS is provided as-is and is not supported by Microsoft. For more information, see the [OSDU Forum](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services).

## Prerequisites

- An Azure subscription. If you don't have an Azure subscription, create a [free account](https://azure.microsoft.com/free/) before you begin.
- An Azure Data Manager for Energy (ADME) instance. If you don't have an ADME instance, [follow the ADME deployment guide](https://learn.microsoft.com/azure/energy-data-services/quickstart-create-microsoft-energy-data-services-instance).

## Deployment options

There are two deployment options available for the RAFS DDMS service:

1. [**Quick-deploy with Azure Container Apps**](#option-1-quick-deploy-with-azure-container-apps): Deploy the RAFS service using Azure Container Apps. This is the quickest way to deploy the RAFS service. This option provides a public endpoint by default, secured with SSL (HTTPS) out of the box. You may choose to deploy the service privately as well.

1. [**Azure Kubernetes Service (AKS) deployment**](#option-2-azure-kubernetes-service-aks-deployment): Deploy the RAFS service using Azure Kubernetes Service (AKS). This option provides more control over the deployment.

### Option 1: Quick-deploy with Azure Container Apps

1. Click the button below to deploy the RAFS service using Azure Container Apps:

    [![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FEirikHaughom%2FADME%2Frefs%2Fheads%2Fmain%2FGuides%2FConnected%2520Rock%2520and%2520Fluid%2520DDMS%2Fazuredeploy.json)

1. Fill in the required parameters and click `Review + create`.
1. After the deployment is complete, click the `Outputs` tab to find the swagger endpoint of the RAFS service.
1. **Optional**: Deploy [monitoring](#monitoring).

See [next steps](#next-steps) for more information on how to use the RAFS service.

#### Parameters for the Azure Container Apps deployment

| Parameter | Description | Required |
| --- | --- | --- |
| `Region` | The Azure region to deploy the services. Will match the region of the selected resource group. | Yes |
| `Name` | The base name of the services. Most services will be appended with a service name (i.e. -redis). | Yes |
| `Container Image` | The container image to use for the RAFS service. Check the [OSDU Forum RAFS Container Registry](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services/container_registry) for newer images. | Yes |
| `Workload Profile` | The workload profile to use for the container app. Consumption uses the `Consumption` profile, while Premium uses the `D4` profile. [Learn more](https://learn.microsoft.com/en-us/azure/container-apps/workload-profiles-overview#profile-types). | Yes |
| `Osdu Endpoint` | The endpoint of the ADME instance. I.e. `https://contoso.energy.azure.com/`. | Yes |
| `Data Partition Id` | The data partition of the ADME instance. I.e. `opendes` | Yes |
| `Logging Level` | The logging level of the RAFS service. Choose between `Debug` and `Info`. | Yes |
| `Enable Redis Cache` | Choose whether or not to deploy and use Azure Cache for Redis. | Yes |
| `Enable Private Network` | Setting this to `true` will deploy the service in a private network, using private endpoints. | Yes |

> **Note**: If you choose to deploy the service in a private network using `Enable Private Network`, you will need to either connect to the service using internal VNET routing, or deploy an ingress controller to access the service. See [Publish the RAFS DDMS service publicly](#publish-the-rafs-ddms-service-publicly) for more information regarding ingress controller options.

### Option 2: Azure Kubernetes Service (AKS) deployment

There are some additional prerequisites for the AKS deployment option:

- An Azure Kubernetes Service (AKS) cluster. If you don't have an AKS cluster, [follow the AKS deployment guide](https://learn.microsoft.com/azure/aks/learn/quick-kubernetes-deploy-portal?tabs=azure-cli).
- **\*OPTIONAL\*** An Azure Redis Cache instance. If you don't have an Azure Redis Cache instance, [follow the Azure Redis Cache deployment guide](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/quickstart-create-redis).

> The redis cache is optional. It is used for caching the data from the ADME instance to improve performance.

#### Deploy RAFS DDMS on AKS

1. Launch the Azure Cloud Shell by clicking the Cloud Shell icon in the Azure portal, or navigate to [shell.azure.com](https://shell.azure.com/).

1. Select `PowerShell` as the environment.

1. Clone the GitHub repository that contains the RAFS DDMS service deployment files:

    ```bash
    git clone https://github.com/EirikHaughom/ADME.git
    cd "ADME/Guides/Connected Rock and Fluid DDMS/"
    ```

1. Define variables

    ```bash
    $AKS_RESOURCE_GROUP="<resource-group-name>" # AKS resource group name
    $AKS_CLUSTER_NAME="<aks-cluster-name>" # AKS cluster name
    $ADME_ENDPOINT="<adme-endpoint>" # ADME instance endpoint (i.e. https://contoso.energy.azure.com/)
    $ADME_DATA_PARTITION="<adme-data-partition>" # ADME data partition (i.e. opendes)
    $REDIS_CACHE_ENABLED="false" # OPTIONAL - Enable Redis cache (true/false)
    $PRIVATE_ACCESS="true" # OPTIONAL - Enables or disables public access to the RAFS service (true/false). True for private access only, false for public access.
    $LOGGING_LEVEL="10" # 10 for DEBUG, 20 for INFO
    ```

1. **\*OPTIONAL\*** If you want to use a Redis cache.
    1. Define the related variables. 

    ```bash
    $REDIS_CACHE_NAME="<redis-cache-name>" # Redis cache name
    $REDIS_CACHE_RESOURCE_GROUP="<redis-cache-resource-group>" # Redis cache resource group
    ```

    1. Connect the AKS cluster to the Redis cache using Service Connector.

    ```azurecli
    $redis = (az redis show --resource-group $REDIS_CACHE_RESOURCE_GROUP --name $REDIS_CACHE_NAME | ConvertFrom-Json).id + "/databases/0"
    $aks = (az aks show --resource-group $AKS_RESOURCE_GROUP --name $AKS_CLUSTER_NAME | ConvertFrom-Json).id

    az aks connection create redis --source-id $aks --target-id $redis --connection rediscache --kube-namespace rafs --secret --customized-keys AZURE_REDIS_HOST=REDIS_HOSTNAME AZURE_REDIS_PASSWORD=REDIS_PASSWORD AZURE_REDIS_PORT=REDIS_PORT AZURE_REDIS_DATABASE=REDIS_DATABASE AZURE_REDIS_SSL=REDIS_SSL --client-type none
    ```

1. Connect to the AKS cluster

    ```bash
    az aks get-credentials --resource-group $AKS_RESOURCE_GROUP --name $AKS_CLUSTER_NAME --admin
    ```

1. Create a values.yaml file

    ```powershell
    Set-Content -Path "Values.yaml" -Value @"
    # This file contains the essential configs for the rafs on azure helm chart
    ################################################################################

    # Specify the values for each service.
    # Check the OSDU Forum RAFS container registry for newer versions.
    # https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services/container_registry/

    global:
        rafsservice:
            namespace: rafs
            name: rafsservice
            replicaCount: 1
            image:
                repository: community.opengroup.org:5555
                name: osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services/rafs-ddms-services-v0-27-1
                tag: 1630990d6bd460e8a8ed25be69778512346e9f10
            service:
                type: LoadBalancer
                annotations:
                    service.beta.kubernetes.io/azure-load-balancer-internal: $PRIVATE_ACCESS
            configuration:
                    ADME_ENDPOINT: $ADME_ENDPOINT
                    ADME_DATA_PARTITION: $ADME_DATA_PARTITION
                    OPENAPI_PREFIX: /api/rafs-ddms
                    URL_PREFIX: api/rafs-ddms
                    REDIS_CACHE_ENABLED: $REDIS_CACHE_ENABLED
                    LOGGING_LEVEL: '"$LOGGING_LEVEL"'
    "@ -Force
    ```

1. Deploy the RAFS DDMS service using the following commands:

    ```bash
    # Build HELM charts
    helm dependency build
    
    # Create AKS namespace
    kubectl create namespace rafs

    # Deploy HELM charts
    helm upgrade -i adme-connected-rafs . -n rafs -f Values.yaml
    ```

1. Verify the deployment by running the following command:

    ```bash
    kubectl get pods -n rafs
    ```

    The output should show the pods for the RAFS DDMS service.

1. To find the IP address of the RAFS DDMS service, run the following command:

    ```bash
    kubectl get service -n rddms
    ```

    The output should show the IP address of the RAFS DDMS service.

### Publish the RAFS DDMS service publicly

To publish the RAFS DDMS service, you will need to use an ingress controller, such as [Azure API Management](https://learn.microsoft.com/en-us/azure/api-management/import-and-publish), [Azure Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ingress-controller-expose-service-over-http-https), [Azure Front Door](https://learn.microsoft.com/en-us/azure/architecture/example-scenario/aks-front-door/aks-front-door), [NGINX Ingress Controller](https://learn.microsoft.com/en-us/azure/aks/app-routing) or [Istio](https://learn.microsoft.com/en-us/azure/aks/istio-deploy-ingress).

You may use the OpenAPI specification from the OSDU Forum if you wish to use Azure API Management. The OpenAPI specification can be found [here](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services/-/blob/main/docs/spec/openapi.json).

### Access the swagger UI

To access the swagger UI, navigate to `https://<public-dns>/api/rafs-ddms/swagger/index.html`.
Replace `<public-dns>` with the public DNS of the service you chose to use.

If you chose to expose the service through the `$PRIVATE_ACCESS=false` variable, you can access the service through the LoadBalancer IP address.

## Monitoring

You can monitor the RAFS service using Azure Monitor. To enable monitoring, follow the [Logging options for Azure Container Apps](https://learn.microsoft.com/en-us/azure/container-apps/log-options) or [Azure Monitor for Kubernetes](https://docs.microsoft.com/en-us/azure/azure-monitor/insights/container-insights-overview) documentation.

## Next steps

- [Run the Rock and Fluid Samples DDMS service integration tests](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services#local-running).
- [Publish the Rock and Fluid Samples schemas, reference- and master data](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services/-/tree/main/deployments).
- [Follow the tutorial on how to use the Rock and Fluid DDMS service](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/rock-and-fluid-sample/rafs-ddms-services/-/tree/main/docs/tutorial).
