from pathlib import Path

from hbreader import FileInfo
from pydantic import BaseModel

from linkml_runtime.dumpers import yaml_dumper
from linkml_runtime.loaders import json_loader, yaml_loader
from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import YAMLRoot
from tests.test_loaders_dumpers.environment import env
from tests.test_loaders_dumpers.models.books_normalized_pydantic import BookSeries
from tests.test_loaders_dumpers.models.kitchen_sink_pydantic import Dataset


@pytest.mark.parametrize(
    "filename,model,loader",
    [
        ("book_series_lotr.yaml", BookSeries, yaml_loader),
        ("book_series_lotr.json", BookSeries, json_loader),
        ("kitchen_sink_normalized_inst_01.yaml", Dataset, yaml_loader),
        ("kitchen_sink_normalized_inst_01.json", Dataset, json_loader),
    ],
)
def test_loader_basemodel(filename, model, loader):
    name = Path(filename).stem
    type = Path(filename).suffix.lstrip(".")
    expected_yaml_file = env.input_path(f"{name}_{type}.yaml")

    metadata = FileInfo()

    # Make sure metadata gets filled out properly
    rel_path = os.path.abspath(os.path.join(test_base.env.cwd, ".."))
    assert os.path.normpath("tests/test_loaders_dumpers/input") == os.path.normpath(
        os.path.relpath(metadata.base_path, rel_path)
    )
    assert os.path.normpath(f"tests/test_loaders_dumpers/input/{filename}") == os.path.normpath(
        os.path.relpath(metadata.source_file, rel_path)
    )

    # Load expected output
    with open(expected_yaml_file) as expf:
        expected = expf.read()

def test_yaml_loader_single():
    """Load book_series_lotr.yaml with yaml_loader and test results"""
    loader_test("book_series_lotr.yaml", BookSeries, yaml_loader)


def test_json_loader():
    """Load book_series_lotr.json with json_loader and test results"""
    loader_test("book_series_lotr.json", BookSeries, json_loader)


def test_yaml_loader_kitchen_sink():
    """Load kitchen_sink_normalized_inst_01.yaml with yaml_loader and test results"""
    loader_test("kitchen_sink_normalized_inst_01.yaml", Dataset, yaml_loader)


def test_json_loader_kitchen_sink():
    """Load kitchen_sink_normalized_inst_01.json with json_loader and test results"""
    loader_test("kitchen_sink_normalized_inst_01.json", Dataset, json_loader)
