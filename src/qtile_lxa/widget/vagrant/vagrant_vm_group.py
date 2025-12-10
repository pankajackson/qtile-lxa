from typing import Any, cast
from libqtile.widget.base import _Widget
from qtile_lxa.widget.widgetbox import WidgetBox, WidgetBoxConfig
from .resources import VagrantVMConfigResources
from .typing import VagrantVMConfig, VagrantVMGroupConfig
from .vagrant_vm import VagrantVM
from .runner import VagrantCLI


class VagrantVMGroup(WidgetBox):
    def __init__(
        self, config: VagrantVMGroupConfig, update_interval: int = 10, **kwargs: Any
    ):
        self.config = config
        self.update_interval = update_interval
        self.resources = VagrantVMConfigResources(
            config=config,
            skip_vagrantfile_generation=not config.manage_vagrantfile,
        )
        self.vagrant_dir = self.resources.vagrant_dir
        self.vg_cli = VagrantCLI(self.vagrant_dir, env=config.env)

        self.vm_list = cast(list[_Widget], self.get_vagrant_vms())
        super().__init__(
            config=WidgetBoxConfig(
                name=self.config.name,
                widgets=self.vm_list,
                close_button_location=self.config.widgetbox_close_button_location,
                text_closed=self.config.widgetbox_text_closed,
                text_open=self.config.widgetbox_text_open,
                timeout=self.config.widgetbox_timeout,
                **kwargs,
            )
        )

    def get_short_name(self, name: str, sep: str = "-") -> str:
        parts = name.split(sep)
        if len(parts) == 1:
            return name[0]

        # all parts except last → take first letter
        initials = "".join(p[0] for p in parts[:-1] if p)

        # last part → use entire last part (usually "0", "1", etc)
        last = parts[-1]

        return f"{initials}{last}"

    def get_node_label(
        self,
        vm_name: str,
        label: str,
        sep: str = "-",
    ) -> str:
        parts = vm_name.split(sep)
        if len(parts) == 1:
            return label
        return f"{label}{sep}{parts[-1]}"

    def get_label(
        self, vm_name: str, label: str | None, sep: str = "-", short_name: bool = False
    ) -> str | None:
        if not short_name and label is None:
            return None
        name = (
            self.get_node_label(vm_name=vm_name, label=label, sep=sep)
            if label
            else vm_name
        )
        if short_name:
            name = self.get_short_name(name=name)
        return name

    def get_vagrant_vms(self) -> list[VagrantVM]:
        vms = self.vg_cli.get_sync_status()
        if not vms or self.config.replicas <= 0:
            return []
        return [
            VagrantVM(
                config=VagrantVMConfig(
                    name=vm.name,
                    label=self.get_label(
                        vm_name=vm.name,
                        label=(
                            self.config.vm_config.label
                            if self.config.vm_config
                            else None
                        ),
                        sep="-",
                        short_name=self.config.use_short_name,
                    ),
                    manage_vagrantfile=False,
                    vagrant_dir=self.vagrant_dir,
                    env=self.config.env,
                ),
                update_interval=self.update_interval,
            )
            for vm in vms
        ]
