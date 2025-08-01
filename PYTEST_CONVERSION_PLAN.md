# Unittest to Pytest Conversion Implementation Plan

## Progress Overview

### Completed ✅ (23/30 files - 77% complete)
- ✅ tests/test_utils/test_version.py 🟢
- ✅ tests/test_utils/test_metamodelcore.py 🟡
- ✅ tests/test_utils/test_list_strings.py 🟢
- ✅ tests/test_utils/test_pattern.py 🟢
- ✅ tests/test_utils/test_formatutils.py 🟢
- ✅ tests/test_utils/test_curienamespace.py 🟢
- ✅ tests/test_utils/test_namespaces.py 🟡
- ✅ tests/test_utils/test_inference_utils.py 🟡
- ✅ tests/test_utils/test_dict_utils.py 🟢
- ✅ tests/test_utils/test_walker_utils.py 🟢
- ✅ tests/test_utils/test_distroutils.py 🟢
- ✅ tests/test_utils/test_ruleutils.py 🟢
- ✅ tests/test_utils/test_schema_as_dict.py 🟠
- ✅ tests/test_utils/test_inlined_as_list_forms.py 🟡 (Enhanced: 13 focused tests)
- ✅ tests/test_utils/test_inlined_as_dict_forms.py 🟡 (Enhanced: 14 focused tests)
- ✅ tests/test_utils/test_introspection.py 🟡
- ✅ tests/test_utils/test_poly_dataclasses.py 🟡
- ✅ tests/test_loaders_dumpers/test_enum.py 🟢
- ✅ tests/test_loaders_dumpers/test_csv_tsv_loader_dumper.py 🟠
- ✅ tests/test_issues/test_include_schema.py 🟠
- ✅ tests/test_processing/test_arrays.py 🟡
- ✅ tests/test_index/test_object_index.py 🟡
- ✅ tests/test_loaders_dumpers/test_loaders_pydantic.py 🟡

### Remaining Files to Convert (7/30 files - 23% remaining)

#### tests/test_loaders_dumpers/ (4 files)
- ⏳ test_loaders_dumpers.py 🔴
- ✅ test_loaders_pydantic.py 🟡
- ⏳ test_loaders.py 🟡
- ⏳ test_dumpers.py 🟡
- ⏳ test_rdflib_dumper.py 🟡
- ✅ test_csv_tsv_loader_dumper.py 🟠
- ✅ test_enum.py 🟢

#### tests/test_utils/ (0 files) ✅ ALL COMPLETED
- ✅ test_inlined_as_list_forms.py 🟡
- ✅ test_schema_as_dict.py 🟠
- ✅ test_inlined_as_dict_forms.py 🟡
- ✅ test_introspection.py 🟡
- ✅ test_poly_dataclasses.py 🟡
- ✅ test_ruleutils.py 🟢
- ✅ test_distroutils.py 🟢
- ✅ test_dict_utils.py 🟢
- ✅ test_walker_utils.py 🟢

#### tests/test_processing/ (1 file)
- ✅ test_arrays.py 🟡
- ⏳ test_referencevalidator.py 🟠

#### tests/test_index/ (0 files) ✅ ALL COMPLETED
- ✅ test_object_index.py 🟡

#### tests/support/ (2 files)
- ⏳ clicktestcase.py 🔴 - *Base class used by other tests*
- ⏳ test_environment.py 🟡 - *Test infrastructure*

#### tests/test_issues/ (0 files) ✅ ALL COMPLETED
- ✅ test_include_schema.py 🟠

### Recommended Order by Complexity
**Easy wins 🟢:**
- ✅ test_enum.py

**Medium effort 🟠🟡:**
- ✅ test_csv_tsv_loader_dumper.py
- ✅ test_include_schema.py
- ✅ test_arrays.py
- ✅ test_object_index.py
- ✅ test_loaders_pydantic.py
- ⏳ test_loaders.py
- ⏳ test_dumpers.py
- ⏳ test_rdflib_dumper.py
- ⏳ test_environment.py

**Complex 🔴:**
- ⏳ test_referencevalidator.py
- ⏳ test_loaders_dumpers.py
- ⏳ clicktestcase.py

---

