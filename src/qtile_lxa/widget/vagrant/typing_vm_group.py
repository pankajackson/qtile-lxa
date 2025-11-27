from dataclasses import dataclass
from pathlib import Path
from .typing_vm import VagrantVMConfig


@dataclass
class VagrantVMGroupConfig:
    name: str
    vm_config: VagrantVMConfig
    replicas: int
    vagrant_dir: Path | None = None
