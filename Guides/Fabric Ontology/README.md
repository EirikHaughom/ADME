# OSDU Ontology Generator

Generate ontologies from [OSDU (Open Subsurface Data Universe)](https://osduforum.org/) data schemas in multiple formats:
- **TTL/OWL** - For use with semantic web tools like [Protégé](https://protege.stanford.edu/)
- **Microsoft Fabric Ontology** - For use with [Microsoft Fabric Ontology (preview)](https://learn.microsoft.com/en-us/fabric/iq/ontology/overview)

This project is based on the [OSDU schema files and standards](https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data/-/tree/master/rc--3.0.0/3-schema).

## License

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Licensed under the Apache License 2.0 - see [LICENSE](./LICENSE).

---

## Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd <repository-folder>

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download OSDU schemas (see instructions below)

# 4. Generate ontology
python create_ontology.py -s schemas/ --format fabric -o "OSDU"
```

---

## Prerequisites

- **Python 3.10+**
- **Azure CLI** (for Fabric import) - [Install Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 1: Download OSDU Schemas

The OSDU schemas are not included in this repository. You must download them from the official OSDU repository.

### Option A: Download via Git (Recommended)

```bash
# Clone the OSDU open-test-data repository
git clone https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data.git

# Copy the schema files to your working directory
cp -r open-test-data/rc--3.0.0/3-schema schemas/
```

### Option B: Download Manually

1. Go to the [OSDU Schema Repository](https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data/-/tree/master/rc--3.0.0/3-schema)
2. Download the `3-schema` folder
3. Extract to a `schemas/` folder in this repository

### Verify Schema Download

Your folder structure should look like:
```
schemas/
├── abstract/
├── dataset/
├── master-data/
├── reference-data/
└── work-product-component/
```

---

## Step 2: Generate Ontology

### Generate TTL/OWL Ontology (Default)

```bash
python create_ontology.py -s schemas/
```

**Output:** `osdu_draft.ttl`

### Generate Microsoft Fabric Ontology

```bash
python create_ontology.py -s schemas/ --format fabric -o "OSDU"
```

**Output:** 
- `osdu_fabric_ontology.json` - Ready for Fabric API import
- `osdu_fabric_ontology_readable.json` - Human-readable version

### Generate Both Formats

```bash
python create_ontology.py -s schemas/ --format both -o "OSDU"
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --src` | Path to schema files | `osdu-ontology-generator/osdu_full_schema/` |
| `-d, --dest` | Output directory | Current directory |
| `-o, --ontology-name` | Name for the ontology | `osdu` |
| `-f, --format` | Output format: `ttl`, `fabric`, or `both` | `ttl` |
| `--id-seed` | Seed for Fabric ID generation (use different values to avoid conflicts) | `0` |
| `-v, --verbose` | Enable verbose output | `True` |
| `-m, --report_metrics` | Report ontology metrics | `False` |

---

## Step 3: Import to Microsoft Fabric (Optional)

### Prerequisites

1. **Azure Authentication** - Login to Azure:
   ```bash
   az login
   ```

2. **Fabric Workspace** - You need a Fabric workspace with Ontology (preview) enabled

3. **Permissions** - Contributor role on the workspace

### List Available Workspaces

```bash
python import_to_fabric.py --list-workspaces
```

### Import Ontology

```bash
python import_to_fabric.py \
    --workspace-id <your-workspace-id> \
    --ontology-file osdu_fabric_ontology.json \
    --display-name "OSDU_Ontology"
```

### Import Options

| Option | Description |
|--------|-------------|
| `--workspace-id` | Fabric workspace ID (required) |
| `--ontology-file` | Path to ontology JSON file |
| `--display-name` | Display name in Fabric |
| `--list-workspaces` | List available workspaces |
| `--list-ontologies` | List existing ontologies in workspace |
| `--dry-run` | Validate without importing |
| `--interactive` | Use browser-based authentication |

### Known Limitations

- **~300 entity limit per ontology** - Fabric has limits on ontology size
- **Recommendation**: For large ontologies, use `create_category_ontologies.py` to split by OSDU category

---

## Additional Tools

### Cleanup Test Ontologies

Delete ontologies from a Fabric workspace:

```bash
# List ontologies
python cleanup_ontologies.py --workspace-id <id> --list

# Delete by pattern (dry run)
python cleanup_ontologies.py --workspace-id <id> --delete-pattern "Test" --dry-run

# Delete by pattern (actual delete)
python cleanup_ontologies.py --workspace-id <id> --delete-pattern "Test"
```

### Generate Category-Based Ontologies

Split the ontology by OSDU category (MasterData, ReferenceData, etc.):

```bash
python create_category_ontologies.py -s schemas/
```

---

## Project Structure

```
├── create_ontology.py           # Main ontology generator
├── import_to_fabric.py          # Fabric import script
├── import_to_fabric_batch.py    # Batch import for large ontologies
├── cleanup_ontologies.py        # Delete ontologies from Fabric
├── create_category_ontologies.py # Generate ontologies by category
├── requirements.txt             # Python dependencies
├── src/
│   ├── fabric_utils.py          # Fabric ontology generation
│   ├── ttl_utils.py             # TTL/OWL generation
│   ├── kg_rep.py                # Knowledge graph representation
│   ├── json_utils.py            # Schema loading utilities
│   └── str_utils.py             # String processing utilities
├── docs/                        # Documentation
├── ttl/                         # Pre-generated TTL files
└── OntologyValidation/          # Validation tools
```

---

## Documentation

See the [docs](./docs) folder for detailed information about:
- OSDU data model overview
- Ontology design decisions
- Class hierarchy and relationships

---

## Troubleshooting

### Authentication Failed

```bash
# Re-authenticate with Azure
az login

# Or use interactive browser login
python import_to_fabric.py --workspace-id <id> --interactive
```

### "ID Conflicts" Error in Fabric

Use a different `--id-seed` value when regenerating the ontology:

```bash
python create_ontology.py -s schemas/ --format fabric --id-seed 1000
```

### Missing Python Modules

```bash
pip install -r requirements.txt
```

### Schema Files Not Found

Ensure you've downloaded the OSDU schemas to the correct location. See [Step 1](#step-1-download-osdu-schemas).

---

## Contributing

Contributions are welcome! Please read the license terms before contributing.

## References

- [OSDU Forum](https://osduforum.org/)
- [OSDU Schema Repository](https://community.opengroup.org/osdu/platform/data-flow/data-loading/open-test-data/)
- [Microsoft Fabric Ontology Documentation](https://learn.microsoft.com/en-us/fabric/iq/ontology/overview)
- [Fabric Ontology REST API](https://learn.microsoft.com/en-us/rest/api/fabric/ontology/items/create-ontology)