## Conversion Details by File

### tests/test_loaders_dumpers/

#### test_loaders_dumpers.py
**Complexity**: High
**Key Features**:
- Uses setUp() method to load and test data through multiple formats
- Has helper method _check_objs()
- Tests round-trip conversions between YAML/JSON/RDF
- Multiple test methods with complex assertions

**Conversion Notes**:
- Convert setUp() to a fixture that yields the loaded container
- Keep _check_objs() as a standalone helper function
- May need multiple fixtures for different data formats
- Watch for assertCountEqual() - convert to sorted comparison

#### test_loaders_pydantic.py
**Complexity**: Medium
**Key Features**:
- Tests Pydantic model integration
- Multiple test methods without setUp/tearDown

**Conversion Notes**:
- Straightforward conversion of test methods
- Replace unittest assertions with pytest equivalents

#### test_loaders.py
**Complexity**: Medium
**Key Features**:
- Tests various loader functionalities
- No setUp/tearDown methods visible

**Conversion Notes**:
- Direct conversion of test methods to functions
- Check for any inherited behavior from base classes

#### test_dumpers.py
**Complexity**: Medium
**Key Features**:
- Tests dumper functionalities
- Likely mirrors test_loaders.py structure

**Conversion Notes**:
- Similar approach to test_loaders.py
- Ensure consistency between loader and dumper tests

#### test_rdflib_dumper.py
**Complexity**: Medium
**Key Features**:
- Tests RDF library integration
- May involve complex RDF graph comparisons

**Conversion Notes**:
- RDF comparisons might need custom assertion helpers
- Check for any RDF-specific setUp/tearDown

#### test_csv_tsv_loader_dumper.py ✅ COMPLETED
**Complexity**: Low-Medium
**Key Features**:
- Tests CSV/TSV file handling with books normalized data
- 6 test methods covering round-trip conversions and complex data
- Uses temporary files for output testing
- Tests both object and dictionary loading modes

**Conversion Notes**:
- ✅ Comprehensive conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted all 6 test methods to standalone functions
- ✅ **ENHANCED**: Created clean pytest fixtures:
  - `schema_view()` - SchemaView instance for books normalized schema
  - `test_data()` - Loads books_normalized_01.yaml test data
  - `test_data2()` - Loads books_normalized_02.yaml test data
- ✅ **ENHANCED**: Used `tmp_path` fixture for temporary file handling instead of hardcoded paths
- ✅ All assertions were already using assert statements (no conversion needed)
- ✅ Preserved all debug logging statements for troubleshooting
- ✅ Improved code organization with inline comments
- ✅ Tests import successfully and conversion is complete

#### test_enum.py ✅ COMPLETED
**Complexity**: Low
**Key Features**:
- Tests enumeration handling in loaders/dumpers
- Single test method: test_enum
- Tests JSON and YAML serialization/deserialization of enums
- Tests round-trip conversion (load/dump cycles)
- References GitHub issues #337 and #119

**Conversion Notes**:
- ✅ Simple conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted single test method to standalone function
- ✅ All assertions were already using assert statements (no conversion needed)
- ✅ Added inline comments to group related assertions for clarity
- ✅ Preserved all debug print statements for troubleshooting
- ✅ Preserved issue references in docstring
- ✅ Tests import successfully and conversion is complete

### tests/test_utils/

#### test_inlined_as_list_forms.py ✅ COMPLETED
**Complexity**: Medium
**Key Features**:
- Tests various YAML forms for inlined_as_list entries
- Two test methods: test_list_variations and test_dict_variations
- Tests 7 different forms of list and dictionary structures
- Uses assertRaises for exception testing

**Conversion Notes**:
- ✅ Straightforward conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ **ENHANCED**: Broke down 2 large test methods into 13 focused individual tests:
  - `test_empty_list_forms()` - Tests various empty forms
  - `test_list_of_keys()` - Form 5: list of keys
  - `test_list_of_key_object_pairs()` - Form 4: key/object pairs
  - `test_duplicate_keys_error()` - Error handling for duplicates
  - `test_key_mismatch_error()` - Error handling for mismatches
  - `test_form5_variations()` - Form 5 with different object types
  - `test_mixed_form5_variations()` - Form 5 with mixed types
  - `test_positional_object_values()` - Form 6: positional values
  - `test_list_of_kv_dictionaries()` - Form 7: key-value dicts
  - `test_dict_key_object_form()` - Form 1: dictionary key/object
  - `test_dict_key_value_tuples()` - Form 2: key/value tuples
  - `test_single_object_dict()` - Form 3: basic single object
  - `test_single_object_dict_multiple_fields()` - Form 3: multiple fields
