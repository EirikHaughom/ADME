"""
Fabric Ontology Generator Module

This module generates Microsoft Fabric Ontology JSON format from OSDU schema
data structures. The output can be used with the Fabric REST API to create
ontology items programmatically.

Fabric Ontology format reference:
https://learn.microsoft.com/en-us/rest/api/fabric/articles/item-management/definitions/ontology-definition
"""

import os
import json
import base64
import uuid
import hashlib
import re
from .kg_rep import PropType, literals_dict, process_name
from .str_utils import extract_classname_from_filename


def sanitize_fabric_name(name: str, max_length: int = 89) -> str:
    """
    Sanitize a name to comply with Fabric naming rules:
    - Must start with a letter
    - Less than 90 characters
    - Only letters, numbers, and underscores
    
    Args:
        name: The original name
        max_length: Maximum allowed length (default 89 to be safe)
        
    Returns:
        Sanitized name
    """
    if not name:
        return "Unknown"
    
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    
    # Remove consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'E_' + sanitized
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove trailing underscore
    sanitized = sanitized.rstrip('_')
    
    return sanitized if sanitized else "Unknown"


# Mapping from OSDU/XSD types to Fabric Ontology value types
FABRIC_TYPE_MAP = {
    "string": "String",
    "integer": "BigInt",
    "number": "Double",
    "boolean": "Boolean",
    "object": "Object",
    # Additional mappings for common patterns
    "datetime": "DateTime",
    "date": "DateTime",
    "time": "DateTime",
    "decimal": "Double",
    "float": "Double",
    "double": "Double",
    "int": "BigInt",
    "long": "BigInt",
}


# Global seed for ID generation - change this to create non-conflicting ontologies
_ID_SEED = 0


def set_id_seed(seed: int):
    """Set the global seed for ID generation to avoid conflicts between ontologies."""
    global _ID_SEED
    _ID_SEED = seed


def generate_entity_id(name: str, seed: int = None) -> str:
    """
    Generate a unique 64-bit positive integer ID from a name.
    Uses hash to ensure deterministic IDs for the same names within an ontology,
    but can be varied using a global seed to avoid conflicts between ontologies.
    
    Args:
        name: The entity or property name to generate an ID for
        seed: Optional seed for variation (uses global seed if not provided)
        
    Returns:
        A string representation of a positive 64-bit integer
    """
    if seed is None:
        seed = _ID_SEED
    # Create a deterministic hash from the name and seed
    hash_input = f"{name}_{seed}".encode('utf-8')
    hash_value = int(hashlib.sha256(hash_input).hexdigest()[:15], 16)
    # Ensure it's a positive 64-bit integer (max ~9.2e18)
    return str(hash_value % (2**63 - 1))


def map_to_fabric_type(osdu_type: str) -> str:
    """
    Map an OSDU/XSD type to a Fabric Ontology valueType.
    
    Args:
        osdu_type: The OSDU or XSD type string
        
    Returns:
        The corresponding Fabric Ontology type
    """
    type_lower = osdu_type.lower().replace("xsd:", "")
    return FABRIC_TYPE_MAP.get(type_lower, "String")


def encode_to_base64(data: dict) -> str:
    """
    Encode a dictionary to base64 string for Fabric API.
    
    Args:
        data: Dictionary to encode
        
    Returns:
        Base64 encoded string
    """
    json_str = json.dumps(data, indent=2)
    return base64.b64encode(json_str.encode('utf-8')).decode('utf-8')


def create_platform_metadata(display_name: str = "OSDU Ontology") -> dict:
    """
    Create the .platform metadata structure.
    
    Args:
        display_name: Display name for the ontology
        
    Returns:
        Platform metadata dictionary
    """
    return {
        "metadata": {
            "type": "Ontology",
            "displayName": sanitize_fabric_name(display_name)
        }
    }


def create_entity_type(
    entity_id: str,
    name: str,
    properties: list,
    base_entity_type_id: str = None,
    description: str = ""
) -> dict:
    """
    Create an EntityType definition for Fabric Ontology.
    
    Args:
        entity_id: Unique 64-bit integer ID for this entity type
        name: Name of the entity type
        properties: List of property definitions
        base_entity_type_id: ID of parent entity type (for inheritance)
        description: Optional description
        
    Returns:
        EntityType definition dictionary
    """
    # Find display name property (first string property, or first property)
    display_name_prop_id = None
    entity_id_parts = []
    
    for prop in properties:
        if prop.get("valueType") == "String":
            if display_name_prop_id is None:
                display_name_prop_id = prop["id"]
                entity_id_parts.append(prop["id"])
            break
    
    if not display_name_prop_id and properties:
        display_name_prop_id = properties[0]["id"]
        entity_id_parts.append(properties[0]["id"])
    
    entity_type = {
        "id": entity_id,
        "namespace": "usertypes",
        "baseEntityTypeId": base_entity_type_id,
        "name": sanitize_fabric_name(name),
        "entityIdParts": entity_id_parts,
        "displayNamePropertyId": display_name_prop_id,
        "namespaceType": "Custom",
        "visibility": "Visible",
        "properties": properties,
        "timeseriesProperties": []
    }
    
    return entity_type


