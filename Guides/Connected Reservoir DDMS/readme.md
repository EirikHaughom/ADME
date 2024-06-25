# Deploying a Connected Reservoir DDMS on Azure Data Manager for Energy (ADME)

This guide will walk you through deploying a Reservoir DDMS service connected to an Azure Data Manager for Energy (ADME) instance using Azure Kubernetes Service (AKS).

## Prerequisites

- An Azure subscription. If you don't have an Azure subscription, create a [free account](https://azure.microsoft.com/free/) before you begin.
- An Azure Data Manager for Energy (ADME) instance. If you don't have an ADME instance, [follow the ADME deployment guide](https://learn.microsoft.com/azure/energy-data-services/quickstart-create-microsoft-energy-data-services-instance).
- An Azure PostgreSQL flexible server. If you don't have an Azure PostgreSQL database, [follow the PostgreSQL deployment guide](https://learn.microsoft.com/azure/postgresql/flexible-server/quickstart-create-server-portal).
- An Azure Kubernetes Service (AKS) cluster. If you don't have an AKS cluster, [follow the AKS deployment guide](https://learn.microsoft.com/azure/aks/learn/quick-kubernetes-deploy-portal?tabs=azure-cli).
- (optional) An Azure Key Vault. If you don't have an Azure Key Vault, [follow the Key Vault deployment guide](https://learn.microsoft.com/azure/key-vault/quick-create-portal).*

