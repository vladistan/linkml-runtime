"""
RDF loader for Pydantic models that uses embedded LinkML metadata.

This loader works with RDF data and converts it back to Pydantic models
using only the embedded linkml_meta without requiring a SchemaView.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union, TextIO

from hbreader import FileInfo
from pydantic import BaseModel
from rdflib import Graph, URIRef, Literal, BNode
from rdflib.namespace import RDF

from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import YAMLRoot

logger = logging.getLogger(__name__)


class PydanticRDFLoader(Loader):
    """
    Loads RDF data into Pydantic models using embedded LinkML metadata.
    
    This loader uses the linkml_meta attributes embedded in Pydantic models
    to understand the RDF structure without requiring a separate SchemaView.
    """
    
    def load(
        self,
        source: Union[str, Graph],
        target_class: Type[BaseModel],
        fmt: str = "turtle",
        prefix_map: Optional[Dict[str, str]] = None,
    ) -> BaseModel:
        """
        Load RDF data into a Pydantic model instance
        
        :param source: RDF data (file path, string, or Graph)
        :param target_class: Target Pydantic model class
        :param fmt: RDF format if source is string/file
        :param prefix_map: Optional prefix mappings
        :return: Pydantic model instance
        """
        # Parse RDF if needed
        if isinstance(source, Graph):
            graph = source
        else:
            graph = Graph()
            if isinstance(source, str):
                # Check if it's RDF content or a file path
                source_stripped = source.strip()
                if (source_stripped.startswith(('@prefix', 'PREFIX', '<', '_:', '{', '[')) or 
                    '\n' in source_stripped or 
                    len(source_stripped) > 200):
                    # It's RDF content
                    graph.parse(data=source, format=fmt)
                else:
                    # It's a file path
                    graph.parse(source, format=fmt)
            else:
                # Handle Path, TextIO, etc.
                graph.parse(source, format=fmt)
        
        # Add optional prefix mappings
        if prefix_map:
            for prefix, uri in prefix_map.items():
                graph.namespace_manager.bind(prefix, URIRef(uri))
        
        # Extract global metadata
        global_meta = self._extract_global_metadata(target_class)
        
        # Build prefix mappings from metadata
        prefixes = {}
        if "prefixes" in global_meta:
            for prefix_info in global_meta["prefixes"].values():
                prefixes[prefix_info["prefix_prefix"]] = prefix_info["prefix_reference"]
        
        # Find the root subject
        root_subject = self._find_root_subject(graph, target_class, global_meta, prefixes)
        
        # Convert RDF to Pydantic model
        return self._convert_subject_to_model(graph, root_subject, target_class, global_meta, prefixes)
    
    def _extract_global_metadata(self, model_class: Type[BaseModel]) -> Dict[str, Any]:
        """Extract global metadata from the model class module"""
        module = model_class.__module__
        try:
            import importlib
            module_obj = importlib.import_module(module)
            if hasattr(module_obj, 'linkml_meta'):
                return module_obj.linkml_meta.root
        except ImportError:
            pass
        return {}
    
    def _find_root_subject(
        self, 
        graph: Graph, 
        target_class: Type[BaseModel], 
        global_meta: Dict[str, Any],
        prefixes: Dict[str, str]
    ) -> URIRef:
        """Find the root subject in the graph for the target class"""
        # Get class metadata
        class_meta = self._get_class_metadata(target_class)
        class_uri = class_meta.get("class_uri")
        
        if class_uri:
            # Expand CURIE to full URI
            expanded_class_uri = self._expand_curie(class_uri, prefixes)
            
            # Find subjects with this type
            for subject in graph.subjects(RDF.type, URIRef(expanded_class_uri)):
                return subject
        
        # Fallback: return first subject
        for subject in graph.subjects():
            if not isinstance(subject, BNode):
                return subject
        
        # Last resort: return any subject
        for subject in graph.subjects():
            return subject
        
        raise ValueError("No suitable subject found in RDF graph")
    
    def _get_class_metadata(self, model_class: Type[BaseModel]) -> Dict[str, Any]:
        """Extract class metadata from Pydantic model class"""
        if hasattr(model_class, 'linkml_meta'):
            return model_class.linkml_meta.root
        return {"name": model_class.__name__}
    
    def _expand_curie(self, curie_or_uri: str, prefixes: Dict[str, str]) -> str:
        """Expand a CURIE to full URI"""
        if "://" in curie_or_uri:
            return curie_or_uri
        if ":" in curie_or_uri:
            prefix, local = curie_or_uri.split(":", 1)
            if prefix in prefixes:
                return prefixes[prefix] + local
        return curie_or_uri
    
    def _convert_subject_to_model(
        self,
        graph: Graph,
        subject: URIRef,
        target_class: Type[BaseModel],
        global_meta: Dict[str, Any],
        prefixes: Dict[str, str]
    ) -> BaseModel:
        """Convert an RDF subject to a Pydantic model instance"""
        # Start with the subject URI as ID if it's not a blank node
        model_data = {}
        if not isinstance(subject, BNode):
            # Extract ID from URI
            subject_str = str(subject)
            # Try to convert back to CURIE if possible
            model_data['id'] = self._uri_to_curie(subject_str, prefixes)
        
        # Process all properties
        for predicate, obj in graph.predicate_objects(subject):
            # Skip rdf:type
            if predicate == RDF.type:
                continue
            
            # Find corresponding field in model
            field_name = self._find_field_for_predicate(target_class, predicate, prefixes)
            if not field_name:
                continue
            
            # Convert object value
            field_value = self._convert_object_value(graph, obj, target_class, field_name, global_meta, prefixes)
            
            # Handle multivalued fields
            if field_name in model_data:
                # Convert to list if not already
                if not isinstance(model_data[field_name], list):
                    model_data[field_name] = [model_data[field_name]]
                model_data[field_name].append(field_value)
            else:
                model_data[field_name] = field_value
        
        # Before creating model instance, check if single values need to be wrapped in lists
        self._wrap_list_fields(model_data, target_class)
        
        # Create model instance
        return target_class(**model_data)
    
    def _wrap_list_fields(self, model_data: Dict[str, Any], target_class: Type[BaseModel]) -> None:
        """Wrap single values in lists for fields that expect lists"""
        import typing
        
        for field_name, field_info in target_class.model_fields.items():
            if field_name not in model_data:
                continue
                
            # Check if field is already a list
            if isinstance(model_data[field_name], list):
                continue
                
            # Check if the field type is a list type
            field_type = field_info.annotation
            
            # Handle Optional[list[...]] and similar Union types
            if hasattr(typing, 'get_origin') and hasattr(typing, 'get_args'):
                origin = typing.get_origin(field_type)
                args = typing.get_args(field_type)
                
                # Handle Union types (like Optional[list[str]])
                if origin is typing.Union:
                    for arg in args:
                        if typing.get_origin(arg) is list:
                            # This field should be a list, wrap the single value
                            model_data[field_name] = [model_data[field_name]]
                            break
                # Handle direct list types
                elif origin is list:
                    model_data[field_name] = [model_data[field_name]]

    def _uri_to_curie(self, uri: str, prefixes: Dict[str, str]) -> str:
        """Convert URI back to CURIE if possible"""
        for prefix, base_uri in prefixes.items():
            if uri.startswith(base_uri):
                return f"{prefix}:{uri[len(base_uri):]}"
        return uri
    
    def _find_field_for_predicate(
        self, 
        model_class: Type[BaseModel], 
        predicate: URIRef, 
        prefixes: Dict[str, str]
    ) -> Optional[str]:
        """Find the model field that corresponds to an RDF predicate"""
        predicate_str = str(predicate)
        
        # Check each field's metadata
        for field_name, field_info in model_class.model_fields.items():
            field_meta = self._get_field_metadata(field_info)
            
            # Check slot_uri
            slot_uri = field_meta.get("slot_uri")
            if slot_uri:
                expanded_slot_uri = self._expand_curie(slot_uri, prefixes)
                if expanded_slot_uri == predicate_str:
                    return field_name
            
            # Check exact_mappings
            exact_mappings = field_meta.get("exact_mappings", [])
            for mapping in exact_mappings:
                expanded_mapping = self._expand_curie(mapping, prefixes)
                if expanded_mapping == predicate_str:
                    return field_name
            
            # Check constructed URI from from_schema + field_name
            from_schema = field_meta.get("from_schema", "")
            if from_schema:
                if not from_schema.endswith(("/", "#")):
                    from_schema += "/"
                constructed_uri = from_schema + field_name
                if constructed_uri == predicate_str:
                    return field_name
        
        return None
    
    def _get_field_metadata(self, field_info) -> Dict[str, Any]:
        """Extract metadata from Pydantic field"""
        if hasattr(field_info, 'json_schema_extra') and field_info.json_schema_extra:
            linkml_meta = field_info.json_schema_extra.get('linkml_meta', {})
            return linkml_meta
        return {}
    
    def _convert_object_value(
        self,
        graph: Graph,
        obj: Union[URIRef, Literal, BNode],
        model_class: Type[BaseModel],
        field_name: str,
        global_meta: Dict[str, Any],
        prefixes: Dict[str, str]
    ) -> Any:
        """Convert an RDF object to appropriate Python value"""
        if isinstance(obj, Literal):
            # Handle typed literals
            if obj.datatype:
                if obj.datatype == URIRef("http://www.w3.org/2001/XMLSchema#integer"):
                    return int(obj)
                elif obj.datatype == URIRef("http://www.w3.org/2001/XMLSchema#decimal"):
                    return float(obj)
                elif obj.datatype == URIRef("http://www.w3.org/2001/XMLSchema#boolean"):
                    return str(obj).lower() in ('true', '1')
                elif obj.datatype == URIRef("http://www.w3.org/2001/XMLSchema#date"):
                    # Import here to avoid circular imports
                    from datetime import date
                    return date.fromisoformat(str(obj))
            
            # Return string representation
            return str(obj)
        
        elif isinstance(obj, URIRef):
            # Could be a reference to another object or just a URI value
            obj_str = str(obj)
            
            # Check if this is a complex object (has rdf:type)
            obj_types = list(graph.objects(obj, RDF.type))
            if obj_types:
                # Try to find corresponding Pydantic class
                target_field_class = self._get_field_target_class(model_class, field_name, global_meta)
                if target_field_class:
                    return self._convert_subject_to_model(graph, obj, target_field_class, global_meta, prefixes)
            
            # Return as CURIE or URI
            return self._uri_to_curie(obj_str, prefixes)
        
        elif isinstance(obj, BNode):
            # Anonymous object - try to convert to nested model
            target_field_class = self._get_field_target_class(model_class, field_name, global_meta)
            if target_field_class:
                return self._convert_subject_to_model(graph, obj, target_field_class, global_meta, prefixes)
            
            # Fallback
            return str(obj)
        
        return str(obj)
    
    def _get_field_target_class(
        self, 
        model_class: Type[BaseModel], 
        field_name: str,
        global_meta: Dict[str, Any]
    ) -> Optional[Type[BaseModel]]:
        """Get the target class for a field if it's a complex object"""
        import typing
        
        field_info = model_class.model_fields.get(field_name)
        if not field_info:
            return None
        
        # First try to get the class from type annotation
        field_type = field_info.annotation
        
        # Handle Optional and List types
        if hasattr(typing, 'get_origin') and hasattr(typing, 'get_args'):
            origin = typing.get_origin(field_type)
            args = typing.get_args(field_type)
            
            # Handle Union types (like Optional[Type])
            if origin is typing.Union:
                for arg in args:
                    # Skip None type
                    if arg is type(None):
                        continue
                    # Check if it's a list
                    if typing.get_origin(arg) is list:
                        inner_args = typing.get_args(arg)
                        if inner_args and isinstance(inner_args[0], type) and issubclass(inner_args[0], BaseModel):
                            return inner_args[0]
                    # Check if it's a direct BaseModel subclass
                    elif isinstance(arg, type) and issubclass(arg, BaseModel):
                        return arg
            # Handle direct list types
            elif origin is list:
                if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                    return args[0]
        
        # Check if it's a direct BaseModel subclass (no Optional/List wrapper)
        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            return field_type
        
        # Fallback to metadata approach
        field_meta = self._get_field_metadata(field_info)
        range_name = field_meta.get("range")
        
        if not range_name:
            return None
        
        # Try to find the class in the same module
        module = model_class.__module__
        try:
            import importlib
            module_obj = importlib.import_module(module)
            if hasattr(module_obj, range_name):
                target_class = getattr(module_obj, range_name)
                if isinstance(target_class, type) and issubclass(target_class, BaseModel):
                    return target_class
        except (ImportError, AttributeError):
            pass
        
        return None
    
    def loads(
        self,
        source: str,
        target_class: Type[BaseModel],
        fmt: str = "turtle",
        prefix_map: Optional[Dict[str, str]] = None,
    ) -> BaseModel:
        """
        Load RDF string into a Pydantic model instance
        
        :param source: RDF string content
        :param target_class: Target Pydantic model class
        :param fmt: RDF format
        :param prefix_map: Optional prefix mappings
        :return: Pydantic model instance
        """
        return self.load(source, target_class, fmt=fmt, prefix_map=prefix_map)
    
    def load_any(
        self,
        source: Union[str, dict, TextIO, Path],
        target_class: Type[Union[BaseModel, YAMLRoot]],
        *,
        base_dir: Optional[str] = None,
        metadata: Optional[FileInfo] = None,
        fmt: str = "turtle",
        prefix_map: Optional[Dict[str, str]] = None,
        **_,
    ) -> Union[BaseModel, YAMLRoot, List[BaseModel], List[YAMLRoot]]:
        """
        Load source as an instance of target_class
        
        :param source: Source file/text/url to load
        :param target_class: Target class
        :param base_dir: Base directory for relative paths
        :param metadata: File metadata
        :param fmt: RDF format
        :param prefix_map: Optional prefix mappings
        :return: Instance of target_class
        """
        # For now, only support Pydantic BaseModel classes
        if not issubclass(target_class, BaseModel):
            raise ValueError("PydanticRDFLoader only supports Pydantic BaseModel classes")
        
        return self.load(source, target_class, fmt=fmt, prefix_map=prefix_map)