- ✅ Each test now focuses on one specific scenario with clear naming
- ✅ Converted all assertEqual assertions to assert statements
- ✅ Converted assertRaises(ValueError) to pytest.raises(ValueError)
- ✅ Changed e.exception to e.value for pytest exception access
- ✅ Converted assertIn to assert "string" in str(e.value)
- ✅ All tests import successfully and conversion is complete

#### test_inlined_as_dict_forms.py ✅ COMPLETED
**Complexity**: Medium
**Key Features**:
- Tests various YAML forms for inlined_as_dict entries (returns dict, not list)
- Three test methods: test_list_variations, test_dict_variations, test_isempties
- Tests 7 different forms of list and dictionary structures
- Uses assertRaises for exception testing
- Tests internal _is_empty method

**Conversion Notes**:
- ✅ Comprehensive conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ **ENHANCED**: Broke down 3 large test methods into 14 focused individual tests:
  - `test_empty_dict_forms()` - Tests various empty forms
  - `test_list_of_keys()` - Form 5: list of keys
  - `test_list_of_key_object_pairs()` - Form 4: key/object pairs
  - `test_duplicate_keys_error()` - Error handling for duplicates
  - `test_key_mismatch_error()` - Error handling for mismatches
  - `test_form5_variations()` - Form 5 with different object types
  - `test_mixed_form5_variations()` - Form 5 with mixed types
  - `test_positional_object_values()` - Form 6: positional values
  - `test_list_of_kv_dictionaries()` - Form 7: key-value dicts
  - `test_dict_key_object_form()` - Form 1: dictionary key/object
  - `test_dict_key_value_tuples()` - Form 2: key/value tuples
  - `test_single_object_dict()` - Form 3: basic single object
  - `test_single_object_dict_multiple_fields()` - Form 3: multiple fields
  - `test_is_empty_method()` - Tests the _is_empty internal method
- ✅ Each test now focuses on one specific scenario with clear naming
- ✅ Converted all assertEqual assertions to assert statements
- ✅ Converted assertRaises(ValueError) to pytest.raises(ValueError)
- ✅ Changed e.exception to e.value for pytest exception access
- ✅ Converted assertTrue/assertFalse to assert/assert not
- ✅ All tests import successfully and conversion is complete

#### test_schema_as_dict.py ✅ COMPLETED
**Complexity**: Low-Medium
**Key Features**:
- Tests schema dictionary representations (schema_as_dict, schema_as_yaml_dump)
- Two test methods: test_as_dict and test_as_dict_with_attributes
- Uses SchemaView and SchemaBuilder

**Conversion Notes**:
- ✅ Straightforward conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted both test methods to standalone functions
- ✅ **ENHANCED**: Replaced complex `schema_paths` dict fixture with three clean, independent fixtures:
  - `schema_no_imports_path()` - Path to kitchen sink schema without imports
  - `schema_with_imports_path()` - Path to kitchen sink schema with imports
  - `clean_output_path()` - Path for clean output schema file
- ✅ Removed unused `yaml_loader()` fixture since it wasn't being used
- ✅ Updated test function parameters to use specific fixtures instead of dict access
- ✅ All assertions were already using assert statements
- ✅ Tests import successfully and conversion is complete

#### test_ruleutils.py ✅ COMPLETED
**Complexity**: Low
**Key Features**:
- Tests rule utilities (get_range_as_disjunction, subclass_to_rules)
- Two test methods: test_disjunction and test_roll_up
- Uses schema loading and rule generation
- One assertCountEqual requiring conversion

