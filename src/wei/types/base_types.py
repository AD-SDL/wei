"""Base Dataclasses and Enums for WEI"""

import json
from pathlib import Path
from typing import Optional, Type, TypeVar, Union

import yaml
from pydantic import AliasChoices, Field
from pydantic import BaseModel as _BaseModel
from pydantic.functional_validators import model_validator
from typing_extensions import Self
from ulid import ULID

_T = TypeVar("_T")

PathLike = Union[str, Path]


def ulid_factory() -> str:
    """Generates a ulid"""
    return str(ULID())


class BaseModel(_BaseModel, use_enum_values=True):
    """Allows any sub-class to inherit methods allowing for programmatic description of protocols
    Can load a yaml into a class and write a class into a yaml file.
    """

    def write_yaml(self, path: PathLike) -> None:
        """Allows all derived data models to be exported into yaml.
        Parameters
        ----------
        path : PathLike
            Path to dump the yaml file.
        Returns
        -------
        None
        """
        with open(path, mode="w") as fp:
            yaml.dump(json.loads(self.json()), fp, indent=4, sort_keys=False)

    @classmethod
    def from_yaml(cls: Type[_T], path: PathLike) -> _T:
        """Allows all derived data models to be loaded from yaml.
        Parameters
        ----------
        path: PathLike
            Path to a yaml file to be read.
        """
        with open(path) as fp:
            raw_data = yaml.safe_load(fp)
        return cls(**raw_data)

    @model_validator(mode="after")
    def validate_ulids(self) -> Self:
        """Validates that all ULID fields are valid"""
        for field in self.model_fields:
            if field == "id" or field.endswith("_id"):
                try:
                    if self.model_dump()[field]:
                        ULID.from_str(self.model_dump()[field])
                except ValueError as e:
                    raise ValueError(f"Invalid ULID in field {field}") from e
        return self


class Metadata(BaseModel, extra="allow"):
    """Metadata container"""

    author: Optional[str] = None
    """Who wrote this object"""
    description: Optional[str] = Field(
        default=None, alias=AliasChoices("description", "info")
    )
    """Description of the object"""
    version: Union[float, str] = ""
    """Version of the object"""
