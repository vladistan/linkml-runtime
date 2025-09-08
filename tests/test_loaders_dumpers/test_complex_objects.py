"""
Test complex object loading in PydanticRDFLoader.

These tests verify that the loader can load complete objects from RDF documents
rather than just URI string references.
"""

import pytest
from pydantic_core import ValidationError

from linkml_runtime.loaders.pydantic_rdf_loader import PydanticRDFLoader
from tests.test_loaders_dumpers.environment import env
from tests.test_loaders_dumpers.models.pokemon_pydantic import Species, PokemonType


def test_pokemon_loads_complete_type_objects():
    """Test that Pokemon loads with complete PokemonType objects, not URI strings"""
    loader = PydanticRDFLoader()
    
    pokemon = loader.load(env.input_path("pokemon_abomasnow.ttl"), Species)
    
    # Basic Pokemon properties should load correctly
    assert pokemon.name == "Abomasnow"  # English default
    assert pokemon.genus == "Frost Tree Pokémon"
    assert pokemon.catch_rate == 60
    
    # Types field should contain complete PokemonType objects, not strings
    assert pokemon.types is not None
    assert isinstance(pokemon.types, list)
    assert len(pokemon.types) == 2
    
    # Each type should be a complete PokemonType object
    for ptype in pokemon.types:
        assert isinstance(ptype, PokemonType), f"Expected PokemonType object, got {type(ptype)}"
        assert ptype.id is not None
        assert ptype.name is not None
    
    # Find the specific types
    type_names = [t.name for t in pokemon.types]
    assert "Grass" in type_names
    assert "Ice" in type_names
    
    # Verify complete object properties
    grass_type = next(t for t in pokemon.types if "Grass" in t.name)
    assert grass_type.id == "pokemon:PokéType_Grass"  # CURIE format
    assert grass_type.name == "Grass"  # English default
    assert grass_type.description is not None
    assert "basic elemental types" in grass_type.description

def test_type_objects_respect_language_preferences():
    """Test that Type objects loaded with language preferences"""
    # Load with German preference
    loader = PydanticRDFLoader(preferred_languages=['de'])
    
    pokemon = loader.load(env.input_path("pokemon_abomasnow.ttl"), Species)
    
    # Pokemon should get German name
    assert pokemon.name == "Rexblisar"
    
    # Type objects should also respect German preference
    grass_type = next(t for t in pokemon.types if "Grass" in t.name or "Pflanze" in t.name)
    assert grass_type.name == "Pflanze"  # German label for Grass
    assert "Gras ist einer der drei" in grass_type.description  # German description

@pytest.mark.parametrize("languages,expected_pokemon_name,expected_grass_name,expected_ice_name", [
    (['en'], "Abomasnow", "Grass", "Ice"),
    (['de'], "Rexblisar", "Pflanze", "Eis"),
    (['ja'], "ユキノオー", "Grass", "Ice"),  # No Japanese type names, should fallback
])
def test_complex_objects_with_multilingual_integration(languages, expected_pokemon_name, expected_grass_name, expected_ice_name):
    """Test complex objects work alongside multilingual functionality"""
    loader = PydanticRDFLoader(preferred_languages=languages)
    pokemon = loader.load(env.input_path("pokemon_abomasnow.ttl"), Species)
    
    assert pokemon.name == expected_pokemon_name
    
    # Find types by ID since names might vary by language
    grass_type = next(t for t in pokemon.types if "Grass" in t.id)
    ice_type = next(t for t in pokemon.types if "Ice" in t.id)
    
    assert grass_type.name == expected_grass_name
    assert ice_type.name == expected_ice_name

def test_missing_referenced_object_should_fail():
    """Test that missing referenced objects cause appropriate failures"""
    loader = PydanticRDFLoader()
    
    # Test file with references to non-existent types should throw exception
    with pytest.raises((ValueError, ValidationError)) as exc_info:
        pokemon = loader.load(env.input_path("pokemon_missing_types.ttl"), Species)
    
    # Should mention the validation issue with non-existent types
    error_str = str(exc_info.value)
    assert "NonExistent" in error_str or "AlsoMissing" in error_str


    """Test that complex object loading is compatible with round-trip operations"""
    from linkml_runtime.dumpers.pydantic_rdf_dumper import PydanticRDFDumper
    
    # Load Pokemon with complex objects
    loader = PydanticRDFLoader()
    original_pokemon = loader.load(env.input_path("pokemon_abomasnow.ttl"), Species)
    
    # Dump back to RDF
    dumper = PydanticRDFDumper()
    rdf_str = dumper.dumps(original_pokemon)
    
    # Load again from dumped RDF
    reloaded_pokemon = loader.loads(rdf_str, Species)
    
    # Should have same structure
    assert len(reloaded_pokemon.types) == len(original_pokemon.types)
    assert reloaded_pokemon.name == original_pokemon.name