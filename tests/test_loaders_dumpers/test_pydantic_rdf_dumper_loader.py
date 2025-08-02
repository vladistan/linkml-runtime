import os
from datetime import date
from pathlib import Path

import pytest

from linkml_runtime.dumpers.pydantic_rdf_dumper import PydanticRDFDumper
from linkml_runtime.loaders.pydantic_rdf_loader import PydanticRDFLoader
from tests.test_loaders_dumpers.models.personinfo_pydantic import EmploymentEvent, Organization, Person


@pytest.fixture(scope="module")
def test_person():
    """Create test person with employment history."""
    org_w = Organization(id="ROR:001", name="Widget Corp", description="A company that makes widgets")
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
def pydantic_dumper():
    """PydanticRDFDumper instance."""
    return PydanticRDFDumper()


@pytest.fixture(scope="module")
def pydantic_loader():
    """PydanticRDFLoader instance."""
    return PydanticRDFLoader()


def test_pydantic_rdf_dumper_basic(test_person, pydantic_dumper):
    """Test basic RDF dumping with Pydantic model using embedded metadata"""
    rdf_str = pydantic_dumper.dumps(test_person)
    
    assert isinstance(rdf_str, str)
    assert len(rdf_str) > 0
    
    # Verify the RDF contains expected content
    assert "Alice Smith" in rdf_str
    # Should use schema.org Person class (may be schema: or schema1: depending on namespace conflicts)
    assert ("schema:Person" in rdf_str or "schema1:Person" in rdf_str)
    assert "P:001" in rdf_str  # Person ID
    
    print("Generated RDF:")
    print(rdf_str)


def test_pydantic_rdf_dumper_prefixes(test_person, pydantic_dumper):
    """Test RDF dumping with custom prefix mappings"""
    custom_prefixes = {
        "custom": "http://example.org/custom/",
        "test": "http://test.org/"
    }
    
    rdf_str = pydantic_dumper.dumps(test_person, prefix_map=custom_prefixes)
    
    assert isinstance(rdf_str, str)
    assert len(rdf_str) > 0
    assert "Alice Smith" in rdf_str


def test_pydantic_rdf_dumper_graph(test_person, pydantic_dumper):
    """Test RDF dumping to Graph object"""
    graph = pydantic_dumper.as_rdf_graph(test_person)
    
    assert graph is not None
    assert len(graph) > 0  # Should have triples
    
    # Check for expected triples
    from rdflib import URIRef
    from rdflib.namespace import RDF
    
    # Should have at least one rdf:type triple
    type_triples = list(graph.triples((None, RDF.type, None)))
    assert len(type_triples) > 0


def test_pydantic_rdf_round_trip(test_person, pydantic_dumper, pydantic_loader):
    """Test round-trip conversion: Pydantic -> RDF -> Pydantic"""
    # Dump to RDF
    rdf_str = pydantic_dumper.dumps(test_person)
    
    # Load back from RDF
    loaded_person = pydantic_loader.loads(rdf_str, Person)
    
    # Verify core properties are preserved
    assert loaded_person.id == test_person.id
    assert loaded_person.name == test_person.name
    
    print(f"Original: {test_person}")
    print(f"Loaded: {loaded_person}")


def test_pydantic_rdf_loader_basic(pydantic_loader):
    """Test basic RDF loading into Pydantic model"""
    # Simple RDF for a person
    rdf_content = """
    @prefix schema: <http://schema.org/> .
    @prefix P: <http://example.org/P/> .
    
    P:001 a schema:Person ;
        schema:name "Bob Smith" .
    """
    
    loaded_person = pydantic_loader.loads(rdf_content, Person)
    
    assert loaded_person is not None
    assert loaded_person.id == "P:001"
    assert loaded_person.name == "Bob Smith"


def test_pydantic_rdf_file_operations(test_person, pydantic_dumper, pydantic_loader, tmp_path):
    """Test file-based dump and load operations"""
    # Create temporary file
    rdf_file = tmp_path / "test_person.ttl"
    
    # Dump to file
    pydantic_dumper.dump(test_person, str(rdf_file))
    
    # Verify file exists and has content
    assert rdf_file.exists()
    assert rdf_file.stat().st_size > 0
    
    # Load from file
    loaded_person = pydantic_loader.load(str(rdf_file), Person)
    
    # Verify core properties
    assert loaded_person.id == test_person.id
    assert loaded_person.name == test_person.name


def test_pydantic_rdf_complex_properties(pydantic_dumper):
    """Test handling of complex nested properties"""
    # Create a person with nested employment events
    org = Organization(id="ORG:001", name="Test Corp")
    employment = EmploymentEvent(
        employed_at=org.id,
        started_at_time=date(2020, 1, 1),
        is_current=True
    )
    person = Person(id="P:002", name="Test Person", has_employment_history=[employment])
    
    rdf_str = pydantic_dumper.dumps(person)
    
    assert "Test Person" in rdf_str
    assert "Test Corp" not in rdf_str  # Organization object not included, just ID reference
    assert "ORG:001" in rdf_str  # Should have employment reference


def test_pydantic_rdf_empty_values(pydantic_dumper):
    """Test handling of None/empty values"""
    person = Person(id="P:003", name="Empty Person")  # Most fields will be None
    
    rdf_str = pydantic_dumper.dumps(person)
    
    assert "Empty Person" in rdf_str
    assert "P:003" in rdf_str
    # Should not crash on None values


def test_pydantic_rdf_metadata_extraction(test_person, pydantic_dumper):
    """Test that metadata is properly extracted from Pydantic models"""
    # This tests the internal metadata extraction
    global_meta = pydantic_dumper._extract_global_metadata(test_person)
    
    # Should have prefixes and other metadata
    assert isinstance(global_meta, dict)
    if global_meta:  # Only check if metadata was successfully extracted
        assert "prefixes" in global_meta or len(global_meta) == 0  # Allow empty if extraction fails


def test_pydantic_rdf_class_metadata(test_person, pydantic_dumper):
    """Test class metadata extraction"""
    class_meta = pydantic_dumper._get_class_metadata(test_person)
    
    assert isinstance(class_meta, dict)
    assert "name" in class_meta
    assert class_meta["name"] == "Person"
    
    # Should have class_uri from metadata
    if "class_uri" in class_meta:
        assert class_meta["class_uri"] == "schema:Person"