import logging
import urllib
from typing import Any, Optional, Union

from curies import Converter
from pydantic import BaseModel
from rdflib import XSD, Graph, URIRef
from rdflib.namespace import RDF
from rdflib.term import BNode, Literal, Node

from linkml_runtime.dumpers.dumper_root import Dumper
from linkml_runtime.linkml_model import ElementName, PermissibleValue, PermissibleValueText, SlotDefinition
from linkml_runtime.utils.schemaview import SchemaView
from linkml_runtime.utils.yamlutils import YAMLRoot

logger = logging.getLogger(__name__)


class RDFLibDumper(Dumper):
    """
    Dumps from elements (instances of a LinkML model) to an rdflib Graph

    Note: this should be used in place of rdf_loader for now

    This requires a SchemaView object

    The conversion process follows this general flow:
    1. Create an RDF graph with appropriate namespace bindings
    2. Recursively traverse the object structure, converting each element to RDF
    3. Handle three main cases during conversion:
       - Enums: Convert to URIs (if they have meanings) or Literals
       - Types: Convert to appropriately typed RDF Literals
       - Complex Objects: Create subject-predicate-object triples for each property

    """

    def as_rdf_graph(
        self,
        element: Union[BaseModel, YAMLRoot],
        schemaview: SchemaView,
        prefix_map: Union[dict[str, str], Converter, None] = None,
    ) -> Graph:
        """
        Dumps from element to an rdflib Graph,
        following a schema

        :param element: element to represent in RDF
        :param schemaview:
        :param prefix_map:
        :return:
        """
        # Initialize empty RDF graph
        g = Graph()

        # Handle different prefix map formats
        if isinstance(prefix_map, Converter):
            # TODO replace with `prefix_map = prefix_map.bimap` after making minimum requirement on python 3.8
            prefix_map = {record.prefix: record.uri_prefix for record in prefix_map.records}
        logger.debug(f"PREFIXMAP={prefix_map}")

        # Get schema namespaces and merge with any provided prefix map
        namespaces = schemaview.namespaces()
        if prefix_map:
            for k, v in prefix_map.items():
                if k == "@base":
                    # Special handling for base URI
                    namespaces._base = v
                else:
                    # Add prefix to both namespace manager and graph bindings
                    namespaces[k] = v
                    g.namespace_manager.bind(k, URIRef(v))

        # Bind all namespaces to the graph
        for prefix in namespaces:
            g.bind(prefix, URIRef(namespaces[prefix]))

        # Handle alternate base URI syntax
        # user can pass in base in prefixmap using '_base'. This gets set
        # in namespaces as a plain dict assignment - explicitly call the setter
        # to set the underlying "@base"
        if "_base" in namespaces:
            namespaces._base = namespaces["_base"]

        # Set graph base URI if specified
        if namespaces._base:
            g.base = namespaces._base

        # Recursively convert the element to RDF triples
        self.inject_triples(element, schemaview, g)
        return g

    def inject_triples(
        self, element: Any, schemaview: SchemaView, graph: Graph, target_type: ElementName = None
    ) -> Node:
        """
        Main dispatcher - delegates to specific type handlers
        
        :param element: element to represent in RDF
        :param schemaview:
        :param graph:
        :param target_type:
        :return: root node as rdflib URIRef, BNode, or Literal
        """
        logger.debug(f"CONVERT: {element} // {type(element)} // {target_type}")
        
        # Dispatch to appropriate handler based on target type
        if target_type in schemaview.all_enums():
            return self._handle_enum(element, schemaview, target_type)
        elif target_type in schemaview.all_types():
            return self._handle_type(element, schemaview, target_type)
        else:
            return self._handle_complex_object(element, schemaview, graph, target_type)

    def _handle_enum(self, element: Any, schemaview: SchemaView, target_type: ElementName) -> Node:
        """Handle enum conversion logic"""
        # Handle different forms of enum values
        if isinstance(element, PermissibleValueText):
            # If it's just text, look up the full PermissibleValue object
            e = schemaview.get_enum(target_type)
            element = e.permissible_values[element]
        else:
            # Otherwise extract the code from the enum object
            element = element.code
        element: PermissibleValue
        
        # Convert to RDF: Use URI if enum has meaning (e.g., ontology term), otherwise plain literal
        if element.meaning is not None:
            return URIRef(schemaview.expand_curie(element.meaning))
        else:
            return Literal(element.text)

    def _handle_type(self, element: Any, schemaview: SchemaView, target_type: ElementName) -> Node:
        """Handle primitive type conversion logic"""
        namespaces = schemaview.namespaces()
        t = schemaview.get_type(target_type)
        dt_uri = t.uri
        if dt_uri:
            # Special handling for specific types
            if dt_uri == "rdfs:Resource":
                # Resources become URIs
                return URIRef(schemaview.expand_curie(element))
            elif dt_uri == "xsd:string":
                # Strings become plain literals
                return Literal(element)
            else:
                # Other types (integers, dates, etc.) become typed literals
                if "xsd" not in namespaces:
                    namespaces["xsd"] = XSD
                return Literal(element, datatype=namespaces.uri_for(dt_uri))
        else:
            # Fallback for types without specified URIs
            logger.warning(f"No datatype specified for : {t.name}, using plain Literal")
            return Literal(element)

    def _handle_complex_object(self, element: Any, schemaview: SchemaView, graph: Graph, target_type: ElementName = None) -> Node:
        """Handle complex object conversion logic"""
        # Extract all public attributes (non-underscore) from the object
        element_vars = {k: v for k, v in vars(element).items() if not k.startswith("_")}
        
        # Special case: If object has no properties, treat it as a simple identifier
        if len(element_vars) == 0:
            id_slot = schemaview.get_identifier_slot(target_type)
            return self._as_uri(element, id_slot, schemaview)
            # return URIRef(schemaview.expand_curie(str(element)))
        
        # Get the class name and determine the subject URI for this object
        element_type = type(element)
        cn = element_type.class_name
        id_slot = schemaview.get_identifier_slot(cn)
        
        # Create subject node: Use identifier if available, otherwise create blank node
        if id_slot is not None:
            element_id = getattr(element, id_slot.name)
            element_uri = self._as_uri(element_id, id_slot, schemaview)
        else:
            # No identifier slot - use anonymous blank node
            element_uri = BNode()
        
        # Track whether we've added a type triple (to avoid duplication)
        type_added = False
        slot_name_map = schemaview.slot_name_mappings()
        
        # Process each property of the object
        for k, v_or_list in element_vars.items():
            # Normalize values to a list for uniform processing
            if isinstance(v_or_list, list):
                vs = v_or_list
            elif isinstance(v_or_list, dict):
                # For dict-valued slots, use the values (keys are identifiers)
                vs = v_or_list.values()
            else:
                vs = [v_or_list]
            
            # Process each value for this property
            for v in vs:
                if v is None:
                    continue
                
                # Map Python attribute name to schema slot name if needed
                if k in slot_name_map:
                    k = slot_name_map[k].name
                else:
                    logger.error(f"Slot {k} not in name map")
                
                # Get the slot definition with all inherited properties
                slot = schemaview.induced_slot(k, cn)
                
                # Skip identifier slots (already used as subject URI)
                if not slot.identifier:
                    # Create predicate URI from slot
                    slot_uri = URIRef(schemaview.get_uri(slot, expand=True))
                    
                    # Recursively convert the value based on its expected type
                    v_node = self.inject_triples(v, schemaview, graph, slot.range)
                    
                    # Add the triple: subject predicate object
                    graph.add((element_uri, slot_uri, v_node))
                    
                    # Check if this slot implies the type (e.g., rdf:type)
                    if slot.designates_type:
                        type_added = True
        
        # Add rdf:type triple if not already added by a designates_type slot
        if not type_added:
            graph.add((element_uri, RDF.type, URIRef(schemaview.get_uri(cn, expand=True))))
        
        # Return the subject node for use in parent context
        return element_uri

    def dump(
        self,
        element: Union[BaseModel, YAMLRoot],
        to_file: str,
        schemaview: SchemaView = None,
        fmt: str = "turtle",
        prefix_map: Union[dict[str, str], Converter, None] = None,
        **args,
    ) -> None:
        """
        Write element as rdf to to_file

        :param element: element to represent in RDF
        :param to_file:
        :param schemaview:
        :param fmt:
        :param prefix_map:
        :return:
        """
        super().dump(element, to_file, schemaview=schemaview, fmt=fmt, prefix_map=prefix_map)

    def dumps(
        self,
        element: Union[BaseModel, YAMLRoot],
        schemaview: SchemaView = None,
        fmt: Optional[str] = "turtle",
        prefix_map: Union[dict[str, str], Converter, None] = None,
    ) -> str:
        """
        Convert element into an RDF graph guided by the schema

        :param element:
        :param schemaview:
        :param fmt:
        :param prefix_map:
        :return: serialization of rdflib Graph containing element
        """
        return self.as_rdf_graph(element, schemaview, prefix_map=prefix_map).serialize(format=fmt)

    def _as_uri(self, element_id: str, id_slot: Optional[SlotDefinition], schemaview: SchemaView) -> URIRef:
        """Convert an identifier to a URI, with optional percent-encoding"""
        if id_slot and schemaview.is_slot_percent_encoded(id_slot):
            # Percent-encode the identifier if the slot requires it
            return URIRef(urllib.parse.quote(element_id))
        else:
            # Otherwise, use standard CURIE expansion
            return schemaview.namespaces().uri_for(element_id)
