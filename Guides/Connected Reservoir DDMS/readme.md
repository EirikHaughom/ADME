# Deploying a Connected Reservoir DDMS on Azure Data Manager for Energy (ADME)

This guide will walk you through deploying a Reservoir DDMS service connected to an Azure Data Manager for Energy (ADME) instance using Azure Kubernetes Service (AKS).

## Prerequisites

- An Azure subscription. If you don't have an Azure subscription, create a [free account](https://azure.microsoft.com/free/) before you begin.
- An Azure Data Manager for Energy (ADME) instance. If you don't have an ADME instance, [follow the ADME deployment guide](https://learn.microsoft.com/azure/energy-data-services/quickstart-create-microsoft-energy-data-services-instance).
- An Azure PostgreSQL flexible server. If you don't have an Azure PostgreSQL database, [follow the PostgreSQL deployment guide](https://learn.microsoft.com/azure/postgresql/flexible-server/quickstart-create-server-portal).
- An Azure Kubernetes Service (AKS) cluster. If you don't have an AKS cluster, [follow the AKS deployment guide](https://learn.microsoft.com/azure/aks/learn/quick-kubernetes-deploy-portal?tabs=azure-cli).

> [!WARNING]
> If you are using private network connectivity, the Azure Kubernetes Service (AKS) cluster must be routable to the Azure PostgreSQL flexible server and the Azure Data Manager for Energy (ADME) instance. Ensure that the AKS cluster is deployed in the same or a peered virtual network as the Azure PostgreSQL flexible server and the ADME instance.

## Connect AKS to database

