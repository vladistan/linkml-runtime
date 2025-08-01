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
        g = Graph()
        if isinstance(prefix_map, Converter):
            # TODO replace with `prefix_map = prefix_map.bimap` after making minimum requirement on python 3.8
            prefix_map = {record.prefix: record.uri_prefix for record in prefix_map.records}
        logger.debug(f"PREFIXMAP={prefix_map}")
        namespaces = schemaview.namespaces()
        if prefix_map:
            for k, v in prefix_map.items():
                if k == "@base":
                    namespaces._base = v
                else:
                    namespaces[k] = v
                    g.namespace_manager.bind(k, URIRef(v))

        for prefix in namespaces:
            g.bind(prefix, URIRef(namespaces[prefix]))
        # user can pass in base in prefixmap using '_base'. This gets set
        # in namespaces as a plain dict assignment - explicitly call the setter
        # to set the underlying "@base"
        if "_base" in namespaces:
            namespaces._base = namespaces["_base"]

        if namespaces._base:
            g.base = namespaces._base

        self.inject_triples(element, schemaview, g)
        return g

    def inject_triples(
        self, element: Any, schemaview: SchemaView, graph: Graph, target_type: ElementName = None
    ) -> Node:
        """
        Inject triples from conversion of element into a Graph

        :param element: element to represent in RDF
        :param schemaview:
        :param graph:
        :param target_type:
        :return: root node as rdflib URIRef, BNode, or Literal
        """
        namespaces = schemaview.namespaces()
        slot_name_map = schemaview.slot_name_mappings()
        logger.debug(f"CONVERT: {element} // {type(element)} // {target_type}")
        if target_type in schemaview.all_enums():
            if isinstance(element, PermissibleValueText):
                e = schemaview.get_enum(target_type)
                element = e.permissible_values[element]
            else:
                element = element.code
            element: PermissibleValue
            if element.meaning is not None:
                return URIRef(schemaview.expand_curie(element.meaning))
            else:
                return Literal(element.text)
        if target_type in schemaview.all_types():
            t = schemaview.get_type(target_type)
            dt_uri = t.uri
            if dt_uri:
                if dt_uri == "rdfs:Resource":
                    return URIRef(schemaview.expand_curie(element))
                elif dt_uri == "xsd:string":
                    return Literal(element)
                else:
                    if "xsd" not in namespaces:
                        namespaces["xsd"] = XSD
                    return Literal(element, datatype=namespaces.uri_for(dt_uri))
            else:
                logger.warning(f"No datatype specified for : {t.name}, using plain Literal")
                return Literal(element)
        element_vars = {k: v for k, v in vars(element).items() if not k.startswith("_")}
        if len(element_vars) == 0:
            id_slot = schemaview.get_identifier_slot(target_type)
            return self._as_uri(element, id_slot, schemaview)
            # return URIRef(schemaview.expand_curie(str(element)))
        element_type = type(element)
        cn = element_type.class_name
        id_slot = schemaview.get_identifier_slot(cn)
        if id_slot is not None:
            element_id = getattr(element, id_slot.name)
            element_uri = self._as_uri(element_id, id_slot, schemaview)
        else:
            element_uri = BNode()
        type_added = False
        for k, v_or_list in element_vars.items():
            if isinstance(v_or_list, list):
                vs = v_or_list
            elif isinstance(v_or_list, dict):
                vs = v_or_list.values()
            else:
                vs = [v_or_list]
            for v in vs:
                if v is None:
                    continue
                if k in slot_name_map:
                    k = slot_name_map[k].name
                else:
                    logger.error(f"Slot {k} not in name map")
                slot = schemaview.induced_slot(k, cn)
                if not slot.identifier:
                    slot_uri = URIRef(schemaview.get_uri(slot, expand=True))
                    v_node = self.inject_triples(v, schemaview, graph, slot.range)
                    graph.add((element_uri, slot_uri, v_node))
                    if slot.designates_type:
                        type_added = True
        if not type_added:
            graph.add((element_uri, RDF.type, URIRef(schemaview.get_uri(cn, expand=True))))
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
        if id_slot and schemaview.is_slot_percent_encoded(id_slot):
            return URIRef(urllib.parse.quote(element_id))
        else:
            return schemaview.namespaces().uri_for(element_id)
