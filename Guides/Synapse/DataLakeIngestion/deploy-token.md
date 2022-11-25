# WORK IN PROGRESS

# Description
This is the guide to deploy the Synapse Pipeline using an Access Token. If you want to use Managed Identity instead, please see [deploy-mi.md](deploy-mi.md).

# Additional Prerequisites
In addition to the shared prerequisites, this authentication mechanism requires some additional services to store and manage secrets.

<details>
<summary>Azure Key Vault</summary>

```Powershell
az keyvault create `
    --name <key-vault-name> `
    --resource-group <resource-group> `
```

<details>
<summary>Example</summary>

```Powershell
az keyvault create `
    --name eirikkeyvault `
    --resource-group medssynapse-rg `
```
</details>
</details>

# Permissions
- Managed Identity access to KeyVault
- Add new AppReg to Entitlements















<br /><br />

# Test and validation
Please see [validation.md](validation.md) for test and validation of the pipeline and trigger.