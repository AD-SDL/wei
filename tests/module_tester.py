"""for testing modules without a workcell"""

from typing import Any

from wei.core.interfaces.rest_interface import RestInterface
from wei.types.module_types import Module
from wei.types.step_types import Step


def test_module(action: str, args: Any, url: str):
    """tests the module action"""
    mod = Module(
        name="test", interface="wei_rest_node", config={"rest_node_address": url}
    )
    step = Step(name="test", module="test", action=action, args=args)
    RestInterface.send_action(step, mod, run_dir=".")