def create_entity_property(
    prop_id: str,
    name: str,
    value_type: str,
    redefines: str = None
) -> dict:
    """
    Create an EntityType property definition.
    
    Args:
        prop_id: Unique ID for the property
        name: Property name
        value_type: Fabric value type (String, Boolean, DateTime, Object, BigInt, Double)
        redefines: ID of property being redefined (for inheritance)
        
    Returns:
        Property definition dictionary
    """
    return {
        "id": prop_id,
        "name": sanitize_fabric_name(name),
        "redefines": redefines,
        "baseTypeNamespaceType": None,
        "valueType": value_type
    }


def create_relationship_type(
    relationship_id: str,
    name: str,
    source_entity_id: str,
    target_entity_id: str
) -> dict:
    """
    Create a RelationshipType definition for Fabric Ontology.
    
    Args:
        relationship_id: Unique 64-bit integer ID for this relationship
        name: Name of the relationship
        source_entity_id: ID of source entity type
        target_entity_id: ID of target entity type
        
    Returns:
        RelationshipType definition dictionary
    """
    return {
        "namespace": "usertypes",
        "id": relationship_id,
        "name": sanitize_fabric_name(name),
        "namespaceType": "Custom",
        "source": {
            "entityTypeId": source_entity_id
        },
        "target": {
            "entityTypeId": target_entity_id
        }
    }