\* The Azure Key Vault is optional, but recommended for storing sensitive information such as connection strings. There are other solutions available as well, such as [HashiCorp Vault Enterprise on Azure Kubernetes Service](https://developer.hashicorp.com/vault/tutorials/kubernetes?ajs_aid=5bbd8d7a-e31c-4576-9e7b-0db256a0453e&product_intent=vault&utm_channel_bucket=paid) or [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets).

> [!WARNING]
> If you are using private network connectivity, the Azure Kubernetes Service (AKS) cluster must be routable to the Azure PostgreSQL flexible server and the Azure Data Manager for Energy (ADME) instance. Ensure that the AKS cluster is deployed in the same or a peered virtual network as the Azure PostgreSQL flexible server and the ADME instance.

## Configuration

1. Launch the Azure Cloud Shell from the Azure portal, or click the following button to open the Azure Cloud Shell directly:

    [![Launch Azure Cloud Shell](https://shell.azure.com/images/launchcloudshell.png "Launch Azure Cloud Shell")](https://shell.azure.com)

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

1. Clone the GitHub repository that contains the Reservoir DDMS service deployment files:

    ```bash
    git clone https://github.com/EirikHaughom/ADME.git
    cd /Guides/Connected%20Reservoir%20DDMS
    ```

1. Define values.

    ```bash
    export AKS_CLUSTER_NAME="example" # Replace with AKS cluster name
    export AKS_RESOURCE_GROUP="example-rg" # Replace with AKS resource group
    export POSTGRESQL_FLEXIBLE_SERVER_NAME="example.postgres.database.azure.com" # Replace with PostgreSQL flexible server name
    export POSTGRESQL_DATABASE_NAME="rddms" # Replace with PostgreSQL database name
    export POSTGRESQL_USERNAME="azureuser" # Replace with PostgreSQL username
    export POSTGRESQL_PASSWORD="<password>" # Replace with PostgreSQL password
    export ADME_INSTANCE_NAME="contoso.energy.azure.com" # Replace with ADME instance name
    export ADME_DATA_PARTITION_ID="opendes" # Replace with ADME data partition ID
    ```

1. Replace the values in the [Values.yaml](Values.yaml) file.

    ```bash
    cat > Values.yaml << EOF
    # This file contains the essential configs for the gcz on azure helm chart
    ################################################################################
    # Specify the values for each service.
    #
    global:
      etpserver:
        namespace: rddms
        name: etpserver
        replicaCount: 3 # Number of replicas for the service
        image:
          repository: community.opengroup.org:5555
          name: osdu/platform/domain-data-mgmt-services/reservoir/open-etp-server/open-etp-server-main
          tag: latest
          command: '[ "openETPServer", "server", "--start", "--log_level", "info", "--port", "9002", "--authZ", "delegate=https://$ADME_INSTANCE_NAME", "--authN", "none" ]'
        service:
          type: LoadBalancer
          annotations:
            service.beta.kubernetes.io/azure-load-balancer-internal: "true"
        configuration:
          RDMS_DATA_PARTITION_MODE: single
          RDMS_DATA_CONNECTIVITY_MODE: osdu
          DOMAIN_NAME: dataservices.energy
          POSTGRESQL_CONN_STRING: host=$POSTGRESQL_FLEXIBLE_SERVER_NAME port=5432 dbname=$POSTGRESQL_DATABASE_NAME user=$POSTGRESQL_USERNAME password=$POSTGRESQL_PASSWORD
      etpclient:
        namespace: rddms
        name: etpclient
        replicaCount: 3
        image:
          repository: community.opengroup.org:5555
          name: osdu/platform/domain-data-mgmt-services/reservoir/open-etp-client/open-etp-client-main
          tag: latest
        service:
          type: LoadBalancer
          annotations:
            service.beta.kubernetes.io/azure-load-balancer-internal: "true"
        configuration:
          RDMS_ETP_PORT: '"80"'
          RDMS_ETP_PROTOCOL: ws
          RDMS_REST_PORT: '"8003"'
          RDMS_AUTHENTICATION_KEY_BASE: "0000000-0000-0000-0000-000000000000"
          RDMS_REST_ROOT_PATH: "/Reservoir/v2"
          RDMS_REST_MAIN_URL: "http://localhost" # If you plan to expose the service to the internet, replace localhost with the public IP address or hostname of the service
          RDMS_DATA_PARTITION_MODE: single
          OPEN_API_PORT: '"80"' # If you plan to expose the service to the internet, replace 80 with the desired port (i.e. 443).
          RDMS_TEST_DATA_PARTITION_ID: $ADME_DATA_PARTITION_ID
    EOF
    ```

> [!IMPORTANT]
> The `POSTGRESQL_CONN_STRING` value will be viewable by anyone with access to the Kubernetes cluster. It is recommended to store the connection string in an Azure Key Vault and referencing it in the deployment template. See [Azure Key Vault provider with Secrets Store CSI Driver](https://learn.microsoft.com/azure/aks/csi-secrets-store-driver) for more information.

## Deploy the Reservoir DDMS service to the AKS cluster

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

There are multiple ways to expose the Reservoir DDMS service to the internet, such as using Azure Application Gateway, Istio ingress gateway, or an Azure API Management service.

For this guide we will use an Azure API Management service to expose the Reservoir DDMS service to the internet.

### Prerequisites

- An Azure API Management service. If you don't have an Azure API Management service, [follow the API Management deployment guide](https://learn.microsoft.com/azure/api-management/get-started-create-service-instance).

> [!WARNING]
> The Azure API Management service must be routable to the Azure Kubernetes Service (AKS) cluster. Ensure that the Azure API Management service is deployed in the same or a peered virtual network as the AKS cluster.

### Add the Reservoir DDMS APIs to the Azure API Management service

1. Define values.

    ```bash
    export APIM_SERVICE_NAME="example" # Replace with API Management service name
    ```

1. In the Azure Shell, run the following command to get the Reservoir DDMS  service IP addresses:

    ```bash
    $ETPSERVER_IP=$(kubectl get service etpserver -n rddms -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    $ETPCLIENT_IP=$(kubectl get service etpclient -n rddms -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    ```

1. Add the Reservoir DDMS APIs to the Azure API Management service using the following commands:

    ```bash
    # Add the ETP server API
    az apim api create --service-name $APIM_SERVICE_NAME --api-id "etpserver" --path "/" --display-name "ETP Server" --service-url "http://$ETPSERVER_IP:80" --protocols "wss"

    # Add the ETP client API
    az apim api create --service-name $APIM_SERVICE_NAME --api-id "etpclient" --path "/Reservoir/v2" --display-name "ETP Client" --service-url "http://$ETPCLIENT_IP:80" --protocols "https"
    ```

1. 