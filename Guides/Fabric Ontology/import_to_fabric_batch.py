"""
Microsoft Fabric Ontology Batch Import Script

This script imports multiple ontology files, handling splitting for large files
that exceed Fabric's ~300 entity limit per ontology.

Usage:
    # Import all category ontologies
    python import_to_fabric_batch.py --workspace-id <your-workspace-id>
    
    # Import a single file
    python import_to_fabric_batch.py --workspace-id <id> --files osdu_fabric_masterdata.json

    # Import with a prefix for ontology names
    python import_to_fabric_batch.py --workspace-id <id> --prefix "adme"
"""

import argparse
import json
import sys
import os
import base64
import time

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
    """Acquire an access token for Microsoft Fabric API."""
    try:
        if use_interactive:
            credential = InteractiveBrowserCredential()
        else:
            credential = DefaultAzureCredential()
        
        token = credential.get_token(FABRIC_SCOPE)
        return token.token
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)


def encode_to_base64(data: dict) -> str:
    """Encode a dictionary to base64 string."""
    json_str = json.dumps(data, indent=2)
    return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')


def create_minimal_ontology(token: str, workspace_id: str, display_name: str) -> dict:
    """Create an empty ontology with just the platform metadata."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Minimal definition with just platform and empty definition
    platform_meta = {
        "metadata": {
            "type": "Ontology",
            "displayName": display_name
        }
    }
    
    minimal_definition = {
        "parts": [
            {
                "path": ".platform",
                "payload": encode_to_base64(platform_meta),
                "payloadType": "InlineBase64"
            },
            {
                "path": "definition.json",
                "payload": encode_to_base64({}),
                "payloadType": "InlineBase64"
            }
        ]
    }
    
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies"
    
    payload = {
        "displayName": display_name,
        "description": "Ontology generated from OSDU data schemas",
        "definition": minimal_definition
    }
    
    print(f"\nCreating minimal ontology '{display_name}'...")
    response = requests.post(endpoint, headers=headers, json=payload)
    
    if response.status_code in (200, 201, 202):
        result = response.json() if response.text else {}
        
        # Handle async operation
        if response.status_code == 202:
            operation_url = response.headers.get("Location")
            if operation_url:
                print("Waiting for ontology creation to complete...")
                time.sleep(5)  # Wait for async operation
        
        return result
    else:
        print(f"Failed to create ontology: {response.status_code}")
        print(response.text)
        return None


def wait_for_operation(token: str, operation_url: str, max_wait: int = 120) -> bool:
    """Wait for an async operation to complete."""
    headers = {"Authorization": f"Bearer {token}"}
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(operation_url, headers=headers)
            if response.status_code == 200:
                result = response.json()
                status = result.get("status", "").lower()
                if status in ("succeeded", "completed"):
                    return True
                elif status in ("failed", "cancelled"):
                    print(f"Operation failed: {result}")
                    return False
            time.sleep(3)
        except Exception as e:
            print(f"Error checking operation: {e}")
            time.sleep(3)
    
    print("Operation timed out")
    return False


def update_ontology_definition(
    token: str,
    workspace_id: str,
    ontology_id: str,
    parts: list
) -> bool:
    """Update ontology with a batch of parts."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies/{ontology_id}/updateDefinition"
    
    # The API expects {"definition": {"parts": [...]}}
    payload = {"definition": {"parts": parts}}
    
    response = requests.post(endpoint, headers=headers, json=payload)
    
    if response.status_code in (200, 201, 202):
        if response.status_code == 202:
            time.sleep(2)  # Brief pause for async operations
        return True
    else:
        print(f"Update failed: {response.status_code}")
        if response.text:
            print(response.text[:500])
        return False


