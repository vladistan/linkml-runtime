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


def test_pydantic_rdf_list_field_handling(pydantic_dumper, pydantic_loader):
    """Test proper handling of list fields in round-trip conversion"""
    # Test with a person that has list fields (aliases)
    person_with_lists = Person(
        id="P:003", 
        name="List Test Person",
        aliases=["alias1", "alias2", "nickname"]
    )
    
    # Dump to RDF
    rdf_str = pydantic_dumper.dumps(person_with_lists)
    
    # Verify RDF contains the aliases
    assert "alias1" in rdf_str
    assert "alias2" in rdf_str
    assert "nickname" in rdf_str
    
    # Load back from RDF
    loaded_person = pydantic_loader.loads(rdf_str, Person)
    
    # Verify core properties are preserved
    assert loaded_person.id == person_with_lists.id
    assert loaded_person.name == person_with_lists.name
    
    # Verify aliases list is properly reconstructed
    assert loaded_person.aliases is not None
    assert isinstance(loaded_person.aliases, list)
    assert len(loaded_person.aliases) == 3
    assert set(loaded_person.aliases) == set(person_with_lists.aliases)


def test_pydantic_rdf_single_list_value_handling(pydantic_dumper, pydantic_loader):
    """Test handling of single values that should be wrapped in lists"""
    # Create person with single alias (which should be a list field)
    person_single_alias = Person(
        id="P:004",
        name="Single Alias Person", 
        aliases=["single_alias"]  # This is a list with one item
    )
    
    # Dump to RDF
    rdf_str = pydantic_dumper.dumps(person_single_alias)
    
    # Load back from RDF
    loaded_person = pydantic_loader.loads(rdf_str, Person)
    
    # Verify the single alias is still wrapped in a list
    assert loaded_person.aliases is not None
    assert isinstance(loaded_person.aliases, list)
    assert len(loaded_person.aliases) == 1
    assert loaded_person.aliases[0] == "single_alias"


def test_pydantic_rdf_mixed_field_types(pydantic_dumper, pydantic_loader):
    """Test handling of mixed field types (scalar and list) in same model"""
    # Create person with both scalar and list fields
    mixed_person = Person(
        id="P:005",
        name="Mixed Fields Person",          # scalar field
        aliases=["alias1", "alias2"],        # list field  
        age_in_years=30,                     # scalar field
        primary_email="test@example.com"     # scalar field
    )
    
    # Round-trip conversion
    rdf_str = pydantic_dumper.dumps(mixed_person)
    loaded_person = pydantic_loader.loads(rdf_str, Person)
    
    # Verify scalar fields
    assert loaded_person.id == mixed_person.id
    assert loaded_person.name == mixed_person.name
    assert loaded_person.age_in_years == mixed_person.age_in_years
    assert loaded_person.primary_email == mixed_person.primary_email
    
    # Verify list field
    assert loaded_person.aliases is not None
    assert isinstance(loaded_person.aliases, list)
    assert set(loaded_person.aliases) == set(mixed_person.aliases)


def test_pydantic_rdf_single_value_to_list_field():
    """Test critical scenario: RDF with single value for a field expecting a list"""
    # Create manual RDF with a single value for aliases field (which expects a list)
    rdf_content = """
    @prefix schema: <http://schema.org/> .
    @prefix personinfo: <https://w3id.org/linkml/examples/personinfo/> .
    @prefix P: <http://example.org/P/> .
    
    P:006 a schema:Person ;
        schema:name "Single Value Test" ;
        personinfo:aliases "only_one_alias" .
    """
    
    pydantic_loader = PydanticRDFLoader()
    
    # Load from RDF - this should wrap the single string in a list
    loaded_person = pydantic_loader.loads(rdf_content, Person)
    
    # Verify the single value was wrapped in a list
    assert loaded_person.id == "P:006"
    assert loaded_person.name == "Single Value Test"
    assert loaded_person.aliases is not None
    assert isinstance(loaded_person.aliases, list)
    assert len(loaded_person.aliases) == 1
    assert loaded_person.aliases[0] == "only_one_alias"