from linkml_runtime.utils.distroutils import get_jsonschema_string, get_schema_string


def test_distroutils():
    p = "linkml_runtime.linkml_model.meta"
    js = get_jsonschema_string(p)
    assert "ClassDefinition" in js
    ys = get_schema_string(p)
    assert "class_definition" in ys
