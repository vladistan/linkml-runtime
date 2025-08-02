import os
from datetime import date

import pytest

from linkml_runtime.dumpers import rdf_dumper, rdflib_dumper
from linkml_runtime.utils.schemaview import SchemaView
from tests.test_loaders_dumpers.models.personinfo_pydantic import EmploymentEvent, Organization, Person


@pytest.fixture(scope="module")
def schema_path():
    """Path to the example personinfo schema."""
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, "input", "example_personinfo.yaml")


@pytest.fixture(scope="module")
def context_path():
    """Path to the example personinfo JSON-LD context."""
    current_dir = os.path.dirname(__file__)
    return os.path.join(current_dir, "input", "example_personinfo.context.jsonld")


@pytest.fixture(scope="module")
def test_person():
    """Create test person with employment history."""
    org_w = Organization(id="WIDG:001", name="Widget Corp", description="A company that makes widgets")
    org_g = Organization(id="GIDG:001", name="Gadget Corp", description="A company that makes gadgets")
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


def test_rdf_dumper(test_person, context_path):
    """Test serialization with rdf_dumper"""
    rdf_str = rdf_dumper.dumps(test_person, contexts=context_path)
    assert isinstance(rdf_str, str)
    assert len(rdf_str) > 0
    assert "Alice Smith" in rdf_str


def test_rdflib_dumper(test_person, schemaview):
    """Test serialization with rdflib_dumper"""
    rdf_str = rdflib_dumper.dumps(test_person, schemaview=schemaview)
    assert isinstance(rdf_str, str)
    assert len(rdf_str) > 0
