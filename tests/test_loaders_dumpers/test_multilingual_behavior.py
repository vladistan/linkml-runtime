"""
Test desired multilingual behavior in PydanticRDFLoader.

Tests the specific language selection logic and fallback behavior
for multilingual RDF data loading.
"""

import pytest

from linkml_runtime.loaders.pydantic_rdf_loader import PydanticRDFLoader
from tests.test_loaders_dumpers.environment import env
from tests.test_loaders_dumpers.models.personinfo_pydantic import Person


def test_default_language_selection_without_preference():
    """Test 1: When no language selected, default is English"""
    # Create loader without specifying preferred languages (should default to ['en'])
    loader = PydanticRDFLoader()
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # Should get English name when no preference specified
    assert person.name == "John Smith"


def test_single_language_selection_ukrainian():
    """Test 2: When single language selected, pick name in that language"""
    # Select Ukrainian specifically
    loader = PydanticRDFLoader(preferred_languages=['uk'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # Should get Ukrainian name
    assert person.name == "Джон Сміт"


def test_multiple_languages_selection_preference_order():
    """Test 3: With multiple languages, select in order of preference"""
    # Select Japanese, Chinese, Bulgarian, Arabic - should get Chinese (first available)
    loader = PydanticRDFLoader(preferred_languages=['ja', 'zh', 'bg', 'ar'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # Should get Chinese name (first available in preference order)
    # Japanese not available, Chinese is available, so should get Chinese
    assert person.name == "约翰·史密斯"


def test_fallback_to_english_when_none_available():
    """Test 4: If none of selected languages available, default to English"""
    # Select languages that don't exist in the data
    loader = PydanticRDFLoader(preferred_languages=['ja', 'de', 'ru'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # Should fall back to English when preferred languages not available
    assert person.name == "John Smith"


def test_non_language_designated_strings_all_selected():
    """Test 5: For strings without language designators, select all available"""
    # Test with any language preference
    loader = PydanticRDFLoader(preferred_languages=['en'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # Aliases don't have language designators, should get all of them
    assert person.aliases is not None
    assert isinstance(person.aliases, list)
    
    # Should contain aliases from all languages since no language tags
    assert "Johnny" in person.aliases     # English
    assert "Juan" in person.aliases       # Spanish  
    assert "Ιωάννης" in person.aliases    # Greek
    assert "יונתן" in person.aliases      # Hebrew
    assert "约翰" in person.aliases       # Chinese
    assert "Іван" in person.aliases      # Ukrainian Cyrillic
    assert "ジョン" in person.aliases     # Japanese Katakana
    
    # Should have all aliases regardless of language preference
    expected_aliases_count = 17  # Based on the aliases in the file
    assert len(person.aliases) == expected_aliases_count


def test_no_preferred_language_no_english_fallback_alphabetical():
    """Test 6: For fields without preferred language and no English, select first alphabetically"""
    # Use language preference that doesn't include Spanish or other description languages
    loader = PydanticRDFLoader(preferred_languages=['ja', 'ko', 'pt'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # For description field: no Japanese, Korean, or Portuguese available
    # No English version in descriptions, so should fall back to first alphabetically
    # First alphabetically should be Spanish (@es)
    assert person.description == "Una persona para probar la funcionalidad multiidioma"


def test_language_preference_with_available_description():
    """Test language preference when target language is available for description"""
    # Select French specifically for description field
    loader = PydanticRDFLoader(preferred_languages=['fr'])
    
    person = loader.load(env.input_path("multilingual_person.ttl"), Person)
    
    # Should get French description
    assert person.description == "Une personne pour tester la fonctionnalité multilingue"


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