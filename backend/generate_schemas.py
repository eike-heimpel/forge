#!/usr/bin/env python3
"""
Dynamically discover and generate JSON schemas from Pydantic models and Enums
to the schemas directory. This ensures the schemas directory is the published 
contract from the backend without manual registration of models.
"""

import json
import inspect
import re
from pathlib import Path
from enum import Enum
from pydantic import BaseModel

# --- Configuration ---
# Point this to the module where your Pydantic/Enum models are defined.
# This is the ONLY part you might ever need to change.
from app.models import schemas as models_module


def convert_camel_to_kebab(name):
    """Converts a CamelCase name to kebab-case for the filename."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', name).lower()


def generate_schemas():
    """Dynamically find and generate JSON schemas from a given module."""
    
    # --- Setup Paths ---
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    schemas_dir = project_root / "schemas" / "json"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Scanning module '{models_module.__name__}' for models...")
    
    all_generated_files = []

    # --- Introspection Magic ---
    # `inspect.getmembers` returns all members (classes, functions, etc.) of a module.
    for name, obj in inspect.getmembers(models_module, inspect.isclass):
        # We process the object if it's a Pydantic model OR an Enum.
        is_pydantic_model = issubclass(obj, BaseModel)
        is_enum = issubclass(obj, Enum) and not issubclass(obj, BaseModel)  # Exclude Pydantic enums

        # CRITICAL CHECK: Ensure the class was defined in our target module,
        # not imported from somewhere else (like Pydantic's own BaseModel).
        if (is_pydantic_model or is_enum) and obj.__module__ == models_module.__name__:
            
            filename = f"{convert_camel_to_kebab(name)}.json"
            schema_path = schemas_dir / filename
            schema = {}

            try:
                if is_pydantic_model:
                    # Use Pydantic's built-in schema generator
                    schema = obj.model_json_schema()
                    print(f"  - Found Pydantic Model: {name} -> {filename}")

                elif is_enum:
                    # Use a custom generator for pure Enums
                    schema = {
                        "title": name,
                        "type": "string",
                        "enum": [item.value for item in obj],
                        "description": f"Enumeration of {name} values"
                    }
                    print(f"  - Found Enum: {name} -> {filename}")
                
                # Add common metadata to all schemas
                schema["$schema"] = "http://json-schema.org/draft-07/schema#"
                schema["generated_from"] = "forge-ai-backend (automated)"
                schema["version"] = "1.0.0"

                with open(schema_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, indent=2, ensure_ascii=False)
                
                all_generated_files.append(filename)

            except Exception as e:
                print(f"  - ERROR generating schema for {name}: {e}")

    # --- Generate Manifest ---
    manifest = {
        "title": "Forge AI Backend Schemas (Auto-Generated)",
        "description": "JSON schemas dynamically discovered from Pydantic models in the backend.",
        "version": "1.0.0",
        "generated_at": "auto",
        "schemas": sorted(all_generated_files)
    }
    manifest_path = schemas_dir / "_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n✅ Generation complete. Generated {len(all_generated_files)} schemas in {schemas_dir}")
    print(f"   Manifest created: {manifest_path.name}")


if __name__ == "__main__":
    generate_schemas() 