from typing import Any, cast
from libqtile.widget.base import _Widget
from qtile_lxa.widget.widgetbox import WidgetBox, WidgetBoxConfig
from .resources import VagrantVMConfigResources
from .typing_vm_group import VagrantVMGroupConfig
from .vagrant_vm import VagrantVM
from .typing_vm import VagrantVMConfig
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

    def get_vagrant_vms(self) -> list[VagrantVM]:
        runner = VagrantCLI(self.vagrant_dir)
        vms = runner.get_vm_list()
        if not vms:
            return []
        return [
            VagrantVM(
                config=VagrantVMConfig(
                    name=vm.name,
                    label=(
                        f"{vm.name[0]}{vm.name[-1]}"
                        if self.config.use_short_name
                        else None
                    ),
                    manage_vagrantfile=False,
                    vagrant_dir=self.vagrant_dir,
                ),
                update_interval=self.update_interval,
            )
            for vm in vms
        ]
