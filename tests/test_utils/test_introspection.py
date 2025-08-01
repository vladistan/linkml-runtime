from linkml_runtime.linkml_model import SchemaDefinition
from linkml_runtime.utils.introspection import object_class_definition, package_schemaview


def test_introspection_on_metamodel():
    """Test introspection capabilities on the linkml metamodel"""
    view = package_schemaview("linkml_runtime.linkml_model.meta")
    
    # Test that expected classes are present
    for cn in ["class_definition", "type_definition", "slot_definition"]:
        assert cn in view.all_classes()
    
    # Test that expected types are present    
    for tn in ["uriorcurie", "string", "float"]:
        assert tn in view.all_types()
    
    # Test object class definition introspection
    obj = SchemaDefinition(id="x", name="x")
    c = object_class_definition(obj)
    assert "classes" in c.slots