def assemble_fabric_ontology(
    class_ontology_dict: dict,
    prop_ontology_dict: dict,
    url_to_classname_dict: dict,
    array_properties_dict: dict,
    dest_filepath: str,
    ontology_name: str = "OSDU_Ontology",
    write_file: bool = True,
    output_filename: str = None
) -> dict:
    """
    Assemble the complete Fabric Ontology JSON structure from OSDU data structures.
    
    Args:
        class_ontology_dict: Dictionary mapping OSDU class names to ClassRep objects
        prop_ontology_dict: Dictionary mapping OSDU property names to PropertyRep objects
        url_to_classname_dict: Dictionary mapping filename keys to class names
        array_properties_dict: Dictionary of array property restrictions
        dest_filepath: Output file path
        ontology_name: Display name for the ontology
        write_file: Whether to write the output file
        output_filename: Base filename for output (without extension). If None, derived from ontology_name
        
    Returns:
        The complete Fabric Ontology definition dictionary
    """
    # Derive output filename from ontology name if not specified
    if output_filename is None:
        output_filename = sanitize_fabric_name(ontology_name).lower() + "_fabric_ontology"
    
    parts = []
    
    # Create platform metadata
    platform_meta = create_platform_metadata(ontology_name)
    parts.append({
        "path": ".platform",
        "payload": encode_to_base64(platform_meta),
        "payloadType": "InlineBase64"
    })
    
    # Create empty definition.json
    parts.append({
        "path": "definition.json",
        "payload": encode_to_base64({}),
        "payloadType": "InlineBase64"
    })
    
    # Track entity IDs for relationship creation
    entity_id_map = {}  # class_name -> entity_id
    
    # Build properties by domain (class)
    properties_by_class = {}
    for prop_name, prop_rep in prop_ontology_dict.items():
        # Only include datatype properties as entity properties
        # Object properties will become relationships
        if prop_rep.type == PropType.Datatype:
            for domain in prop_rep.domain:
                if domain not in properties_by_class:
                    properties_by_class[domain] = []
                
                # Determine value type from range
                value_type = "String"
                if prop_rep.range:
                    range_val = prop_rep.range[0]
                    if range_val in literals_dict or range_val in FABRIC_TYPE_MAP:
                        value_type = map_to_fabric_type(range_val)
                
                prop_id = generate_entity_id(f"{domain}_{prop_name}")
                properties_by_class[domain].append(
                    create_entity_property(
                        prop_id=prop_id,
                        name=prop_name,
                        value_type=value_type
                    )
                )
    
    # Helper function to get all inherited property names from ancestor chain
    def get_inherited_properties(class_name: str, visited: set = None) -> set:
        if visited is None:
            visited = set()
        if class_name in visited:
            return set()
        visited.add(class_name)
        
        inherited = set()
        class_rep = class_ontology_dict.get(class_name)
        if class_rep:
            for superclass in class_rep.superclass_list:
                if not superclass.startswith("owl:") and superclass in class_ontology_dict:
                    # Add properties from parent
                    parent_props = properties_by_class.get(superclass, [])
                    for p in parent_props:
                        inherited.add(p["name"])
                    # Also add "DisplayName" since root entities get it
                    inherited.add("DisplayName")
                    # Recursively get ancestor properties
                    inherited.update(get_inherited_properties(superclass, visited))
        return inherited
    
    # Create EntityTypes from classes
    for class_name, class_rep in class_ontology_dict.items():
        # Skip owl:Thing and other OWL primitives
        if class_name.startswith("owl:") or class_name.startswith("xsd:"):
            continue
            
        entity_id = generate_entity_id(class_name)
        entity_id_map[class_name] = entity_id
        
        # Get base entity type ID from superclass
        base_entity_type_id = None
        parent_class_name = None
        for superclass in class_rep.superclass_list:
            if not superclass.startswith("owl:") and superclass in class_ontology_dict:
                base_entity_type_id = generate_entity_id(superclass)
                parent_class_name = superclass
                break
        
        # Get properties for this class
        class_properties = properties_by_class.get(class_name, [])
        
        # If has parent, filter out properties that are inherited
        if base_entity_type_id is not None:
            inherited_props = get_inherited_properties(class_name)
            class_properties = [p for p in class_properties if p["name"] not in inherited_props]
        else:
            # Only add DisplayName property to root entities (no parent)
            has_display_name = any(p["name"] == "DisplayName" for p in class_properties)
            if not has_display_name:
                display_prop_id = generate_entity_id(f"{class_name}_DisplayName")
                class_properties.insert(0, create_entity_property(
                    prop_id=display_prop_id,
                    name="DisplayName",
                    value_type="String"
                ))
        
        # Create entity type definition
        entity_type = create_entity_type(
            entity_id=entity_id,
            name=class_name,
            properties=class_properties,
            base_entity_type_id=base_entity_type_id,
            description=class_rep.comments[0] if class_rep.comments else ""
        )
        
        # Add to parts
        parts.append({
            "path": f"EntityTypes/{entity_id}/definition.json",
            "payload": encode_to_base64(entity_type),
            "payloadType": "InlineBase64"
        })
    
    # Create RelationshipTypes from object properties
    for prop_name, prop_rep in prop_ontology_dict.items():
        if prop_rep.type == PropType.Object:
            for domain in prop_rep.domain:
                for range_val in prop_rep.range:
                    # Skip non-class ranges
                    if range_val in literals_dict:
                        continue
                    if range_val.startswith("owl:") or range_val.startswith("xsd:"):
                        continue
                    
                    source_id = entity_id_map.get(domain)
                    target_id = entity_id_map.get(range_val)
                    
                    if source_id and target_id:
                        relationship_id = generate_entity_id(f"{domain}_{prop_name}_{range_val}")
                        
                        # Create unique relationship name including source and target
                        # to avoid duplicate name conflicts
                        rel_name = f"{domain}_{prop_name}_{range_val}"
                        
                        relationship = create_relationship_type(
                            relationship_id=relationship_id,
                            name=rel_name,
                            source_entity_id=source_id,
                            target_entity_id=target_id
                        )
                        
                        parts.append({
                            "path": f"RelationshipTypes/{relationship_id}/definition.json",
                            "payload": encode_to_base64(relationship),
                            "payloadType": "InlineBase64"
                        })
    
    # Assemble final structure
    ontology_definition = {"parts": parts}
    
    if write_file:
        # Write the complete definition
        output_path = os.path.join(dest_filepath, output_filename + ".json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(ontology_definition, f, indent=2)
        
        # Also write a human-readable version with decoded payloads
        readable_parts = []
        for part in parts:
            readable_part = {
                "path": part["path"],
                "payload_decoded": json.loads(
                    base64.b64decode(part["payload"]).decode('utf-8')
                ),
                "payloadType": part["payloadType"]
            }
            readable_parts.append(readable_part)
        
        readable_output = {"parts": readable_parts}
        readable_path = os.path.join(dest_filepath, output_filename + "_readable.json")
        with open(readable_path, 'w', encoding='utf-8') as f:
            json.dump(readable_output, f, indent=2)
        
        print(f"Fabric Ontology written to: {output_path}")
        print(f"Readable version written to: {readable_path}")
    
    return ontology_definition


def generate_fabric_ontology_summary(
    class_ontology_dict: dict,
    prop_ontology_dict: dict
) -> dict:
    """
    Generate a summary of the Fabric Ontology for reporting.
    
    Args:
        class_ontology_dict: Dictionary of class representations
        prop_ontology_dict: Dictionary of property representations
        
    Returns:
        Summary statistics dictionary
    """
    entity_count = sum(
        1 for name in class_ontology_dict.keys()
        if not name.startswith("owl:") and not name.startswith("xsd:")
    )
    
    datatype_prop_count = sum(
        1 for prop in prop_ontology_dict.values()
        if prop.type == PropType.Datatype
    )
    
    relationship_count = sum(
        len(prop.domain) * len([r for r in prop.range if r not in literals_dict])
        for prop in prop_ontology_dict.values()
        if prop.type == PropType.Object
    )
    
    return {
        "entity_types": entity_count,
        "properties": datatype_prop_count,
        "relationship_types": relationship_count
    }
