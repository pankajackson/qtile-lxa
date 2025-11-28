from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from .typing_vm import VagrantVMConfig


@dataclass
class VagrantVMGroupConfig:
    name: str
    vm_config: VagrantVMConfig
    replicas: int = 1
    vagrant_dir: Path | None = None
    use_short_name: bool = False

    # WidgetBoxConfig
    widgetbox_close_button_location: Literal["left", "right"] = "left"
    widgetbox_text_closed: str = "  "
    widgetbox_text_open: str = "  "
    widgetbox_timeout: int = 5
