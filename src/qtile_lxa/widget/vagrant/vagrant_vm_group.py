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

    def short_name(self, vm_name: str, sep: str = "-") -> str:
        parts = vm_name.split(sep)
        if len(parts) == 1:
            return vm_name[0]  # fallback

        # all parts except last → take first letter
        initials = "".join(p[0] for p in parts[:-1] if p)

        # last part → use entire last part (usually "0", "1", etc)
        last = parts[-1]

        return initials + last

    def get_vagrant_vms(self) -> list[VagrantVM]:
        vms = self.vg_cli.get_vm_list()
        if not vms:
            return []
        return [
            VagrantVM(
                config=VagrantVMConfig(
                    name=vm.name,
                    label=(
                        f"{self.short_name(vm.name)}"
                        if self.config.use_short_name
                        else None
                    ),
                    manage_vagrantfile=False,
                    vagrant_dir=self.vagrant_dir,
                    env=self.config.env,
                ),
                update_interval=self.update_interval,
            )
            for vm in vms
        ]
