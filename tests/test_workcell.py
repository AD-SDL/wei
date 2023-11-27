"""Tests for WEI Workcell functionality"""

from pathlib import Path

from fastapi.testclient import TestClient

from wei.core.data_classes import Location, Module, WorkcellData

from .test_base import TestWEI_Base


class Test_Workcell_Base(TestWEI_Base):
    """Tests for WEI Workcell functionality"""

    def test_set_workcell(self):
        """Test that WEI properly loads a workcell"""
        with TestClient(self.app) as client:
            response = client.post("/wc/state/clear")
            assert response.status_code == 200

            workcell = WorkcellData.from_yaml(Path("tests/test_workcell.yaml"))
            response = client.post("/wc/", json=workcell.model_dump(mode="json"))

            assert response.status_code == 200
            assert WorkcellData.model_validate(response.json())

    def test_workcell_get_state(self):
        """Test that we can get the workcell state"""
        with TestClient(self.app) as client:
            response = client.post("/wc/state/clear")
            assert response.status_code == 200

            response = client.get("/wc/state")

            assert response.status_code == 200
            assert isinstance(response.json().get("workcell"), dict)
            assert response.json().get("workcell") == {}
            assert isinstance(response.json().get("locations"), dict)
            assert response.json().get("locations") == {}
            assert isinstance(response.json().get("modules"), dict)
            assert response.json().get("modules") == {}
            assert isinstance(response.json().get("workflows"), dict)
            assert response.json().get("workflows") == {}

            workcell = WorkcellData.from_yaml(Path("tests/test_workcell.yaml"))
            client.post("/wc/", json=workcell.model_dump(mode="json"))

            response = client.get("/wc/state")

            assert response.status_code == 200
            assert isinstance(response.json().get("workcell"), dict)
            assert WorkcellData.model_validate(response.json().get("workcell"))
            assert isinstance(response.json().get("locations"), dict)
            for location in response.json().get("locations").values():
                assert Location.model_validate(location)
            assert isinstance(response.json().get("modules"), dict)
            for module in response.json().get("modules").values():
                assert Module.model_validate(module)
            assert isinstance(response.json().get("workflows"), dict)
            for wf_run in response.json().get("workflows").values():
                assert Module.model_validate(wf_run)
