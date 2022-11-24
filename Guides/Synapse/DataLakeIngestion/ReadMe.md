# <mark style="background-color:red">Work in Progress</mark>

# Description
The intent with this solution is to automatically ingest binary data created on an external datastore into Microsoft Energy Data Services. While the example uses an Azure Data Lake, any compatible storage solutions coult theoretically be used.

# Prerequisites
These prerequisites is needed to deploy the solution above. Expand each prerequisite in the list below to see example code.
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
az account set --subscription %subscription_id%
```
</details>

<details>
<summary>Azure Resource Providers</summary>

```Powershell
az provider register --namespace Microsoft.DataFactory
az provider register --namespace Microsoft.DataLakeStore
az provider register --namespace Microsoft.OpenEnergyPlatform
az provider register --namespace Microsoft.Sql
az provider register --namespace Microsoft.Storage
az provider register --namespace Microsoft.Synapse
```
</details>

<details>
<summary>Azure Resource Group</summary>

```Powershell
az group create `
    --name <resource-group> `
    --location <location>
```
<details open>
<summary>Example</summary>

```Powershell
az group create `
    --name medssynapse-rg `
    --location westeurope
```
</details>
</details>

<details>
<summary>Azure Data Lake Storage or Azure Storage Account</summary>

```Powershell
az storage account create `
    --name <storage-account> `
    --resource-group <resource-group> `
    --sku Standard_LRS `
    --hns true
```
<details open>
<summary>Example</summary>

```Powershell
az storage account create `
    --name eirikmedsadls `
    --resource-group medssynapse-rg `
    --sku Standard_LRS `
    --hns true
```
</details>

Then create a container to use as the source.
```Powershell
az storage container create `
    --account-name <storage-account> `
    --name <container> `
    --auth-mode login
```
<details open>
<summary>Example</summary>

```Powershell
az storage container create `
    --account-name eirikmedsadls `
    --name medssource `
    --auth-mode login
```
</details>
</details>

<details>
<summary>Azure Synapse Workspace</summary>

```Powershell
az synapse workspace create `
    --name <workspace-name> `
    --file-system <filesystem> `
    --resource-group <resource-group> `
    --storage-account <storage-account>`
    --sql-admin-login-user <username> `
    --sql-admin-login-password <password> 
```
<details open>
<summary>Example</summary>

```Powershell
az synapse workspace create `
    --name eirikmedssynapse `
    --file-system synapsefs `
    --resource-group medssynapse-rg `
    --storage-account eirikmedsadls `
    --sql-admin-login-user mysqladmin `
    --sql-admin-login-password mysqlpassword1! 
```
</details>

Open the Synapse Workspace for public access.

```Powershell
az synapse workspace firewall-rule create `
    --name <rule-name> `
    --resource-group <resource-group> `
    --workspace-name <workspace-name> `
    --start-ip-address <start-ip> `
    --end-ip-address <end-ip>
```
<details open>
<summary>Example</summary>

```Powershell
az synapse workspace firewall-rule create `
    --name allowAll `
    --resource-group medssynapse-rg `
    --workspace-name eirikmedssynapse `
    --start-ip-address 0.0.0.0 `
    --end-ip-address 255.255.255.255
