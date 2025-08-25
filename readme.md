# Azure Data Manager for Energy (ADME) Solutions Repository

This repository contains comprehensive guides, tools, and solutions for deploying, configuring, and integrating Azure Data Manager for Energy (ADME) with various Azure services and external systems. These solutions are designed to help organizations maximize the value of their OSDU-based energy data platform.

## 🚀 Quick-Start Solutions

### Data Integration & Management

- **[Automatic Data Lake Ingestion](/Guides/Synapse/DataLakeIngestion/)** - Automated pipeline for ingesting binary data from Azure Data Lake Storage (ADLS) into ADME using Azure Synapse Analytics
- **[Schema Upgrade Tool](/Guides/Schema%20Upgrade%20Tool/)** - Automated container-based tool for upgrading OSDU schema versions in your ADME instance

### Domain Data Management Services (DDMS)

- **[Connected Production DDMS](/Guides/Connected%20Production%20DDMS/)** - Deploy production data management services with Azure App Services and PostgreSQL
- **[Connected Reservoir DDMS](/Guides/Connected%20Reservoir%20DDMS/)** - Kubernetes-based reservoir data management service deployment guide
- **[Connected Rock and Fluid DDMS](/Guides/Connected%20Rock%20and%20Fluid%20DDMS/)** - Sample rock and fluid data management service using Azure Container Apps or AKS

### Authentication & Security

- **[Azure AD to Entitlements Sync](/Guides/AADEntitlementsSync/)** - Logic App solution for synchronizing Azure AD groups with ADME entitlements, supporting dynamic group assignments
- **[Dedicated Token App Registration](/Guides/Azure%20AD/Dedicated%20Token%20App%20Registration/)** - Secure token provisioning solution separating authentication from data access privileges

### API Management & Integration

- **[Custom Domain Configuration](/Guides/Custom%20Domain/)** - Deploy Azure API Management as a gateway with custom DNS domains for ADME APIs (supports both public and private endpoint configurations)
- **[Complete API Collections](/Guides/Postman%20Collection/)** - Comprehensive Postman and Bruno collections covering all ADME M18 core services APIs
- **[Notification Relay](https://github.com/EirikHaughom/adme-notification-relay)** - Service to relay notifications from ADME/OSDU to Azure Services
- **[Power Connector API Specifications](/Guides/Power%20Connector/)** - OpenAPI specifications for M23 services including compliance, dataset, entitlements, and various DDMS services

### Business Intelligence & Analytics

- **[Power BI Integration](/Guides/Power%20BI/)** - Ready-to-use Power BI templates for visualizing ADME data, including TNO dataset examples and generic query templates

## 📋 Solution Categories

### 🔄 Data Ingestion & Processing

| Solution | Type | Use Case |
|----------|------|----------|
| [Data Lake Ingestion](/Guides/Synapse/DataLakeIngestion/) | Azure Synapse Pipeline | Automated binary data ingestion from external storage |
| [Schema Upgrade Tool](/Guides/Schema%20Upgrade%20Tool/) | Container App | OSDU schema version management |

### 🏗️ Domain Services

| Solution | Platform | Description |
|----------|----------|-------------|
| [Production DDMS](/Guides/Connected%20Production%20DDMS/) | Azure App Services | Production data management with PostgreSQL backend |
| [Reservoir DDMS](/Guides/Connected%20Reservoir%20DDMS/) | Azure Kubernetes Service | Scalable reservoir data management |
| [Rock & Fluid DDMS](/Guides/Connected%20Rock%20and%20Fluid%20DDMS/) | Container Apps/AKS | Sample implementation for rock and fluid data |

### 🔐 Security & Access Management

| Solution | Technology | Purpose |
|----------|------------|---------|
| [AAD Entitlements Sync](/Guides/AADEntitlementsSync/) | Azure Logic Apps | Group membership synchronization |
| [Token App Registration](/Guides/Azure%20AD/Dedicated%20Token%20App%20Registration/) | Azure AD | Secure token provisioning |

### 🌐 API & Integration

| Solution | Service | Benefit |
|----------|---------|---------|
| [Custom Domain](/Guides/Custom%20Domain/) | API Management | Brand consistency and custom DNS |
| [API Collections](/Guides/Postman%20Collection/) | Postman/Bruno | Complete API testing and documentation |
| [Notification Relay](https://github.com/EirikHaughom/adme-notification-relay) | Message Queue | Service to relay notifications from ADME/OSDU to Azure Services |
| [Power Connector](/Guides/Power%20Connector/) | OpenAPI Specs | M23 service specifications |

### 📊 Analytics & Visualization

| Solution | Platform | Focus |
|----------|----------|-------|
| [Power BI Templates](/Guides/Power%20BI/) | Power BI | Data visualization and reporting |

## 🛠️ Getting Started

1. **Choose your deployment scenario** based on your organization's requirements
2. **Review prerequisites** for each solution in their respective guides
3. **Follow step-by-step instructions** provided in each guide
4. **Test and validate** your deployment using the included validation steps

## 📖 Documentation Structure

Each solution guide includes:

- **Overview** and architecture diagrams
- **Prerequisites** and dependencies
- **Step-by-step deployment** instructions
- **Configuration** parameters and options
- **Validation** and testing procedures
- **Troubleshooting** guidance
- **Cleanup** instructions

## 🤝 Contributing

I welcome contributions to improve these solutions:

- **Issues**: Report bugs or request features
- **Pull Requests**: Submit improvements or new solutions
- **Documentation**: Help improve guides and examples

Please ensure all contributions follow best practices and include appropriate documentation.

## ⚠️ Disclaimer

This repository contains community-contributed solutions and is not officially affiliated with Microsoft employment. These solutions are provided as-is for educational and reference purposes. Always review and test thoroughly before implementing in production environments.

## 📞 Support

For issues related to:

- **Azure Data Manager for Energy**: Use official Microsoft support channels
- **OSDU Platform**: Refer to the [OSDU Community](https://community.opengroup.org/osdu)
- **Repository Solutions**: Create an issue in this repository
