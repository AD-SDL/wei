"""Tests WEI data management"""

import filecmp

from wei.types.datapoint_types import LocalFileDataPoint, ValueDataPoint

from .test_base import TestWEI_Base


class TestWEI_Workflows(TestWEI_Base):
    """Tests WEI location management"""

    def test_create_value_datapoint(self):
        """Test creating and uploading a value datapoint"""

        datapoint = ValueDataPoint(label="test_data_label", value=42)
        self.experiment_client.create_datapoint(datapoint)

        assert self.experiment_client.get_datapoint_value(datapoint.id)["value"] == 42
        uploaded_datapoint = self.experiment_client.get_datapoint_info(datapoint.id)
        assert uploaded_datapoint.label == "test_data_label"
        assert uploaded_datapoint.value == 42
        assert uploaded_datapoint.type == "data_value"
        assert uploaded_datapoint.id == datapoint.id
        assert (
            uploaded_datapoint.experiment_id
            == self.experiment_client.experiment.experiment_id
        )
        assert (
            uploaded_datapoint.campaign_id
            == self.experiment_client.experiment.campaign_id
        )

    def test_create_local_file_datapoint(self):
        """Test creating and uploading a local file datapoint"""

        datapoint = LocalFileDataPoint(label="test_file_label", path=__file__)
        self.experiment_client.create_datapoint(datapoint)
        assert isinstance(
            self.experiment_client.get_datapoint_value(datapoint.id), bytes
        )
        uploaded_datapoint = self.experiment_client.get_datapoint_info(datapoint.id)
        assert uploaded_datapoint.label == "test_file_label"
        assert uploaded_datapoint.type == "local_file"
        assert uploaded_datapoint.id == datapoint.id
        assert (
            uploaded_datapoint.experiment_id
            == self.experiment_client.experiment.experiment_id
        )
        assert (
            uploaded_datapoint.campaign_id
            == self.experiment_client.experiment.campaign_id
        )
        self.experiment_client.save_datapoint_value(datapoint.id, "download.py")
        assert filecmp.cmp(__file__, "download.py")
