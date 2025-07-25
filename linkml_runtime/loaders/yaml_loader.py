from __future__ import annotations

import os
from io import StringIO
from typing import TYPE_CHECKING, TextIO

import yaml
from hbreader import FileInfo

from linkml_runtime.loaders.loader_root import Loader
from linkml_runtime.utils.yamlutils import DupCheckYamlLoader, YAMLRoot

if TYPE_CHECKING:
    from pydantic import BaseModel


class YAMLLoader(Loader):
    """
    A Loader that is capable of instantiating LinkML data objects from a YAML file
    """

    def load_as_dict(
        self, source: str | dict | TextIO, *, base_dir: str | None = None, metadata: FileInfo | None = None
    ) -> dict | list[dict]:
        if metadata is None:
            metadata = FileInfo()
        if base_dir and not metadata.base_path:
            metadata.base_path = base_dir
        data = self._read_source(
            source, base_dir=base_dir, metadata=metadata, accept_header="text/yaml, application/yaml;q=0.9"
        )
        if isinstance(data, str):
            data = StringIO(data)
            if metadata and metadata.source_file:
                data.name = os.path.relpath(metadata.source_file, metadata.base_path)
            return yaml.load(data, DupCheckYamlLoader)
        return data

    def load_any(
        self,
        source: str | dict | TextIO,
        target_class: type[YAMLRoot | BaseModel],
        *,
        base_dir: str | None = None,
        metadata: FileInfo | None = None,
        **_,
    ) -> YAMLRoot | list[YAMLRoot]:
        data_as_dict = self.load_as_dict(source, base_dir=base_dir, metadata=metadata)
        return self._construct_target_class(data_as_dict, target_class)

    def loads_any(
        self, source: str, target_class: type[BaseModel | YAMLRoot], *, metadata: FileInfo | None = None, **_
    ) -> BaseModel | YAMLRoot | list[BaseModel] | list[YAMLRoot]:
        """
        Load source as a string
        @param source: source
        @param target_class: destination class
        @param metadata: metadata about the source
        @param _: extensions
        @return: instance of taarget_class
        """
        return self.load_any(source, target_class, metadata=metadata)
