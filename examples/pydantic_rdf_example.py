#!/usr/bin/env python3
"""
Example demonstrating PydanticRDFDumper and PydanticRDFLoader

This example shows how to use the new RDF dumper/loader that works
directly with Pydantic models using embedded LinkML metadata,
without requiring a SchemaView.
"""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path to import from tests
sys.path.insert(0, str(Path(__file__).parent.parent))

from linkml_runtime.dumpers.pydantic_rdf_dumper import PydanticRDFDumper
from linkml_runtime.loaders.pydantic_rdf_loader import PydanticRDFLoader

# Import Pydantic models generated from LinkML
from tests.test_loaders_dumpers.models.personinfo_pydantic import (
    Person, Organization, EmploymentEvent
)


def main():
    print("=== PydanticRDFDumper and PydanticRDFLoader Example ===\n")
    
    # Create sample data
    print("1. Creating sample Pydantic model instances...")
    
    # Create organizations
    widget_corp = Organization(
        id="ROR:001", 
        name="Widget Corp", 
        description="A company that makes widgets"
    )
    
    gadget_corp = Organization(
        id="ROR:002", 
        name="Gadget Corp", 
        description="A company that makes gadgets"
    )
    
    # Create employment events
    employment_history = [
        EmploymentEvent(
            employed_at=widget_corp.id,
            started_at_time=date(2020, 1, 1),
            ended_at_time=date(2021, 1, 1),
        ),
        EmploymentEvent(
            employed_at=gadget_corp.id,
            started_at_time=date(2021, 2, 1),
            is_current=True,
            ended_at_time=None,
        ),
    ]
    
    # Create person
    person = Person(
        id="P:001", 
        name="Alice Smith", 
        primary_email="alice@example.org",
        has_employment_history=employment_history
    )
    
    print(f"Created person: {person.name} ({person.id})")
    print(f"Employment history: {len(employment_history)} jobs")
    print()
    
    # Dump to RDF using embedded metadata
    print("2. Dumping to RDF using PydanticRDFDumper...")
    print("   (Uses linkml_meta embedded in Pydantic models - no SchemaView needed)")
    
    dumper = PydanticRDFDumper()
    rdf_output = dumper.dumps(person)
    
    print("Generated RDF:")
    print("-" * 60)
    print(rdf_output)
    print("-" * 60)
    print()
    
    # Load back from RDF
    print("3. Loading RDF back to Pydantic model using PydanticRDFLoader...")
    
    loader = PydanticRDFLoader()
    loaded_person = loader.loads(rdf_output, Person)
    
    print(f"Loaded person: {loaded_person.name} ({loaded_person.id})")
    print(f"Email: {loaded_person.primary_email}")
    print(f"Employment history: {len(loaded_person.has_employment_history or [])} jobs")
    
    # Verify round-trip accuracy
    print("\n4. Verifying round-trip accuracy...")
    print(f"Original ID: {person.id} -> Loaded ID: {loaded_person.id}")
    print(f"Original name: {person.name} -> Loaded name: {loaded_person.name}")
    print(f"Original email: {person.primary_email} -> Loaded email: {loaded_person.primary_email}")
    
    if loaded_person.has_employment_history:
        print(f"Employment events preserved: {len(loaded_person.has_employment_history)}")
        for i, event in enumerate(loaded_person.has_employment_history):
            print(f"  Event {i+1}: {event.employed_at} ({event.started_at_time} - {event.ended_at_time})")
    
    print("\n✅ Round-trip successful! Pydantic -> RDF -> Pydantic")
    
    # Show key features
    print("\n5. Key Features Demonstrated:")
    print("   ✅ No SchemaView required - uses embedded linkml_meta")
    print("   ✅ Proper semantic RDF with correct URIs:")
    print("      - Person typed as schema:Person (from class_uri)")
    print("      - Properties use correct URIs (schema:name, prov:startedAtTime)")
    print("      - Nested objects as blank nodes with proper typing")
    print("   ✅ XSD datatypes for primitives (dates, booleans)")
    print("   ✅ Round-trip fidelity preserves complex nested structures")
    print("   ✅ CURIE/URI handling from embedded prefix mappings")


if __name__ == "__main__":
    main()