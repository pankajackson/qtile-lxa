from pathlib import Path
from typing import Any
from qtile_lxa.widget.widgetbox import WidgetBox, WidgetBoxConfig
from .resources import VagrantVMConfigResources
from .typing_vm_group import VagrantVMGroupConfig


class VagrantVMGroup(WidgetBox):
    def __init__(self, config: VagrantVMGroupConfig, **kwargs: Any):
        super().__init__(**kwargs)
        self.config = config
        self.config = config

        # Root directory where VM-specific folders live
        self.base_dir = Path.home() / ".lxa_vagrant"

        # Folder for this specific VM
        self.vagrant_dir = self.config.vagrant_dir or self.base_dir / self.config.name

        # Data directory inside VM folder (for rendered configs)
        self.data_dir = self.vagrant_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load + render template resources
        self.resources = VagrantVMConfigResources(
            config=config.vm_config, output_dir=self.vagrant_dir
        )
