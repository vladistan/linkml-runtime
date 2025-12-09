# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## About linkml-runtime

linkml-runtime provides runtime support for LinkML datamodels, offering core functionality for loading, dumping, validating, and working with LinkML schemas and data. It serves as the foundation for the broader LinkML ecosystem.

## Commands

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test directory
uv run pytest tests/test_utils/
uv run pytest tests/test_loaders_dumpers/

# Run specific test file
uv run pytest tests/test_utils/test_schemaview.py

# Run with verbose output
uv run pytest -xvs

# Using make command
make test
```

### Linting and Formatting
```bash
# Format code (auto-fix)
uv run tox -e format

# Check formatting only
uv run tox -e format_check

# Run linter (check only)
uv run tox -e lint

# Run spell checker
uv run tox -e codespell
```

### Development Setup
```bash
# Install with development dependencies
uv sync --all-extras --dev

# Install in editable mode
pip install -e .
```

### CLI Tools
The package provides several CLI tools:
- `comparefiles` - Compare files utility
- `linkml-normalize` - Reference validator

## Architecture Overview

### Core Components

**SchemaView** (`linkml_runtime/utils/schemaview.py`)
- Central API for working with LinkML schemas
- Handles imports, merging, inheritance resolution
- Provides methods for querying schema elements
- Caches computed properties for performance
- Primary interface for schema introspection and manipulation

**Loaders** (`linkml_runtime/loaders/`)
- Load instance data from various formats into LinkML objects
- Base class: `Loader` in `loader_root.py` 
- Format-specific implementations:
  - `yaml_loader.py` - YAML data loading
  - `json_loader.py` - JSON data loading  
  - `csv_loader.py` - CSV/TSV data loading
  - `rdf_loader.py` - RDF data loading
- All loaders inherit from abstract `Loader` class with `load_as_dict()` method

**Dumpers** (`linkml_runtime/dumpers/`)
- Serialize LinkML objects to various formats
- Mirror the structure of loaders with corresponding dumper classes
- Base class: `Dumper` in `dumper_root.py`
- Handle format-specific serialization rules and conventions

**LinkML Model** (`linkml_runtime/linkml_model/`)
- Contains the Python dataclass representation of the LinkML metamodel
- Vendored from the `linkml-model` project
- Provides core classes like `SchemaDefinition`, `ClassDefinition`, `SlotDefinition`
- Updated via `make update_model` from `../linkml-model/`

### Key Utilities

**Core Utilities** (`linkml_runtime/utils/`)
- `curienamespace.py` - URI/CURIE conversion and namespace handling
- `metamodelcore.py` - Core types and utilities for LinkML metamodel
- `yamlutils.py` - YAML handling utilities with LinkML-specific extensions
- `schemaops.py` - Schema manipulation and transformation operations
- `formatutils.py` - String formatting utilities (camelcase, underscore, etc.)
- `namespaces.py` - Namespace management
- `pattern.py` - Pattern resolution for schema validation

## Key Design Patterns

### Loader/Dumper Architecture
- Abstract base classes define common interface
- Format-specific implementations handle serialization details
- Loaders convert external formats → LinkML objects
- Dumpers convert LinkML objects → external formats
- Round-trip compatibility maintained between corresponding loader/dumper pairs

### Schema Import Handling
- SchemaView manages schema import resolution
- Supports local file imports and URL-based imports
- Handles circular dependencies and import caching
- Context utilities manage import path resolution

### Metamodel Integration
- Runtime depends on LinkML metamodel dataclasses
- Metamodel is vendored to avoid circular dependencies
- Regular updates from upstream `linkml-model` project
- SchemaView provides high-level API over raw metamodel objects

## Development Notes

### Vendored Dependencies
The `linkml_runtime/linkml_model/` directory contains vendored code from the `linkml-model` project. To update:

```bash
# From linkml-model directory
make all

# From linkml-runtime directory  
make update_model
```

### Testing Strategy
- Unit tests organized by component (`test_utils/`, `test_loaders_dumpers/`, etc.)
- Loader/dumper tests use round-trip validation
- SchemaView tests cover import resolution and schema querying
- Environment-specific test fixtures in `environment.py` files

### Circular Dependencies
linkml-runtime is designed to be the foundation layer that other LinkML projects depend on. It vendors the metamodel to avoid circular dependencies with `linkml-model`.

### Code Quality
- Uses Ruff for linting and formatting
- Pre-commit hooks enforce code quality
- Spell checking with codespell
- Type checking with mypy (configured in pyproject.toml)