**Conversion Notes**:
- ✅ Simple conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted both test methods to standalone functions
- ✅ Converted assertCountEqual to sorted comparison: `assert sorted(disj) == sorted({...})`
- ✅ **ENHANCED**: Added clean pytest fixture for better organization:
  - `rules_schema()` fixture returns SchemaView instance directly
  - Simple, focused fixture that provides exactly what tests need
  - Removed unused YAMLLoader import since it wasn't needed
- ✅ Eliminated code duplication between test functions
- ✅ Clean fixture design - minimal and focused on actual usage
- ✅ Both tests pass after conversion and fixture refactoring

#### test_introspection.py ✅ COMPLETED
**Complexity**: Medium
**Key Features**:
- Tests introspection capabilities on the linkml metamodel
- Single test method: test_introspection_on_metamodel
- Tests package_schemaview and object_class_definition functions
- Validates metamodel classes and types are accessible

**Conversion Notes**:
- ✅ Simple conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted single test method to standalone function
- ✅ All assertions were already using assert statements (no conversion needed)
- ✅ Added descriptive docstring and inline comments for clarity
- ✅ Grouped related assertions with comments for better readability
- ✅ Tests import successfully and conversion is complete

#### test_distroutils.py ✅ COMPLETED
**Complexity**: Low
**Key Features**:
- Tests distribution utilities (get_jsonschema_string, get_schema_string)
- Single test method with simple assertions
- No setUp/tearDown methods

**Conversion Notes**:
- ✅ Very simple conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted single test method to standalone function
- ✅ Assertions were already using assert statements
- ✅ Test passes after conversion

#### test_poly_dataclasses.py ✅ COMPLETED
**Complexity**: Medium
**Key Features**:
- Tests polymorphic dataclass behavior for LinkML metamodel classes
- Single test method: test_class_for_uri
- Tests class lookup functionality (_class_for_uri, _class_for_curie)
- Tests different URI resolution modes and error handling

**Conversion Notes**:
- ✅ Simple conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted single test method to standalone function
- ✅ Converted assertEqual assertions to assert == statements
- ✅ Converted assertIsNone to assert is None
- ✅ Enhanced docstring for better clarity
- ✅ Improved inline comments for each test scenario
- ✅ Tests import successfully and conversion is complete

#### test_dict_utils.py ✅ COMPLETED
**Complexity**: Low
**Key Features**:
- Tests for dictionary utility functions (as_dict, as_simple_dict)
- Tests YAML utilities and dictionary serialization
- Single test method with multiple assertions
- Originally inherited from TestEnvironmentTestCase

**Conversion Notes**:
- ✅ Simple conversion completed
- ✅ Removed inheritance from TestEnvironmentTestCase (not needed)
- ✅ Converted TestCase class to standalone test function
- ✅ Preserved all helper functions (_signature, _is_python_type, _is_basic_type)
- ✅ All assertions were already using assert statements
- ✅ Test passes after conversion

#### test_walker_utils.py ✅ COMPLETED
**Complexity**: Low
**Key Features**:
- Tests for object tree traversal utilities
- Three test methods: collector, mutating transformer, non-mutating transformer
- No setUp/tearDown methods

**Conversion Notes**:
- ✅ Simple conversion completed
- ✅ Converted TestCase class to standalone functions
- ✅ Updated assertions: assertGreater, assertEqual, assertNotEqual → assert statements
- ✅ Preserved count_classes() helper function
- ✅ All 3 tests pass after conversion

### tests/test_processing/

#### test_arrays.py ✅ COMPLETED
**Complexity**: Medium
**Key Features**:
- Tests array normalization functionality
- Single test method: test_array_normalization
- Uses setUp() method to initialize normalizer and matrix data
- Tests multidimensional array processing via ReferenceValidator

**Conversion Notes**:
- ✅ Comprehensive conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted setUp() method to pytest fixtures:
  - `normalizer()` - ReferenceValidator instance for array example schema
  - `matrix_data()` - Loads matrix data from array example data file
- ✅ Converted single test method to standalone function
- ✅ Converted assertEqual assertion to assert statement
- ✅ Enhanced docstring with LinkML documentation reference
- ✅ Preserved array processing logic and numerical comparisons
- ✅ Tests import successfully and conversion is complete

