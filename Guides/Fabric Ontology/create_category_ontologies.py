"""
Generate separate Fabric Ontologies by OSDU category.

This script creates separate ontology files for:
- MasterData entities
- ReferenceData entities  
- WorkProductComponent entities
- Dataset entities
- Abstract/System entities

Usage:
    python create_category_ontologies.py -s schemas/
"""

import argparse
import os
import sys
import json
import base64

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.json_utils import load_schemas
from src.fabric_utils import (
    assemble_fabric_ontology, 
    set_id_seed,
    create_platform_metadata,
    encode_to_base64
)
from src.kg_rep import add_class_from_parameters, add_property_from_parameters, PropType
from src.str_utils import process_name, lower_process_name, extract_classname_from_kind
import regex as re


def categorize_schemas(schema_dict: dict) -> dict:
    """Categorize schemas by OSDU type."""
    categories = {
        "MasterData": {},
        "ReferenceData": {},
        "WorkProductComponent": {},
        "Dataset": {},
        "Abstract": {}
    }
    
    for key, schema in schema_dict.items():
        if "/manifest/" in key:
            continue
        elif "/reference-data/" in key:
            categories["ReferenceData"][key] = schema
        elif "/work-product-component/" in key:
            categories["WorkProductComponent"][key] = schema
        elif "/master-data/" in key:
            categories["MasterData"][key] = schema
        elif "/dataset/" in key:
            categories["Dataset"][key] = schema
        else:
            categories["Abstract"][key] = schema
    
    return categories


def main():
    parser = argparse.ArgumentParser(
        description="Generate separate Fabric Ontologies by OSDU category"
    )
    parser.add_argument(
        "-s", "--src",
        required=True,
        help="Source location for schema files"
    )
    parser.add_argument(
        "-d", "--dest",
        default="./",
        help="Destination directory for output files"
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["MasterData", "ReferenceData", "WorkProductComponent", "Dataset", "Abstract", "all"],
        default=["all"],
        help="Which categories to generate"
    )
    
    args = parser.parse_args()
    
    print("Loading schemas...")
    schema_dict = load_schemas(args.src)
    print(f"Loaded {len(schema_dict)} schemas")
    
    print("\nCategorizing schemas...")
    categories = categorize_schemas(schema_dict)
    
    for cat, schemas in categories.items():
        print(f"  {cat}: {len(schemas)} schemas")
    
    # Determine which categories to process
    if "all" in args.categories:
        to_process = list(categories.keys())
    else:
        to_process = args.categories
    
    print(f"\nGenerating ontologies for: {', '.join(to_process)}")
    
    for i, category in enumerate(to_process):
        if not categories[category]:
            print(f"\nSkipping {category} (no schemas)")
            continue
            
        print(f"\n{'='*60}")
        print(f"Processing {category} ({len(categories[category])} schemas)")
        print(f"{'='*60}")
        
        # Use different seed for each category to avoid ID conflicts
        seed = (i + 1) * 1000
        set_id_seed(seed)
        
        # Build ontology for this category
        from src.kg_rep import add_class_from_parameters, add_property_from_parameters
        
        CLASS_DICT = {}
        PROP_DICT = {}
        URL_TO_CLASS = {}
        ARRAY_PROPS = {}
        
        # Process schemas in this category
        for key, schema in categories[category].items():
            process_schema_for_category(key, schema, CLASS_DICT, PROP_DICT, URL_TO_CLASS, category)
        
        # Generate the ontology file
        output_name = f"osdu_fabric_{category.lower()}"
        
        from src.fabric_utils import assemble_fabric_ontology
        
        assemble_fabric_ontology(
            CLASS_DICT,
            PROP_DICT,
            URL_TO_CLASS,
            ARRAY_PROPS,
            dest_filepath=args.dest,
            ontology_name=f"OSDU_{category}",
            write_file=True,
            output_filename=output_name
        )
        
        print(f"Created: {output_name}.json")
        print(f"  Entity Types: {len(CLASS_DICT)}")
    
    print(f"\n{'='*60}")
    print("COMPLETE")
    print(f"{'='*60}")


def process_schema_for_category(key, schema, class_dict, prop_dict, url_to_class, category):
    """Process a single schema into class and property dictionaries."""
    from src.kg_rep import add_class_from_parameters, add_property_from_parameters, PropType
    from src.str_utils import process_name
    
    # Extract class name
    class_name = re.search(r"([A-Za-z]+)\.\d\.\d\.\d\.json", key)
    if class_name:
        class_name = class_name.groups()[0]
    else:
        class_name = key.split("/")[-1].replace(".json", "")
    
    class_name = process_name(class_name)
    url_to_class[key] = class_name
    
    title = schema.get("title", class_name)
    comments = [schema.get("description", "")] if schema.get("description") else []
    
    # Add class
    class_dict = add_class_from_parameters(
        class_name=class_name,
        superclass_list=[category],
        ontology_dict=class_dict,
        comments=comments,
        pref_label=title
    )
    
    # Process properties
    if "properties" in schema and "data" in schema["properties"]:
        if "allOf" in schema["properties"]["data"]:
            for prop_item in schema["properties"]["data"]["allOf"]:
                if "properties" in prop_item:
                    for prop_name, prop_def in prop_item["properties"].items():
                        add_property_simple(prop_name, prop_def, class_name, prop_dict)
    elif "properties" in schema:
        for prop_name, prop_def in schema["properties"].items():
            add_property_simple(prop_name, prop_def, class_name, prop_dict)


def add_property_simple(prop_name, prop_def, class_name, prop_dict):
    """Add a simple property to the dictionary."""
    from src.kg_rep import add_property_from_parameters, PropType
    from src.str_utils import lower_process_name
    
    range_type = "string"
    if "type" in prop_def:
        range_type = prop_def["type"]
        if range_type == "array" and "items" in prop_def:
            range_type = prop_def["items"].get("type", "string")
    
    prop_dict = add_property_from_parameters(
        property_name=lower_process_name(prop_name),
        domain_name=class_name,
        range_name=range_type,
        ontology_dict=prop_dict,
        property_type=PropType.Datatype,
        comment=prop_def.get("description", "")
    )


if __name__ == "__main__":
    main()
