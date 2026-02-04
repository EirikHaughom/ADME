"""
Cleanup script to delete test ontologies from a Fabric workspace.

Usage:
    python cleanup_ontologies.py --workspace-id <id> --list
    python cleanup_ontologies.py --workspace-id <id> --delete-pattern "OSDU_Test"
    python cleanup_ontologies.py --workspace-id <id> --delete-all-except "OSDU_Production"
"""

import argparse
import json
import sys
import re

try:
    from azure.identity import DefaultAzureCredential
    import requests
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install azure-identity requests")
    sys.exit(1)


FABRIC_API_BASE = "https://api.fabric.microsoft.com/v1"
FABRIC_SCOPE = "https://api.fabric.microsoft.com/.default"


def get_token():
    credential = DefaultAzureCredential()
    return credential.get_token(FABRIC_SCOPE).token


def list_ontologies(token: str, workspace_id: str) -> list:
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies"
    
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        print(f"Failed to list ontologies: {response.status_code}")
        print(response.text)
        return []


def delete_ontology(token: str, workspace_id: str, ontology_id: str) -> bool:
    headers = {"Authorization": f"Bearer {token}"}
    endpoint = f"{FABRIC_API_BASE}/workspaces/{workspace_id}/ontologies/{ontology_id}"
    
    response = requests.delete(endpoint, headers=headers)
    return response.status_code in (200, 202, 204)


def main():
    parser = argparse.ArgumentParser(description="Cleanup test ontologies from Fabric workspace")
    parser.add_argument("--workspace-id", required=True, help="Fabric workspace ID")
    parser.add_argument("--list", action="store_true", help="List all ontologies")
    parser.add_argument("--delete-pattern", help="Delete ontologies matching this regex pattern")
    parser.add_argument("--delete-all-except", help="Delete all except ontologies matching this pattern")
    parser.add_argument("--delete-ids", nargs="+", help="Delete specific ontology IDs")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")
    parser.add_argument("--interactive", action="store_true", help="Use browser login")
    
    args = parser.parse_args()
    
    print("Authenticating...")
    token = get_token()
    
    ontologies = list_ontologies(token, args.workspace_id)
    
    if args.list or (not args.delete_pattern and not args.delete_all_except and not args.delete_ids):
        print(f"\nOntologies in workspace ({len(ontologies)} total):")
        print("-" * 60)
        for ont in ontologies:
            print(f"  {ont.get('displayName')}")
            print(f"    ID: {ont.get('id')}")
        return
    
    # Determine which to delete
    to_delete = []
    
    if args.delete_ids:
        to_delete = [ont for ont in ontologies if ont.get('id') in args.delete_ids]
    elif args.delete_pattern:
        pattern = re.compile(args.delete_pattern, re.IGNORECASE)
        to_delete = [ont for ont in ontologies if pattern.search(ont.get('displayName', ''))]
    elif args.delete_all_except:
        pattern = re.compile(args.delete_all_except, re.IGNORECASE)
        to_delete = [ont for ont in ontologies if not pattern.search(ont.get('displayName', ''))]
    
    if not to_delete:
        print("No ontologies matched the criteria.")
        return
    
    print(f"\nOntologies to delete ({len(to_delete)}):")
    for ont in to_delete:
        print(f"  - {ont.get('displayName')} ({ont.get('id')})")
    
    if args.dry_run:
        print("\n[DRY RUN] No ontologies were deleted.")
        return
    
    # Confirm
    confirm = input(f"\nDelete {len(to_delete)} ontologies? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Delete
    success = 0
    failed = 0
    for ont in to_delete:
        ont_id = ont.get('id')
        ont_name = ont.get('displayName')
        print(f"Deleting {ont_name}...", end=" ")
        
        if delete_ontology(token, args.workspace_id, ont_id):
            print("✓")
            success += 1
        else:
            print("✗")
            failed += 1
    
    print(f"\nDeleted: {success}, Failed: {failed}")


if __name__ == "__main__":
    main()
