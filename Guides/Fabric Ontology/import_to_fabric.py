"""
Microsoft Fabric Ontology Import Script

This script imports the generated OSDU Fabric Ontology JSON into a Microsoft Fabric workspace.

Prerequisites:
    pip install azure-identity requests

Authentication:
    Uses DefaultAzureCredential which supports multiple authentication methods:
    - Azure CLI (az login)
    - Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
    - Managed Identity (when running in Azure)
    - Interactive browser login (fallback)

Usage:
    python import_to_fabric.py --workspace-id <your-workspace-id>
    python import_to_fabric.py --workspace-id <your-workspace-id> --ontology-file osdu_fabric_ontology.json
    python import_to_fabric.py --workspace-id <your-workspace-id> --display-name "My OSDU Ontology"

Reference:
    https://learn.microsoft.com/en-us/rest/api/fabric/ontology/items/create-ontology
"""

import argparse
import json
import sys
import os

try:
    from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
    import requests
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install azure-identity requests")
    sys.exit(1)


FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"


def get_access_token(use_interactive: bool = False) -> str:
    """
    Acquire an access token for Microsoft Fabric API.
    
    Args:
        use_interactive: If True, forces interactive browser login
        
    Returns:
        Access token string
    """
    try:
        if use_interactive:
            credential = InteractiveBrowserCredential()
        else:
            credential = DefaultAzureCredential()
        
        token = credential.get_token(FABRIC_SCOPE)
        return token.token
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("\nTry one of the following:")
        print("  1. Run 'az login' to authenticate with Azure CLI")
        print("  2. Set environment variables: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET")
        print("  3. Use --interactive flag for browser-based login")
        sys.exit(1)


def load_ontology_definition(filepath: str) -> dict:
    """
    Load the ontology definition from a JSON file.
    
    Args:
        filepath: Path to the ontology JSON file
        
    Returns:
        Ontology definition dictionary
    """
    if not os.path.exists(filepath):
        print(f"Error: Ontology file not found: {filepath}")
        sys.exit(1)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_workspaces(token: str) -> list:
    """
    List available Fabric workspaces.
    
    Args:
        token: Access token
        
    Returns:
        List of workspace dictionaries
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(f"{FABRIC_API_BASE}/workspaces", headers=headers)
    
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        print(f"Failed to list workspaces: {response.status_code}")
        print(response.text)
        return []


def create_ontology(
    token: str,
    workspace_id: str,
    display_name: str,
    description: str,
    definition: dict
) -> dict:
    """
    Create an ontology in Microsoft Fabric.
    
    Args:
        token: Access token
        workspace_id: Target workspace ID
        display_name: Display name for the ontology
        description: Description of the ontology
        definition: The ontology definition (with base64-encoded parts)
        
    Returns:
        API response dictionary
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies"
    
    payload = {
        "displayName": display_name,
        "description": description,
        "definition": definition
    }
    
    print(f"\nCreating ontology '{display_name}' in workspace {workspace_id}...")
    print(f"Endpoint: {endpoint}")
    print(f"Parts count: {len(definition.get('parts', []))}")
    
    response = requests.post(endpoint, headers=headers, json=payload)
    
    return {
        "status_code": response.status_code,
        "response": response.json() if response.text else {},
        "headers": dict(response.headers)
    }


