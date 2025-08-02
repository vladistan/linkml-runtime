import os
from datetime import date

import pytest

from linkml_runtime.dumpers import rdf_dumper, rdflib_dumper
from linkml_runtime.utils.schemaview import SchemaView
from tests.test_loaders_dumpers.models.personinfo_pydantic import EmploymentEvent, Organization, Person
from pathlib import Path


@pytest.fixture(scope="module")
def schema_path():
    """Path to the example personinfo schema."""
    current_dir = Path(__file__).parent
    return current_dir / "input" / "example_personinfo.yaml"


@pytest.fixture(scope="module")
def test_person():
    """Create test person with employment history."""
    org_w = Organization(id="WIDG:001", name="Widget Corp", description="A company that makes widgets")
    org_g = Organization(id="ROR:002", name="Gadget Corp", description="A company that makes gadgets")
    employment = [
        EmploymentEvent(
            employed_at=org_w.id,
            started_at_time=date(2020, 1, 1),
            ended_at_time=date(2021, 1, 1),
        ),
        EmploymentEvent(
            employed_at=org_g.id,
            started_at_time=date(2021, 2, 1),
            is_current=True,
            ended_at_time=None,
        ),
    ]
    return Person(id="P:001", name="Alice Smith", has_employment_history=employment)


@pytest.fixture(scope="module")
def schemaview(schema_path):
    """SchemaView instance for the personinfo schema."""
    return SchemaView(schema_path)



def test_rdflib_dumper(test_person, schemaview):
    """Test serialization with rdflib_dumper"""
    rdf_str = rdflib_dumper.dumps(
        test_person, 
        schemaview=schemaview,
        prefix_map={ 
            "WIDG": "http://example.org/widget/", 
            "GADG": "http://example.org/gadget/" })
    assert isinstance(rdf_str, str)
    assert len(rdf_str) > 0
    
    # Verify the RDF contains expected content
    assert "Alice Smith" in rdf_str
    # Should use schema.org Person class (may be schema: or schema1: depending on namespace conflicts)
    assert ("schema:Person" in rdf_str or "schema1:Person" in rdf_str)
    assert "P:001" in rdf_str  # Person ID
    # Verify it's using the proper personinfo namespace for properties
    assert "personinfo:has_employment_history" in rdf_str
    assert "personinfo:EmploymentEvent" in rdf_str

