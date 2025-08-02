import logging
import urllib
from dataclasses import dataclass
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


@dataclass
class ConversionContext:
    """Context object to reduce parameter passing and centralize conversion state"""
    schemaview: SchemaView
    graph: Graph
    namespaces: Any
    slot_name_map: dict
    
    @classmethod
    def create(cls, schemaview: SchemaView, graph: Graph):
        """Factory method to create context with derived data"""
        return cls(
            schemaview=schemaview,
            graph=graph,
            namespaces=schemaview.namespaces(),
            slot_name_map=schemaview.slot_name_mappings()
        )


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
        Main dispatcher - creates context and delegates to specific type handlers
        
        :param element: element to represent in RDF
        :param schemaview:
        :param graph:
        :param target_type:
        :return: root node as rdflib URIRef, BNode, or Literal
        """
        logger.debug(f"CONVERT: {element} // {type(element)} // {target_type}")
        
        # Create context for this conversion
        ctx = ConversionContext.create(schemaview, graph)
        
        # Dispatch to appropriate handler based on target type
        if target_type in ctx.schemaview.all_enums():
            return self._handle_enum(element, ctx, target_type)
        elif target_type in ctx.schemaview.all_types():
            return self._handle_type(element, ctx, target_type)
        else:
            return self._handle_complex_object(element, ctx, target_type)

    def _handle_enum(self, element: Any, ctx: ConversionContext, target_type: ElementName) -> Node:
        """Handle enum conversion logic with context"""
        # Handle different forms of enum values
        if isinstance(element, PermissibleValueText):
            # If it's just text, look up the full PermissibleValue object
            e = ctx.schemaview.get_enum(target_type)
            element = e.permissible_values[element]
        else:
            # Otherwise extract the code from the enum object
            element = element.code
        element: PermissibleValue
        
        # Convert to RDF: Use URI if enum has meaning (e.g., ontology term), otherwise plain literal
        if element.meaning is not None:
            return URIRef(ctx.schemaview.expand_curie(element.meaning))
        else:
            return Literal(element.text)

    def _handle_type(self, element: Any, ctx: ConversionContext, target_type: ElementName) -> Node:
        """Handle primitive type conversion logic with context"""
        t = ctx.schemaview.get_type(target_type)
        dt_uri = t.uri
        if dt_uri:
            # Special handling for specific types
            if dt_uri == "rdfs:Resource":
                # Resources become URIs
                return URIRef(ctx.schemaview.expand_curie(element))
            elif dt_uri == "xsd:string":
                # Strings become plain literals
                return Literal(element)
            else:
                # Other types (integers, dates, etc.) become typed literals
                if "xsd" not in ctx.namespaces:
                    ctx.namespaces["xsd"] = XSD
                return Literal(element, datatype=ctx.namespaces.uri_for(dt_uri))
        else:
            # Fallback for types without specified URIs
            logger.warning(f"No datatype specified for : {t.name}, using plain Literal")
            return Literal(element)

    def _handle_complex_object(self, element: Any, ctx: ConversionContext, target_type: ElementName = None) -> Node:
        """Handle complex object conversion with context"""
        element_vars = self._extract_element_vars(element)
        if not element_vars:
            return self._handle_simple_identifier(element, ctx, target_type)
        
        subject_uri = self._create_subject_uri(element, ctx)
        type_added = self._process_element_properties(element, element_vars, ctx, subject_uri)
        
        if not type_added:
            self._add_type_triple(subject_uri, element, ctx)
        
        return subject_uri

    def _extract_element_vars(self, element: Any) -> dict:
        """Extract public attributes from element"""
        # Handle primitive types and objects without __dict__
        if not hasattr(element, '__dict__'):
            return {}
        return {k: v for k, v in vars(element).items() if not k.startswith("_")}

    def _get_class_name(self, element: Any) -> str:
        """Get class name from element, handling both YAMLRoot and Pydantic models"""
        element_type = type(element)
        
        # Try YAMLRoot-style class_name attribute first
        if hasattr(element_type, 'class_name'):
            return element_type.class_name
        
        # For Pydantic models, use the class name directly
        return element_type.__name__

    def _handle_simple_identifier(self, element: Any, ctx: ConversionContext, target_type: ElementName) -> Node:
        """Handle objects with no properties - treat as simple identifier"""
        id_slot = ctx.schemaview.get_identifier_slot(target_type)
        return self._as_uri(element, id_slot, ctx.schemaview)

    def _create_subject_uri(self, element: Any, ctx: ConversionContext) -> Node:
        """Create subject URI or blank node for the element"""
        cn = self._get_class_name(element)
        id_slot = ctx.schemaview.get_identifier_slot(cn)
        
        # Create subject node: Use identifier if available, otherwise create blank node
        if id_slot is not None:
            element_id = getattr(element, id_slot.name)
            return self._as_uri(element_id, id_slot, ctx.schemaview)
        else:
            # No identifier slot - use anonymous blank node
            return BNode()

    def _add_type_triple(self, subject_uri: Node, element: Any, ctx: ConversionContext):
        """Add rdf:type triple for the element"""
        cn = self._get_class_name(element)
        ctx.graph.add((subject_uri, RDF.type, URIRef(ctx.schemaview.get_uri(cn, expand=True))))

    def _process_element_properties(self, element: Any, element_vars: dict, ctx: ConversionContext, subject_uri: Node) -> bool:
        """Process all properties of an element, return whether type was added"""
        type_added = False
        cn = self._get_class_name(element)
        
        for prop_name, prop_value in element_vars.items():
            type_added |= self._process_single_property(
                prop_name, prop_value, cn, ctx, subject_uri
            )
        return type_added

    def _process_single_property(self, prop_name: str, prop_value: Any, class_name: str, ctx: ConversionContext, subject_uri: Node) -> bool:
        """Process a single property, return whether it designated type"""
        values = self._normalize_property_values(prop_value)
        
        # Map Python attribute name to schema slot name if needed - preserving original behavior
        slot_name = prop_name
        if prop_name in ctx.slot_name_map:
            slot_name = ctx.slot_name_map[prop_name].name
        else:
            logger.error(f"Slot {prop_name} not in name map")
        
        # Use try/catch to handle missing slots gracefully like the original
        try:
            slot = ctx.schemaview.induced_slot(slot_name, class_name)
        except ValueError:
            # If slot not found, skip this property (matches original behavior when error occurs)
            return False
        
        if slot.identifier:
            return False  # Skip identifier slots
        
        return self._add_property_triples(values, slot, ctx, subject_uri)

    def _normalize_property_values(self, prop_value: Any) -> list:
        """Normalize property values to a list for uniform processing"""
        if isinstance(prop_value, list):
            return prop_value
        elif isinstance(prop_value, dict):
            # For dict-valued slots, use the values (keys are identifiers)
            return list(prop_value.values())
        else:
            return [prop_value]

    def _add_property_triples(self, values: list, slot: Any, ctx: ConversionContext, subject_uri: Node) -> bool:
        """Add triples for all values of a property"""
        type_added = False
        slot_uri = URIRef(ctx.schemaview.get_uri(slot, expand=True))
        
        for v in values:
            if v is None:
                continue
            
            # Recursively convert the value based on its expected type
            v_node = self.inject_triples(v, ctx.schemaview, ctx.graph, slot.range)
            
            # Add the triple: subject predicate object
            ctx.graph.add((subject_uri, slot_uri, v_node))
            
            # Check if this slot implies the type (e.g., rdf:type)
            if slot.designates_type:
                type_added = True
        
        return type_added

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
