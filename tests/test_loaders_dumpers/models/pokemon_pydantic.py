from __future__ import annotations

import re
import sys
from datetime import (
    date,
    datetime,
    time
)
from decimal import Decimal
from enum import Enum
from typing import (
    Any,
    ClassVar,
    Literal,
    Optional,
    Union
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator
)


metamodel_version = "None"
version = "None"


class ConfiguredBaseModel(BaseModel):
    model_config = ConfigDict(
        validate_assignment = True,
        validate_default = True,
        extra = "forbid",
        arbitrary_types_allowed = True,
        use_enum_values = True,
        strict = False,
    )
    pass




class LinkMLMeta(RootModel):
    root: dict[str, Any] = {}
    model_config = ConfigDict(frozen=True)

    def __getattr__(self, key:str):
        return getattr(self.root, key)

    def __getitem__(self, key:str):
        return self.root[key]

    def __setitem__(self, key:str, value):
        self.root[key] = value

    def __contains__(self, key:str) -> bool:
        return key in self.root


linkml_meta = LinkMLMeta({'default_prefix': 'pokemon',
     'default_range': 'string',
     'description': 'Minimal Pokemon schema for testing multilingual RDF support',
     'id': 'https://pokemonkg.org/ontology',
     'imports': ['linkml:types'],
     'license': 'CC0',
     'name': 'pokemon-multilingual-test',
     'prefixes': {'foaf': {'prefix_prefix': 'foaf',
                           'prefix_reference': 'http://xmlns.com/foaf/0.1/'},
                  'instance': {'prefix_prefix': 'instance',
                               'prefix_reference': 'https://pokemonkg.org/instance/'},
                  'linkml': {'prefix_prefix': 'linkml',
                             'prefix_reference': 'https://w3id.org/linkml/'},
                  'pokemon': {'prefix_prefix': 'pokemon',
                              'prefix_reference': 'https://pokemonkg.org/ontology#'},
                  'rdfs': {'prefix_prefix': 'rdfs',
                           'prefix_reference': 'http://www.w3.org/2000/01/rdf-schema#'},
                  'schema': {'prefix_prefix': 'schema',
                             'prefix_reference': 'http://schema.org/'}},
     'source_file': 'tests/test_loaders_dumpers/input/pokemon_schema.yaml'} )


class Species(ConfiguredBaseModel):
    """
    A Pokemon species
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'pokemon:Species',
         'from_schema': 'https://pokemonkg.org/ontology'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'alias': 'id',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': '@id'} })
    name: Optional[str] = Field(default=None, description="""Name (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:label'} })
    genus: Optional[str] = Field(default=None, description="""Pokemon genus/category (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'genus', 'domain_of': ['Species'], 'slot_uri': 'pokemon:hasGenus'} })
    description: Optional[str] = Field(default=None, description="""Description (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'description',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:comment'} })
    catch_rate: Optional[int] = Field(default=None, description="""Base catch rate""", json_schema_extra = { "linkml_meta": {'alias': 'catch_rate',
         'domain_of': ['Species'],
         'slot_uri': 'pokemon:hasCatchRate'} })
    types: Optional[list[PokemonType]] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'types', 'domain_of': ['Species'], 'slot_uri': 'pokemon:hasType'} })
    moves: Optional[list[Move]] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'moves',
         'domain_of': ['Species'],
         'slot_uri': 'pokemon:isAbleToApply'} })
    depictions: Optional[list[str]] = Field(default=None, json_schema_extra = { "linkml_meta": {'alias': 'depictions', 'domain_of': ['Species'], 'slot_uri': 'foaf:depiction'} })


class PokemonType(ConfiguredBaseModel):
    """
    A Pokemon type (e.g., Grass, Ice)
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'pokemon:PokeType',
         'from_schema': 'https://pokemonkg.org/ontology'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'alias': 'id',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': '@id'} })
    name: Optional[str] = Field(default=None, description="""Name (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:label'} })
    description: Optional[str] = Field(default=None, description="""Description (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'description',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:comment'} })


class Ability(ConfiguredBaseModel):
    """
    A Pokemon ability
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'pokemon:Ability',
         'from_schema': 'https://pokemonkg.org/ontology'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'alias': 'id',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': '@id'} })
    name: Optional[str] = Field(default=None, description="""Name (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:label'} })
    description: Optional[str] = Field(default=None, description="""Description (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'description',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:comment'} })


class Move(ConfiguredBaseModel):
    """
    A Pokemon move
    """
    linkml_meta: ClassVar[LinkMLMeta] = LinkMLMeta({'class_uri': 'pokemon:Move', 'from_schema': 'https://pokemonkg.org/ontology'})

    id: str = Field(default=..., json_schema_extra = { "linkml_meta": {'alias': 'id',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': '@id'} })
    name: Optional[str] = Field(default=None, description="""Name (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'name',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:label'} })
    description: Optional[str] = Field(default=None, description="""Description (supports multilingual)""", json_schema_extra = { "linkml_meta": {'alias': 'description',
         'domain_of': ['Species', 'PokemonType', 'Ability', 'Move'],
         'slot_uri': 'rdfs:comment'} })


# Model rebuild
# see https://pydantic-docs.helpmanual.io/usage/models/#rebuilding-a-model
Species.model_rebuild()
PokemonType.model_rebuild()
Ability.model_rebuild()
Move.model_rebuild()