def load_ontology_parts(filepath: str) -> list:
    """Load ontology parts from file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get("parts", [])


def split_into_batches(parts: list, batch_size: int) -> list:
    """Split parts into batches, keeping platform and definition.json in all."""
    # Separate required parts from entity/relationship parts
    required_parts = []
    entity_parts = []
    relationship_parts = []
    
    for part in parts:
        path = part.get("path", "")
        if path in (".platform", "definition.json"):
            required_parts.append(part)
        elif path.startswith("EntityTypes/"):
            entity_parts.append(part)
        elif path.startswith("RelationshipTypes/"):
            relationship_parts.append(part)
    
    batches = []
    
    # Create batches for entity types
    for i in range(0, len(entity_parts), batch_size):
        batch = required_parts.copy() + entity_parts[i:i + batch_size]
        batches.append(batch)
    
    # Create batches for relationship types
    for i in range(0, len(relationship_parts), batch_size):
        batch = required_parts.copy() + relationship_parts[i:i + batch_size]
        batches.append(batch)
    
    return batches


def list_ontologies(token: str, workspace_id: str) -> list:
    """List existing ontologies in workspace."""
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies"
    
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        return response.json().get("value", [])
    return []


def main():
    parser = argparse.ArgumentParser(
        description="Import large OSDU Ontology into Microsoft Fabric in batches"
    )
    
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace ID")
    parser.add_argument("--ontology-file", default="osdu_fabric_ontology.json")
    parser.add_argument("--display-name", default="OSDU Ontology")
    parser.add_argument("--batch-size", type=int, default=100, help="Parts per batch")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--ontology-id", help="Existing ontology ID to update")
    parser.add_argument("--start-batch", type=int, default=0, help="Resume from batch N")
    
    args = parser.parse_args()
    
    # Authenticate
    print("Authenticating...")
    token = get_access_token(use_interactive=args.interactive)
    print("Authentication successful!")
    
    # Load ontology
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ontology_path = os.path.join(script_dir, args.ontology_file) if not os.path.isabs(args.ontology_file) else args.ontology_file
    
    print(f"\nLoading ontology from: {ontology_path}")
    parts = load_ontology_parts(ontology_path)
    print(f"Total parts: {len(parts)}")
    
    # Split into batches
    batches = split_into_batches(parts, args.batch_size)
    print(f"Split into {len(batches)} batches of ~{args.batch_size} parts each")
    
    ontology_id = args.ontology_id
    
    # Create new ontology if no ID provided
    if not ontology_id:
        print("\n" + "=" * 60)
        print("Step 1: Creating minimal ontology...")
        print("=" * 60)
        
        result = create_minimal_ontology(token, args.workspace_id, args.display_name)
        
        if result:
            ontology_id = result.get("id")
            print(f"Ontology created with ID: {ontology_id}")
        else:
            # Try to find existing ontology with same name
            print("Checking for existing ontology...")
            ontologies = list_ontologies(token, args.workspace_id)
            for ont in ontologies:
                if ont.get("displayName") == args.display_name:
                    ontology_id = ont.get("id")
                    print(f"Found existing ontology: {ontology_id}")
                    break
        
        if not ontology_id:
            print("Failed to create or find ontology")
            sys.exit(1)
    
    # Update with batches
    print("\n" + "=" * 60)
    print("Step 2: Updating ontology with entity definitions...")
    print("=" * 60)
    
    success_count = 0
    fail_count = 0
    
    for i, batch in enumerate(batches):
        if i < args.start_batch:
            print(f"Skipping batch {i + 1}/{len(batches)}")
            continue
            
        print(f"\nProcessing batch {i + 1}/{len(batches)} ({len(batch)} parts)...")
        
        if update_ontology_definition(token, args.workspace_id, ontology_id, batch):
            success_count += 1
            print(f"  ✓ Batch {i + 1} succeeded")
        else:
            fail_count += 1
            print(f"  ✗ Batch {i + 1} failed")
            print(f"  Resume with: --ontology-id {ontology_id} --start-batch {i}")
        
        # Rate limiting pause
        time.sleep(1)
    
    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"Ontology ID: {ontology_id}")
    print(f"Successful batches: {success_count}")
    print(f"Failed batches: {fail_count}")
    
    if fail_count > 0:
        print(f"\nTo retry failed batches, run with: --ontology-id {ontology_id}")


if __name__ == "__main__":
    main()
