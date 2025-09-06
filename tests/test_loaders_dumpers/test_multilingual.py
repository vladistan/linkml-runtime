"""
Tests for multilingual support in PydanticRDFLoader.
"""

import pytest
from pydantic_core import ValidationError

from linkml_runtime.loaders.pydantic_rdf_loader import PydanticRDFLoader
from tests.test_loaders_dumpers.environment import env
from tests.test_loaders_dumpers.models.personinfo_pydantic import Person
from tests.test_loaders_dumpers.models.pokemon_pydantic import Species


def test_default_language_selection_without_preference():
    """When no language selected, default is English"""
    loader = PydanticRDFLoader()
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    assert person.name == "John Smith"


def test_single_language_selection():
    """When single language selected, pick name in that language"""
    loader = PydanticRDFLoader(preferred_languages=['uk'])
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    assert person.name == "Джон Сміт"


def test_multiple_languages_selection_preference_order():
    """With multiple languages, select in order of preference"""
    
    loader = PydanticRDFLoader(preferred_languages=['ja', 'zh', 'bg', 'ar'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    assert person.name == "约翰·史密斯"


def test_fallback_to_english_when_none_available():
    """If none of selected languages available, default to English"""
    loader = PydanticRDFLoader(preferred_languages=['ja', 'de', 'ru'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    assert person.name == "John Smith"


def test_non_language_designated_strings_all_selected():
    """For strings without language designators, select all available"""
    loader = PydanticRDFLoader(preferred_languages=['en'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    assert person.aliases is not None
    assert isinstance(person.aliases, list)
    
    # Should contain aliases from all languages since no language tags
    assert "Johnny" in person.aliases     # English
    assert "Juan" in person.aliases       # Spanish  
    assert "Ιωάννης" in person.aliases    # Greek
    assert len(person.aliases) == 17


def test_no_preferred_language_no_english_fallback_alphabetical():
    """For fields without preferred language and no English, select first alphabetically"""
    loader = PydanticRDFLoader(preferred_languages=['ja', 'ko', 'pt'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # For description field: no Japanese, Korean, or Portuguese available
    # No English version in descriptions, so should fall back to first alphabetically
    # First alphabetically should be Spanish (@es)
    assert person.description == "Una persona para probar la funcionalidad multiidioma"

def test_mixed_language_scenarios():
    """Test mixed scenario: different languages available for different fields"""
    # Select languages with mixed availability
    loader = PydanticRDFLoader(preferred_languages=['hi', 'uk', 'es'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # Name: Hindi not available, Ukrainian available -> should get Ukrainian
    assert person.name == "Джон Сміт"
    
    # Description: Hindi available -> should get Hindi (first preference)
    assert person.description == "बहुभाषी कार्यक्षमता का परीक्षण करने के लिए एक व्यक्ति"
    
    # Aliases: No language tags, should get all
    assert len(person.aliases) == 17


@pytest.mark.parametrize("languages,expected_name,expected_description", [
    # Test various language combinations and expected results
    (['en'], "John Smith", "Una persona para probar la funcionalidad multiidioma"),  # English name, no English desc -> alphabetical
    (['ar'], "جون سميث", "Una persona para probar la funcionalidad multiidioma"),       # Arabic name, no Arabic desc -> alphabetical  
    (['zh'], "约翰·史密斯", "用于测试多语言功能的人"),                                   # Chinese name, Chinese desc
    (['uk'], "Джон Сміт", "Людина для тестування багатомовної функціональності"),      # Ukrainian name, Ukrainian desc
    (['fr'], "John Smith", "Une personne pour tester la fonctionnalité multilingue"), # No French name -> English, French desc
    (['es'], "John Smith", "Una persona para probar la funcionalidad multiidioma"),   # No Spanish name -> English, Spanish desc
])
def test_language_selection_parametrized(languages, expected_name, expected_description):
    """Parametrized test for various language selection scenarios"""
    loader = PydanticRDFLoader(preferred_languages=languages)
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    assert person.name == expected_name
    assert person.description == expected_description
    # Aliases should always be full list (no language tags)
    assert len(person.aliases) == 17

def test_multiple_names_without_language_tags_should_fail():
    """Test that multiple names without language tags cause validation failure"""
    loader = PydanticRDFLoader(preferred_languages=['en'])
    
    # This RDF has multiple schema:name values without language tags
    # Since name is single-valued, this should cause validation failure
    with pytest.raises((ValidationError, ValueError)) as exc_info:
        person = loader.load(env.input_path("invalid_multiple_values.ttl"), Person)
    
    # The error should be related to single-valued fields having multiple values
    error_str = str(exc_info.value)
    assert "cannot have multiple values without language tags" in error_str.lower()
