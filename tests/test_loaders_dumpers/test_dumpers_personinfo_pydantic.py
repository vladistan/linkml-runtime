import os
from datetime import date

import pytest

from linkml_runtime.dumpers import rdf_dumper, rdflib_dumper
from linkml_runtime.dumpers.pydantic_rdf_dumper import PydanticRDFDumper
from linkml_runtime.loaders.pydantic_rdf_loader import PydanticRDFLoader
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


@pytest.fixture(scope="module")
def pydantic_rdf_dumper():
    """PydanticRDFDumper instance."""
    return PydanticRDFDumper()


@pytest.fixture(scope="module")
def pydantic_rdf_loader():
    """PydanticRDFLoader instance."""
    return PydanticRDFLoader()



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


def test_pydantic_rdf_dumper_loader(test_person, pydantic_rdf_dumper, pydantic_rdf_loader):
    """Test PydanticRDFDumper and PydanticRDFLoader with personinfo Pydantic models"""
    # Dump using PydanticRDFDumper (no SchemaView required)
    rdf_str = pydantic_rdf_dumper.dumps(test_person)
    
    assert isinstance(rdf_str, str)
    assert len(rdf_str) > 0
    
    # Verify the RDF contains expected content
    assert "Alice Smith" in rdf_str
    # Should use schema.org Person class (may be schema: or schema1: depending on namespace conflicts)
    assert ("schema:Person" in rdf_str or "schema1:Person" in rdf_str)
    assert "P:001" in rdf_str  # Person ID
    
    # Verify proper semantic RDF structure
    assert "personinfo:has_employment_history" in rdf_str
    assert ("personinfo:EmploymentEvent" in rdf_str or "EmploymentEvent" in rdf_str)
    
    # Verify XSD datatypes for dates
    assert "xsd:date" in rdf_str or "2020-01-01" in rdf_str
    assert "2021-02-01" in rdf_str
    
    # Load back using PydanticRDFLoader
    loaded_person = pydantic_rdf_loader.loads(rdf_str, Person)
    
    # Verify core properties are preserved
    assert loaded_person.id == test_person.id
    assert loaded_person.name == test_person.name
    
    # Verify employment history is preserved (order may differ in RDF)
    assert loaded_person.has_employment_history is not None
    assert len(loaded_person.has_employment_history) == len(test_person.has_employment_history)
    
    # Verify employment details are preserved
    original_employers = {emp.employed_at for emp in test_person.has_employment_history}
    loaded_employers = {emp.employed_at for emp in loaded_person.has_employment_history}
    assert original_employers == loaded_employers
    
    # Verify dates are preserved
    original_start_dates = {emp.started_at_time for emp in test_person.has_employment_history}
    loaded_start_dates = {emp.started_at_time for emp in loaded_person.has_employment_history}
    assert original_start_dates == loaded_start_dates