First we need to create a connection between AKS and the Azure PostgreSQL flexible server. This can be done by using the [Service Connector](https://learn.microsoft.com/en-us/azure/service-connector/) feature (preview), or [Azure Key Vault](https://learn.microsoft.com/en-us/azure/aks/csi-secrets-store-driver).

For this guide we will use the `Service Connector` feature. Note that the `Service Connector` feature is in preview and may not be available in all regions. See the [Service Connector documentation](https://learn.microsoft.com/en-us/azure/service-connector/concept-region-support) for more information.

1. Launch the Azure Cloud Shell from the Azure portal, or click the following button to open the Azure Cloud Shell directly:

    [![Open in Remote - Containers](https://img.shields.io/static/v1?style=for-the-badge&label=Azure%20Cloud%20Shell&message=Open&color=blue&logo=microsoftazure)](https://shell.azure.com)

1. Make sure you are connected to the correct subscription by running the following command:

    ```bash
    az account show
    ```

    If you need to change the subscription, list the available subscriptions using the following command:

    ```bash
    az account list --output table
    ```

    Set the correct subscription using the following command:

    ```bash
    az account set --subscription "<subscription-id>"
    ```

1. Deploy the Resource Provider in your subscription using the following command:

    ```bash
    az provider register --namespace Microsoft.ServiceLinker
    ```

1. Define variables.

    ```bash
    ### AKS cluster variables
    export AKS_CLUSTER_NAME="example" # Replace with AKS cluster name
    export AKS_RESOURCE_GROUP="example-rg" # Replace with AKS resource group

    ### PostgreSQL flexible server variables
    export POSTGRESQL_FLEXIBLE_SERVER_NAME="example" # Replace with PostgreSQL flexible server name (do not include .postgres.database.azure.com)
    export POSTGRESQL_RESOURCE_GROUP="example-rg" # Replace with PostgreSQL resource group
    export POSTGRESQL_DATABASE_NAME="rddms" # Replace with PostgreSQL database name
    export POSTGRESQL_USERNAME="azureuser" # Replace with PostgreSQL username
    export POSTGRESQL_PASSWORD="<password>" # Replace with PostgreSQL password

    ### Azure Data Manager for Energy (ADME variables)
    export ADME_INSTANCE_NAME="contoso.energy.azure.com" # Replace with ADME instance name
    export ADME_DATA_PARTITION_ID="opendes" # Replace with ADME data partition ID

    ### Expose publicly
    export INTERNAL_LOAD_BALANCER="true" # If set to false, the connection will be created using a public IP on the AKS load balancer for public access, if you are using private network connectivity (or plan to expose the service to the internet using a different method), set this to true

    ### Reservoir DDMS service variables
    export RDDMS_REST_MAIN_URL="http://localhost" # If you use a different method to expose the ETP REST API service to the internet, set this to the public DNS endpoint of the service or custom domain
    export RDDMS_ETP_REPLICAS=3 # Target number of replicas for the ETP server, scaling beyond this number might happen depending on the load and AKS configuration
    export RDDMS_CLIENT_REPLICAS=3 # Target number of replicas for the ETP REST API server, scaling beyond this number might happen depending on the load and AKS configuration. Set to 0 if you don't want to deploy the ETP REST API server
    ```

1. Connect AKS to Azure PostgreSQL flexible server using Service Connector by executing the following command:

    ```bash
    az aks connection create postgres-flexible --resource-group $AKS_RESOURCE_GROUP --name $AKS_CLUSTER_NAME --kube-namespace rddms --target-resource-group $POSTGRESQL_RESOURCE_GROUP --server $POSTGRESQL_FLEXIBLE_SERVER_NAME --database $POSTGRESQL_DATABASE_NAME --connection rddmspostgresconnection --client-type none --secret name=$POSTGRESQL_USERNAME secret=$POSTGRESQL_PASSWORD
    ```

> [!IMPORTANT]
> By exposing the service publicly using the `AKS load balancer` it will not support Secure Websocket (wss) and HTTPS protocols. We recommend to use a different method to expose the service to the internet, such as Azure Application Gateway, Istio ingress gateway, or Azure API Management service. See the [Expose the Reservoir DDMS service to the internet](#expose-the-reservoir-ddms-service-to-the-internet) section for more information.

## Configuration

1. Clone the GitHub repository that contains the Reservoir DDMS service deployment files:

    ```bash
    git clone https://github.com/EirikHaughom/ADME.git
    cd ADME/Guides/Connected\ Reservoir\ DDMS/
    ```

1. Replace the values in the [Values.yaml](Values.yaml) file.

    ```bash
    cat > Values.yaml << EOF
    # This file contains the essential configs for the rddms on azure helm chart
    ################################################################################
    # Specify the values for each service.
    #
    global:
      etpserver:
        namespace: rddms
        name: etpserver
        replicaCount: $RDDMS_ETP_REPLICAS
        image:
          repository: community.opengroup.org:5555
          name: osdu/platform/domain-data-mgmt-services/reservoir/open-etp-server/open-etp-server-main
          tag: latest
        service:
          type: LoadBalancer
          annotations:
            service.beta.kubernetes.io/azure-load-balancer-internal: $INTERNAL_LOAD_BALANCER
        configuration:
          RDMS_DATA_PARTITION_MODE: single
          RDMS_DATA_CONNECTIVITY_MODE: osdu
          DOMAIN_NAME: dataservices.energy
          ADME_INSTANCE_NAME: $ADME_INSTANCE_NAME
      etpclient:
        namespace: rddms
        name: etpclient
        replicaCount: $RDDMS_CLIENT_REPLICAS
        image:
          repository: community.opengroup.org:5555
          name: osdu/platform/domain-data-mgmt-services/reservoir/open-etp-client/open-etp-client-main
          tag: latest
        service:
          type: LoadBalancer
          annotations:
            service.beta.kubernetes.io/azure-load-balancer-internal: $INTERNAL_LOAD_BALANCER
        configuration:
          RDMS_ETP_PORT: '"80"'
          RDMS_ETP_PROTOCOL: ws
          RDMS_REST_PORT: '"8003"'
          RDMS_AUTHENTICATION_KEY_BASE: "0000000-0000-0000-0000-000000000000"
          RDMS_REST_ROOT_PATH: "/Reservoir/v2"
          RDMS_REST_MAIN_URL: $RDDMS_REST_MAIN_URL
          RDMS_DATA_PARTITION_MODE: single
          OPEN_API_PORT: '"443"'
          RDMS_TEST_DATA_PARTITION_ID: $ADME_DATA_PARTITION_ID
    EOF
    ```

## Deploy the Reservoir DDMS service to the AKS cluster

1. Connect to the AKS cluster
  
    ```bash
    az aks get-credentials --resource-group $AKS_RESOURCE_GROUP --name $AKS_CLUSTER_NAME --admin
    ```

1. Deploy the Reservoir DDMS service using the following commands:

    ```bash
    # Build HELM charts
    helm dependency build
    
    # Create AKS namespace
    kubectl create namespace rddms

    # Deploy HELM charts
    helm upgrade -i adme-connected-rddms . -n rddms -f Values.yaml
    ```

1. Verify the deployment by running the following command:

    ```bash
    kubectl get pods -n rddms
    ```

    The output should show the pods for the Reservoir DDMS service.

1. To find the IP address of the Reservoir DDMS service, run the following command:

    ```bash
    kubectl get service -n rddms
    ```

    The output should show the IP address of the Reservoir DDMS service.

## Expose the Reservoir DDMS service to the internet

By default, the Reservoir DDMS service is exposed to the internet using the AKS load balancer with a public IP. If you want to expose the service to the internet using a different method, you can modify the solution to use a different service type, such as:

- [Azure Application Gateway](https://learn.microsoft.com/en-us/azure/application-gateway/ingress-controller-expose-service-over-http-https)
- [Istio ingress gateway](https://learn.microsoft.com/en-us/azure/aks/istio-secure-gateway)
- [Azure API Management service](https://learn.microsoft.com/en-us/azure/api-management/api-management-kubernetes)

> [!NOTE]
> If you want to use other methods to expose the service to the internet, you need to verify that it supports Secure Websocket (wss) and HTTPS protocols.

## Test the Reservoir DDMS service

1. Create the following groups in your ADME instance:

    | Group Name | Description |
    |------------|-------------|
    | `service.reservoir-dms.owners` | Owners of the Reservoir DDMS service |
    | `service.reservoir-dms.viewers` | Viewers of the Reservoir DDMS service |

1. Add users to the groups.

1. See the [Reservoir DDMS service documentation](https://community.opengroup.org/osdu/platform/domain-data-mgmt-services/reservoir/open-etp-server/-/blob/main/docs/testing.md) for more information on how to use the service.
