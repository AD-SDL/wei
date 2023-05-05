from pathlib import Path

from rpl_wei.core.workcell import Workcell


class WEI:
    def __init__(
        self,
        workcell_path: Path,
    ) -> None:
        self.workcell = Workcell(workcell_path)