def update_ontology(
    token: str,
    workspace_id: str,
    ontology_id: str,
    definition: dict
) -> dict:
    """
    Update an existing ontology definition in Microsoft Fabric.
    
    Args:
        token: Access token
        workspace_id: Workspace ID
        ontology_id: Existing ontology ID
        definition: The updated ontology definition
        
    Returns:
        API response dictionary
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies/{ontology_id}/updateDefinition"
    
    print(f"\nUpdating ontology {ontology_id}...")
    
    response = requests.post(endpoint, headers=headers, json=definition)
    
    return {
        "status_code": response.status_code,
        "response": response.json() if response.text else {},
        "headers": dict(response.headers)
    }


def list_ontologies(token: str, workspace_id: str) -> list:
    """
    List existing ontologies in a workspace.
    
    Args:
        token: Access token
        workspace_id: Workspace ID
        
    Returns:
        List of ontology dictionaries
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies"
    response = requests.get(endpoint, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        print(f"Failed to list ontologies: {response.status_code}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Import OSDU Ontology into Microsoft Fabric",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new ontology
  python import_to_fabric.py --workspace-id abc-123-def

  # Create with custom name
  python import_to_fabric.py --workspace-id abc-123-def --display-name "My OSDU Ontology"

  # Update existing ontology
  python import_to_fabric.py --workspace-id abc-123-def --ontology-id xyz-789 --update

  # List workspaces to find workspace ID
  python import_to_fabric.py --list-workspaces

  # List existing ontologies in workspace
  python import_to_fabric.py --workspace-id abc-123-def --list-ontologies
        """
    )
    
    parser.add_argument(
        "--workspace-id",
        help="Microsoft Fabric workspace ID (GUID)"
    )
    parser.add_argument(
        "--ontology-file",
        default="osdu_fabric_ontology.json",
        help="Path to the ontology JSON file (default: osdu_fabric_ontology.json)"
    )
    parser.add_argument(
        "--display-name",
        default="OSDU Ontology",
        help="Display name for the ontology (default: OSDU Ontology)"
    )
    parser.add_argument(
        "--description",
        default="Ontology generated from OSDU data schemas",
        help="Description for the ontology"
    )
    parser.add_argument(
        "--ontology-id",
        help="Existing ontology ID (for updates)"
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing ontology instead of creating new"
    )
    parser.add_argument(
        "--list-workspaces",
        action="store_true",
        help="List available Fabric workspaces and exit"
    )
    parser.add_argument(
        "--list-ontologies",
        action="store_true",
        help="List existing ontologies in the workspace"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Use interactive browser login for authentication"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs without making API calls"
    )
    
    args = parser.parse_args()
    
    # Get access token
    print("Authenticating with Microsoft Fabric...")
    token = get_access_token(use_interactive=args.interactive)
    print("Authentication successful!")
    
    # List workspaces
    if args.list_workspaces:
        print("\nAvailable Workspaces:")
        print("-" * 60)
        workspaces = list_workspaces(token)
        for ws in workspaces:
            print(f"  {ws.get('displayName', 'Unknown')}")
            print(f"    ID: {ws.get('id')}")
            print(f"    Type: {ws.get('type', 'Unknown')}")
            print()
        return
    
    # Validate workspace ID
    if not args.workspace_id:
        print("Error: --workspace-id is required")
        print("Use --list-workspaces to find your workspace ID")
        sys.exit(1)
    
    # List ontologies
    if args.list_ontologies:
        print(f"\nOntologies in workspace {args.workspace_id}:")
        print("-" * 60)
        ontologies = list_ontologies(token, args.workspace_id)
        if not ontologies:
            print("  No ontologies found")
        for ont in ontologies:
            print(f"  {ont.get('displayName', 'Unknown')}")
            print(f"    ID: {ont.get('id')}")
            print(f"    Description: {ont.get('description', 'N/A')}")
            print()
        return
    
    # Load ontology definition
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ontology_path = args.ontology_file
    if not os.path.isabs(ontology_path):
        ontology_path = os.path.join(script_dir, ontology_path)
    
    print(f"\nLoading ontology from: {ontology_path}")
    definition = load_ontology_definition(ontology_path)
    
    parts_count = len(definition.get("parts", []))
    print(f"Loaded {parts_count} definition parts")
    
    # Dry run check
    if args.dry_run:
        print("\n[DRY RUN] Would create/update ontology with:")
        print(f"  Display Name: {args.display_name}")
        print(f"  Description: {args.description}")
        print(f"  Workspace ID: {args.workspace_id}")
        print(f"  Parts: {parts_count}")
        return
    
    # Create or update ontology
    if args.update:
        if not args.ontology_id:
            print("Error: --ontology-id is required for updates")
            sys.exit(1)
        
        result = update_ontology(
            token=token,
            workspace_id=args.workspace_id,
            ontology_id=args.ontology_id,
            definition=definition
        )
    else:
        result = create_ontology(
            token=token,
            workspace_id=args.workspace_id,
            display_name=args.display_name,
            description=args.description,
            definition=definition
        )
    
    # Handle response
    status = result["status_code"]
    
    if status in (200, 201, 202):
        print("\n" + "=" * 60)
        print("SUCCESS! Ontology created/updated successfully.")
        print("=" * 60)
        
        if result["response"]:
            print("\nResponse:")
            print(json.dumps(result["response"], indent=2))
        
        # Check for long-running operation
        if "Location" in result["headers"]:
            print(f"\nOperation URL: {result['headers']['Location']}")
            print("The ontology is being created. Check the Fabric portal for status.")
        
        if "x-ms-operation-id" in result["headers"]:
            print(f"Operation ID: {result['headers']['x-ms-operation-id']}")
            
    elif status == 202:
        print("\nOntology creation accepted (async operation)")
        print("Check the Fabric portal for completion status.")
        
    else:
        print("\n" + "=" * 60)
        print(f"FAILED! Status code: {status}")
        print("=" * 60)
        print("\nError response:")
        print(json.dumps(result["response"], indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
