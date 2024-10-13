# Deploying a Connected Rock and Fluid DDMS on Azure Data Manager for Energy (ADME)

This guide will walk you through deploying a Rock and Fluid DDMS (RAFS) service connected to an Azure Data Manager for Energy (ADME) instance using Azure Kubernetes Service (AKS).

## Prerequisites

- An Azure subscription. If you don't have an Azure subscription, create a [free account](https://azure.microsoft.com/free/) before you begin.
- An Azure Data Manager for Energy (ADME) instance. If you don't have an ADME instance, [follow the ADME deployment guide](https://learn.microsoft.com/azure/energy-data-services/quickstart-create-microsoft-energy-data-services-instance).
- An Azure Kubernetes Service (AKS) cluster. If you don't have an AKS cluster, [follow the AKS deployment guide](https://learn.microsoft.com/azure/aks/learn/quick-kubernetes-deploy-portal?tabs=azure-cli).
- **\*OPTIONAL\*** An Azure Redis Cache instance. If you don't have an Azure Redis Cache instance, [follow the Azure Redis Cache deployment guide](https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/quickstart-create-redis).

> The redis cache is optional. It is used for caching the data from the ADME instance to improve performance.

## Deploy the RAFS service

1. Launch the Azure Cloud Shell by clicking the Cloud Shell icon in the Azure portal, or navigate to [shell.azure.com](https://shell.azure.com/).

1. Select `PowerShell` as the environment.

1. Clone the GitHub repository that contains the Reservoir DDMS service deployment files:

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

1. Deploy the Reservoir DDMS service using the following commands:

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

    The output should show the pods for the Reservoir DDMS service.

1. To find the IP address of the Reservoir DDMS service, run the following command:

    ```bash
    kubectl get service -n rddms
    ```

    The output should show the IP address of the Reservoir DDMS service.