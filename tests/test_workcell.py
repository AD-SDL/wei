"""Tests for WEI Workcell functionality"""

from pathlib import Path

import requests

from wei.core.data_classes import Location, Module, Workcell

from .test_base import TestWEI_Base


class Test_Workcell_Base(TestWEI_Base):
    """Tests for WEI Workcell functionality"""

    def test_set_workcell(self):
        """Test that WEI properly loads a workcell"""
        response = requests.post(f"{self.url}/wc/state/reset")
        assert response.status_code == 200

        workcell = Workcell.from_yaml(
            self.root_dir / Path("tests/workcells/test_workcell.yaml")
        )
        response = requests.post(
            f"{self.url}/wc/", json=workcell.model_dump(mode="json")
        )

        assert response.status_code == 200
        assert Workcell.model_validate(response.json())

    def test_workcell_get_state(self):
        """Test that we can get the workcell state"""
        response = requests.post(f"{self.url}/wc/state/reset")
        assert response.status_code == 200

        workcell = Workcell.from_yaml(
            self.root_dir / Path("tests/workcells/test_workcell.yaml")
        )
        requests.post(f"{self.url}/wc/", json=workcell.model_dump(mode="json"))

        response = requests.get(f"{self.url}/wc/state")

        assert response.status_code == 200
        assert isinstance(response.json().get("workcell"), dict)
        assert Workcell.model_validate(response.json().get("workcell"))
        assert isinstance(response.json().get("locations"), dict)
        for location in response.json().get("locations").values():
            assert Location.model_validate(location)
        assert isinstance(response.json().get("modules"), dict)
        for module in response.json().get("modules").values():
            assert Module.model_validate(module)
        assert isinstance(response.json().get("workflows"), dict)
        for wf_run in response.json().get("workflows").values():
            assert Module.model_validate(wf_run)
