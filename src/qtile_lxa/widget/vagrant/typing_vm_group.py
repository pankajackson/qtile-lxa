from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from .typing_vm import VagrantVMConfig


@dataclass
class VagrantVMGroupConfig:
    name: str | None = None
    vm_config: VagrantVMConfig | None = None
    replicas: int = 1
    vagrant_dir: Path | None = None
    use_short_name: bool = False
    skip_vagrantfile: bool = False

    # WidgetBoxConfig
    widgetbox_close_button_location: Literal["left", "right"] = "left"
    widgetbox_text_closed: str = "  "
    widgetbox_text_open: str = "  "
    widgetbox_timeout: int = 5

    def __post_init__(self):
        if not self.vagrant_dir and not self.name:
            raise ValueError(
                "VagrantVMGroupConfig: Either `name` or `vagrant_dir` must be provided."
            )
        if self.skip_vagrantfile:
            if self.vagrant_dir:
                # vagrant_dir
                if self.vagrant_dir and not isinstance(self.vagrant_dir, Path):
                    raise TypeError("vagrant_dir must be Path.")
                if not self.vagrant_dir.exists():
                    raise FileNotFoundError(
                        f"Vagrant directory {self.vagrant_dir} does not exist."
                    )
                if not self.vagrant_dir.is_dir():
                    raise TypeError(
                        f"Vagrant directory {self.vagrant_dir} is not a directory."
                    )
                if not (self.vagrant_dir / "Vagrantfile").exists():
                    raise FileNotFoundError(
                        f"Vagrant directory {self.vagrant_dir} does not contain a Vagrantfile."
                    )
                if not (self.vagrant_dir / "Vagrantfile").is_file():
                    raise TypeError(
                        f"Vagrant directory {self.vagrant_dir} does not contain a Vagrantfile."
                    )
            return

        # name validation
        if not self.vm_config:
            raise ValueError("VagrantVMConfig requires a valid VM config.")

        # vagrant_dir
        if self.vagrant_dir:
            if not isinstance(self.vagrant_dir, Path):
                raise TypeError("vagrant_dir must be Path.")
            if not self.vagrant_dir.exists():
                raise FileNotFoundError(
                    f"Vagrant directory {self.vagrant_dir} does not exist."
                )
            if not self.vagrant_dir.is_dir():
                raise TypeError(
                    f"Vagrant directory {self.vagrant_dir} is not a directory."
                )
