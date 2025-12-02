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

    def get_short_name(self, name: str, sep: str = "-") -> str:
        parts = name.split(sep)
        short_name = "".join(p[0] for p in parts if p)
        return short_name

    def get_label(
        self, vm_name: str, label: str | None, short_name: bool = False
    ) -> str | None:
        if not short_name and label is None:
            return None
        name = label if label else vm_name
        if short_name:
            name = self.get_short_name(name=name)
        return name

    def get_multipass_vms(self) -> list[MultipassVM]:
        vms: list[MultipassVM] = []
        for i in range(self.config.replicas):
            cfg = copy.deepcopy(self.config.instance_config)

            cfg.label = self.get_label(
                vm_name=cfg.instance_name,
                label=cfg.label,
                short_name=self.config.use_short_name,
            )

            vms.append(
                MultipassVM(
                    config=cfg,
                    vm_index=i,
                    update_interval=self.update_interval,
                )
            )

        return vms
