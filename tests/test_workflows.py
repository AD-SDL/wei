"""Tests WEI workflow functionality"""


from .test_base import TestWEI_Base


class TestWEI_Workflows(TestWEI_Base):
    """Tests WEI location management"""

    def test_workflow_run(self):
        """Test Running a simple workflow"""
        from pathlib import Path

        workflow_path = Path(__file__).parent / "workflows" / "test_workflow.yaml"

        print(
            self.experiment.start_run(
                workflow_file=workflow_path,
                payload={"wait_time": 5},
                blocking=True,
                simulate=False,
            )
        )
