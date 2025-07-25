from __future__ import annotations

from abc import ABC, abstractmethod
from logging import getLogger
from typing import TYPE_CHECKING, Any, TextIO

from hbreader import FileInfo, hbread
from jsonasobj2 import JsonObj, as_dict
from pydantic import BaseModel

from linkml_runtime import URI_TO_LOCAL
from linkml_runtime.utils.yamlutils import YAMLRoot

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

CACHE_SIZE = 1024


class Loader(ABC):
    @staticmethod
    def json_clean(inp: Any) -> Any:
        """
        Remove empty values and JSON-LD relics from an input file

        :param inp: JSON-LD representation
        :return: JSON representation
        """

        def _is_empty(o) -> bool:
            return o is None or o == [] or o == {}

        if isinstance(inp, list):
            for e in [inp_e for inp_e in inp if _is_empty(inp_e)]:
                del inp[e]
            for e in inp:
                Loader.json_clean(e)
        elif isinstance(inp, dict):
            for k, v in list(inp.items()):
                if k.startswith("@") or _is_empty(v):
                    del inp[k]
                else:
                    Loader.json_clean(v)
        return inp

    def load_source(
        self,
        source: str | dict | TextIO,
        loader: Callable[[str | dict, FileInfo], dict | list | None],
        target_class: type[YAMLRoot | BaseModel],
        accept_header: str | None = "text/plain, application/yaml;q=0.9",
        metadata: FileInfo | None = None,
    ) -> BaseModel | YAMLRoot | list[BaseModel] | list[YAMLRoot] | None:
        """Base loader - convert a file, url, string, open file handle or dictionary into an instance
        of target_class

        :param source: URL, file name, block of text, Existing Object or open file handle
        :param loader: Take a stringified image or a dictionary and return a loadable dictionary
        :param target_class: Destination class
        :param accept_header: Accept header to use if doing a request
        :param metadata: Metadata about the source.  Filled in as we go along

        :return: Instance of the target class if loader worked
        """

        data = self._read_source(source, metadata=metadata, base_dir=metadata.base_path, accept_header=accept_header)
        data_as_dict = loader(data, metadata)
        return self._construct_target_class(data_as_dict, target_class=target_class)

    def load(self, *args, **kwargs) -> BaseModel | YAMLRoot:
        """
        Load source as an instance of target_class

        :param source: source file/text/url to load
        :param target_class: destination class
        :param base_dir: scoping directory for source if it is a file or url
        :param metadata: metadata about the source
        :param _: extensions
        :return: instance of target_class
        """
        results = self.load_any(*args, **kwargs)
        if isinstance(results, (BaseModel, YAMLRoot)):
            return results
        msg = f"Result is not an instance of BaseModel or YAMLRoot: {type(results)}"
        raise ValueError(msg)

    def load_as_dict(self, *args, **kwargs) -> dict | list[dict]:
        raise NotImplementedError()

    @abstractmethod
    def load_any(
        self,
        source: str | dict | TextIO | Path,
        target_class: type[BaseModel | YAMLRoot],
        *,
        base_dir: str | None = None,
        metadata: FileInfo | None = None,
        **_,
    ) -> BaseModel | YAMLRoot | list[BaseModel] | list[YAMLRoot]:
        """
        Load source as an instance of target_class, or list of instances of target_class

        @param source: source file/text/url to load
        @param target_class: destination class
        @param base_dir: scoping directory for source if it is a file or url
        @param metadata: metadata about the source
        @param _: extensions
        @return: instance of target_class
        """
        raise NotImplementedError()

    def loads_any(
        self, source: str, target_class: type[BaseModel | YAMLRoot], *, metadata: FileInfo | None = None, **_
    ) -> BaseModel | YAMLRoot | list[BaseModel] | list[YAMLRoot]:
        """
        Load source as a string as an instance of target_class, or list of instances of target_class
        @param source: source
        @param target_class: destination class
        @param metadata: metadata about the source
        @param _: extensions
        @return: instance of taarget_class
        """
        return self.load_any(source, target_class, metadata=metadata)

    def loads(
        self, source: str, target_class: type[BaseModel | YAMLRoot], *, metadata: FileInfo | None = None, **_
    ) -> BaseModel | YAMLRoot:
        """
        Load source as a string
        :param source: source
        :param target_class: destination class
        :param metadata: metadata about the source
        :param _: extensions
        :return: instance of taarget_class
        """
        return self.load(source, target_class, metadata=metadata)

    def _construct_target_class(
        self, data_as_dict: dict | list[dict], target_class: type[YAMLRoot | BaseModel]
    ) -> BaseModel | YAMLRoot | list[BaseModel] | list[YAMLRoot] | None:
        if data_as_dict:
            if isinstance(data_as_dict, list):
                if issubclass(target_class, YAMLRoot):
                    return [target_class(**as_dict(x)) for x in data_as_dict]
                if issubclass(target_class, BaseModel):
                    return [target_class.model_validate(as_dict(x)) for x in data_as_dict]
                msg = f"Cannot load list of {target_class}"
                raise ValueError(msg)
            if isinstance(data_as_dict, dict):
                if issubclass(target_class, BaseModel):
                    return target_class.model_validate(data_as_dict)
                return target_class(**data_as_dict)

            if isinstance(data_as_dict, JsonObj):
                return [target_class(**as_dict(x)) for x in data_as_dict]

            msg = f"Unexpected type {data_as_dict}"
            # should really be a TypeError
            raise ValueError(msg)
        return None

    def _read_source(
        self,
        source: str | dict | TextIO,
        *,
        base_dir: str | None = None,
        metadata: FileInfo | None = None,
        accept_header: str | None = "text/plain, application/yaml;q=0.9",
    ) -> dict | str:
        if metadata is None:
            metadata = FileInfo()
        if base_dir and not metadata.base_path:
            metadata.base_path = base_dir

        if isinstance(source, dict):
            return source

        # Try to get local version of schema, if one is known to exist
        try:
            if str(source) in URI_TO_LOCAL:
                source = str(URI_TO_LOCAL[str(source)])
        except (TypeError, KeyError) as e:
            # Fine, use original `source` value
            logger = getLogger("linkml_runtime.loaders.Loader")
            logger.debug(f"Error converting stringlike source to local linkml file: {source}, got: {e}")

        return hbread(source, metadata, base_dir, accept_header)