#### test_referencevalidator.py
**Complexity**: Medium-High
**Key Features**:
- Tests reference validation logic
- Likely has complex validation scenarios

**Conversion Notes**:
- May have many edge cases to test
- Consider using parametrize for validation scenarios

### tests/test_index/

#### test_object_index.py
**Complexity**: Medium
**Key Features**:
- Tests object indexing functionality
- May involve complex data structures

**Conversion Notes**:
- Check for index building in setUp
- Convert index queries and assertions

### tests/support/

#### clicktestcase.py
**Complexity**: High
**Key Features**:
- Base class for CLI testing
- Has complex helper methods
- Used by other test files

**Conversion Notes**:
- This is a support class, not a test file
- May need to convert to pytest fixtures or helper functions
- Critical to convert carefully as other tests depend on it

#### test_environment.py
**Complexity**: Medium
**Key Features**:
- Tests or provides test environment setup
- May be used by other tests

**Conversion Notes**:
- Check if this is tests or test infrastructure
- May need to become pytest fixtures

### tests/test_issues/

#### test_include_schema.py ✅ COMPLETED
**Complexity**: Low-Medium
**Key Features**:
- Regression test for GitHub issue #3: schema inclusion exceptions
- Single test method: test_include_schema
- Tests schema loading without assertions (original test)
- Used by linkml issues tracking

**Conversion Notes**:
- ✅ Simple conversion completed
- ✅ Removed unittest imports and TestCase class
- ✅ Converted single test method to standalone function
- ✅ **ENHANCED**: Added meaningful assertions to verify schema loading success:
  - `assert inp is not None` - Ensures schema was loaded
  - `assert isinstance(inp, SchemaDefinition)` - Verifies correct type
- ✅ Enhanced docstring with GitHub issue reference and purpose
- ✅ Preserved GitHub issue #3 reference in comments
- ✅ Tests import successfully and conversion is complete

---

## Conversion Strategy

### Phase 1: Support Infrastructure
1. Convert tests/support/clicktestcase.py to pytest fixtures/helpers
2. Convert tests/support/test_environment.py if needed

### Phase 2: Simple Conversions
1. Complete remaining tests/test_utils/ files
2. Convert tests/test_issues/test_include_schema.py

### Phase 3: Loader/Dumper Tests
1. Start with simpler files (test_enum.py, test_csv_tsv_loader_dumper.py)
2. Move to complex files (test_loaders_dumpers.py)

### Phase 4: Processing and Index
1. Convert tests/test_processing/ files
2. Convert tests/test_index/test_object_index.py

### Phase 5: Validation
1. Run full test suite
2. Check for any broken dependencies
3. Verify test coverage remains the same

## Common Conversion Patterns

### setUp/tearDown → Fixtures
```python
# unittest
class TestCase(unittest.TestCase):
    def setUp(self):
        self.data = load_data()
    
    def tearDown(self):
        cleanup()

# pytest
@pytest.fixture
def data():
    data = load_data()
    yield data
    cleanup()
```

### Assertions
```python
# unittest → pytest
self.assertEqual(a, b)       → assert a == b
self.assertNotEqual(a, b)    → assert a != b
self.assertTrue(x)           → assert x
self.assertFalse(x)          → assert not x
self.assertIs(a, b)          → assert a is b
self.assertIsNone(x)         → assert x is None
self.assertIn(a, b)          → assert a in b
self.assertIsInstance(a, B)  → assert isinstance(a, B)
self.assertRaises(E)         → pytest.raises(E)
self.assertCountEqual(a, b)  → assert sorted(a) == sorted(b)
```

### Skip/ExpectedFailure
```python
# unittest → pytest
@unittest.skip(reason)       → @pytest.mark.skip(reason=reason)
@unittest.skipIf(cond, why)  → @pytest.mark.skipif(cond, reason=why)
@unittest.expectedFailure    → @pytest.mark.xfail
```

## Notes

- Always run tests after conversion to ensure they still pass
- Pay attention to test discovery - pytest finds test_* functions automatically
- Consider using pytest.mark.parametrize for data-driven tests
- Preserve any important comments about test purposes
- Keep helper functions as standalone functions rather than class methods
- Use tmp_path fixture for temporary file handling instead of manual cleanup