```
</details>
</details>

<details>
<summary>Microsoft Energy Data Services</summary>

As this is a gated Public Preview product, please see the instructions at [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/energy-data-services/quickstart-create-microsoft-energy-data-services-instance).
</details><br />

# Deploy pipeline
## Permissions
In this example pipeline we will be using the Synapse Workspace Managed Identity to ingest data into Microsoft Energy Data Services. An alternative would be to use a separate Application Registration and use Tokens to authorize the access.

### Grant Synapse Workspace access to write data to Microsoft Energy Data Services.
1. Obtain an Access Token for a user with access to write to the Microsoft Energy Data Services Entitlements service. For more information see [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/energy-data-services/how-to-manage-users).
2. Get the Synapse Workspace Managed Identity ObjectID. If multiple IDs are returned, please verify in the which ID is the correct Managed Instance ID.
    ```Powershell
    $users = az synapse role assignment list --workspace-name eirikmedssynapse | convertfrom-json
    $users | where-object {$_.principalType -eq "ServicePrincipal"} | select principalId
    ```
3. Run the below REST API call through Postman or other API tool to add the Synapse Workspace Managed Identity ObjectID to the users.datalake.editors group.
    ```Powershell
    curl --location --request POST 'https://<instance>.energy.azure.com/api/entitlements/v2/groups/users.datalake.editors@<data-partition-id>.dataservices.energy/members' `
        --header 'data-partition-id: <data-partition-id>' `
        --header 'Authorization: Bearer <access_token>' `
        --header 'Content-Type: application/json' `
        --data-raw '{
                        "email": "<Synapse_Managed-Instance_Object_ID>",
                        "role": "MEMBER"
                    }'
    ```
    <details>
    <summary>Example</summary>

    ```Powershell
    curl --location --request POST 'https://eirikmeds.energy.azure.com/api/entitlements/v2/groups/users.datalake.editors@eirikmeds-opendes.dataservices.energy/members' \
        --header 'data-partition-id: eirikmeds-opendes' \
        --header 'Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1Ni...' \
        --header 'Content-Type: application/json' \
        --data-raw '{
                        "email": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
                        "role": "MEMBER"
                    }'
    ```
    </details>

4. Make sure you get a <mark style="background-color:green">HTTP/1.1 200 OK</mark> response.
    <details>
    <summary>Sample Response</summary>

    ```JSON
    HTTP/1.1 200 OK
    Date: Wed, 23 Nov 2022 12:11:41 GMT
    Content-Type: application/json
    Transfer-Encoding: chunked
    Connection: close
    set-cookie: JSESSIONID=; Path=/api/entitlements/v2; Secure; HttpOnly
    x-frame-options: DENY
    strict-transport-security: max-age=31536000; includeSubDomains
    cache-control: no-cache, no-store, must-revalidate
    access-control-allow-origin: *
    access-control-allow-credentials: true
    access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH
    x-content-type-options: nosniff
    content-security-policy: default-src 'self'
    expires: 0
    x-xss-protection: 1; mode=block
    access-control-max-age: 3600
    access-control-allow-headers: access-control-allow-origin, origin, content-type, accept, authorization, data-partition-id, correlation-id, appkey
    x-envoy-upstream-service-time: 262
    server: istio-envoy

    {
    "email": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "role": "MEMBER"
    }
    ```
    </details>

## Linked Services and Datasets
Now we will create the Synapse Linked Services and the Datasets to be used in the Synapse Pipeline.

### Create Source Linked Service
This is the linked service for the source container where we will fetch data from.
We've already created this Azure Data Lake Storage, as well as the container (medssource) as listed in the prerequisites.

### Create Source Dataset
1. Download the [dataset-source.json](src/dataset-source.json) to your local disk.
2. Modify the <mark style="background-color:green">linked-service-name</mark> value to your Linked Service name.  
You may find the linked services in your Synapse workspace by running the following command:
    ```Powershell
    $linkedservice = az synapse linked-service list --workspace-name eirikmedssynapse | ConvertFrom-Json
    $linkedservice | select name
    ```
3. Run the following command and refer to the downloaded JSON file.
    ```Powershell
    az synapse dataset create `
        --name <dataset-name> `
        --workspace-name <workspace-name> `
        --file @<path-to>/dataset-source.json
    ```

    <details>
    <summary>Example</summary>

    ```Powershell
    az synapse dataset create `
        --name dataset_source_meds `
        --workspace-name eirikmedssynapse `
        --file @C:/Temp/dataset-source.json
    ```
    </details>

4. Verify that the dataset was created successfully.

### Create Target Linked Service
1. Download the [linkedservice-target.json](src/linkedservice-target.json) to your local machine.
2. Run the following command and refer to the downloaded JSON file.
    ```Powershell
        az synapse linked-service create `
            --name <linked-service-name> `
            --workspace-name <workspace-name> `
            --file @<path-to>/linkedservice-target.json
    ```
    <details>
    <summary>Example</summary>

    ```Powershell
    az synapse linked-service create `
        --name meds-staging-area `
        --workspace-name eirikmedssynapse `
        --file @C:/Temp/linkedservice-target.json
    ```
    </details>
3. Verify that the linked service was created successfully.

### Create Target Dataset
1. Download the [dataset-target.json](src/dataset-target.json) to your local machine.
2. Replace the <mark style="background-color:green">target-linked-service-name</mark> value with the value of your target linkedservice created in the previous step.
3. Run the following command to create the dataset.
    ```Powershell
    az synapse dataset create `
        --name <target-dataset-name> `
        --workspace-name <workspace-name> `
        --file @<path-to>/dataset-target.json
    ```
    <details>
    <summary>Example</summary>

    ```Powershell
    az synapse dataset create `
        --name dataset_target_meds `
        --workspace-name eirikmedssynapse `
        --file @C:/Temp/dataset-target.json
    ```
    </details>
4. Verify that the dataset was created successfully.

### Create pipeline
Now we will deploy the actual pipeline which will migrate the files from the source container into the Microsoft Energy Data Services staging area.

1. Download the [pipeline-mi.json](src/pipeline-mi.json) to your local machine.
2. Replace all of the values <> in the pipeline-mi.json file.
3. Run the following command to create the pipeline.
    ```Powershell
    az synapse pipeline create `
        --name <pipeline-name> `
        --workspace-name <workspace-name> `
        --file @<path-to>/pipeline-mi.json
    ```

    <details>
    <summary>Example</summary>

    ```Powershell
    az synapse pipeline create `
        --name meds-adls-pipeline `
        --workspace-name eirikmedssynapse `
        --file @C:/Temp/pipeline-mi.json
    ```
    </details>
4. Verify that the pipeline was created successfully.

### Create trigger
Now we will create the trigger which automatically triggers the pipeline we just created.

1. Download [trigger.json](src/trigger.json).
2. Update all the values as needed <>. 
3. Run the following command to deploy the trigger.
    ```Powershell
    az synapse trigger create `
        --name <trigger-name> `
        --workspace-name <workspace-name> `
        --file @<path-to>/trigger.json
    ```

    <details>
    <summary>Example</summary>

    ```Powershell
    az synapse trigger create `
        --name adls-source-trigger `
        --workspace-name eirikmedssynapse `
        --file @C:/Temp/trigger.json
    ```
    </details>
4. Validate that the trigger was created successfully.

## Test and validate pipeline
You should now have a working Synapse pipeline that will trigger every time a file is uploaded to the source container on the source linked service.

To test the pipeline we will upload a test-file to the container and verify that the trigger works and that the pipeline is successful. 

In this example I'll be ingesting a Well Trajectory file from the open-source Volve dataset, available [here](https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data/-/tree/master/rc--3.0.0/1-data/3-provided/Volve/work-products/trajectories).
<br /><br />

Once you've downloaded that you can choose how to upload it to the ADLS Container. I'll be using the Azure CLI with the following command.

```Powershell
az storage blob upload `
    --account-name <storage-account-name> `
    --container-name <container-name> `
    --name <target-file-name> `
    --file <path-to-source-file>
    --auth-mode login
```

<details>
<summary>Example</summary>

```Powershell
az storage blob upload `
    --account-name eirikmedsadls `
    --container-name medssource `
    --file C:\Temp\Volve\volve\trajectories\NPD-3145.csv
    --auth-mode login
```
</details>

### Check that trigger has been triggered
In the Synapse Studio (web portal), go to *Monitor* and then to *Trigger runs*.
Verify that the trigger has successfully run immediately after uploading the file to the container.

![Monitor trigger runs](img/validate-trigger-runs.png)

### Check that pipeline has run successfully
