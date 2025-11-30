import copy
from typing import Any, cast
from libqtile.widget.base import _Widget
from qtile_lxa.widget.widgetbox import WidgetBox, WidgetBoxConfig
from .typing import MultipassVMGroupConfig
from .multipass_vm import MultipassVM


class MultipassVMGroup(WidgetBox):
    def __init__(
        self, config: MultipassVMGroupConfig, update_interval: int = 10, **kwargs: Any
    ):
        self.config = config
        self.update_interval = update_interval

        self.vm_list = cast(list[_Widget], self.get_multipass_vms())
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

    def get_multipass_vms(self) -> list[MultipassVM]:
        return [
            MultipassVM(
                config=copy.deepcopy(self.config.instance_config),
                vm_index=i,
                update_interval=self.update_interval,
            )
            for i in range(self.config.replicas)
        ]
