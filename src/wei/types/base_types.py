"""Base Dataclasses and Enums for WEI"""

import json
from pathlib import Path
from typing import Type, TypeVar, Union

import ulid
import yaml
from pydantic import BaseModel as _BaseModel

_T = TypeVar("_T")

PathLike = Union[str, Path]


def ulid_factory() -> str:
    """Generates a ulid string"""
    return ulid.new().str


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
