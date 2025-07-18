from linkml_runtime.loaders.csv_loader import CSVLoader
from linkml_runtime.loaders.json_loader import JSONLoader
from linkml_runtime.loaders.rdf_loader import RDFLoader
from linkml_runtime.loaders.rdflib_loader import RDFLibLoader
from linkml_runtime.loaders.tsv_loader import TSVLoader
from linkml_runtime.loaders.yaml_loader import YAMLLoader

json_loader = JSONLoader()
rdf_loader = RDFLoader()
rdflib_loader = RDFLibLoader()
yaml_loader = YAMLLoader()
csv_loader = CSVLoader()
tsv_loader = TSVLoader()
