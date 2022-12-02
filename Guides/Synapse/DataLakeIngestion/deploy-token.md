# WORK IN PROGRESS

# Description
This is the guide to deploy the Synapse Pipeline using an Access Token issued from an Application Registration. If you want to use Managed Identity instead, please see [deploy-mi.md](deploy-mi.md).

# Additional Prerequisites
In addition to the shared prerequisites, this authentication mechanism requires some additional services to store and manage secrets.

<details>
<summary>Azure Key Vault</summary>

```Powershell
az keyvault create `
    --name <key-vault-name> `
    --resource-group <resource-group>
```

<details>
    <summary>Example</summary>

    ```Powershell
    az keyvault create `
        --name eirikkeyvault `
        --resource-group medssynapse-rg
    ```
</details>
</details>

<details>
<summary>Azure Application Registration</summary>

```Powershell
### Create App Registration
$clientid = (az ad app create `
    --display-name <display-name> `
    --key-type Password | `
    convertfrom-json).appId

### Create Service Principal for the App Registration
az ad sp create --id $clientid

### Generate a Secret for the App Registration
$clientsecret = (az ad app credential reset `
    --id $clientid | `
    convertfrom-json).password

### Store generated secret to KeyVault
az keyvault secret set `
    --vault-name <keyvault-name> `
    --name MEDSSynapseSecret `
    --value $clientsecret
```

<details>
<summary>Example</summary>

```Powershell
### Create App Registration
$clientid = (az ad app create `
    --display-name eirikmeds-appreg `
    --key-type Password | `
    convertfrom-json).appId

### Create Service Principal for the App Registration
az ad sp create --id $clientid

### Generate a Secret for the App Registration
$clientsecret = (az ad app credential reset `
    --id $clientid | `
    convertfrom-json).password

### Store generated secret to KeyVault
az keyvault secret set `
    --vault-name eirikkeyvault `
    --name MEDSSynapseSecret `
    --value $clientsecret
```
</details>
</details>

# Permissions

## Grant Synapse Managed Identity access to KeyVault

1. Fetch Synapse Managed Idenity ObjectID.
```Powershell
$synapsemi = (az synapse workspace show ` 
    --name <synapse-workspace> `
    --resource-group <resource-group> | `
    ConvertFrom-Json).identity.principalId
```
<details>
<summary>Example</summary>

```Powershell
$synapsemi = (az synapse workspace show `
    --name eirikmedssynapse `
    --resource-group medssynapse-rg | `
    ConvertFrom-Json).identity.principalId
```
</details>

2. Grant Synapse Managed Identity reader access to Keyvault
```Powershell
az role assignment create `
    --
```

## Add new AppReg to Entitlements















<br /><br />

# Test and validation
Please see [validation.md](validation.md) for test and validation of the pipeline and trigger.