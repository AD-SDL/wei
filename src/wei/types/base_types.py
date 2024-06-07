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

    def write_yaml(self, cfg_path: PathLike) -> None:
        """Allows programmatic creation of ot2util objects and saving them into yaml.
        Parameters
        ----------
        cfg_path : PathLike
            Path to dump the yaml file.
        Returns
        -------
        None
        """
        with open(cfg_path, mode="w") as fp:
            yaml.dump(json.loads(self.json()), fp, indent=4, sort_keys=False)

    @classmethod
    def from_yaml(cls: Type[_T], filename: PathLike) -> _T:
        """Allows loading of yaml into ot2util objects.
        Parameters
        ----------
        filename: PathLike
            Path to yaml file location.
        """
        with open(filename) as fp:
            raw_data = yaml.safe_load(fp)
        return cls(**raw_data)
