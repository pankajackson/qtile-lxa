from pathlib import Path
from libqtile.widget.base import _Widget
from qtile_lxa.widget.multipass import MultipassVM
from qtile_lxa.widget.vagrant import VagrantVM
from qtile_lxa.widget.widgetbox import WidgetBox, WidgetBoxConfig
from typing import Any, cast
from .typing import K8SConfig
from .resources import K8sResources
from .platforms import virtualbox, libvirt, multipass


class K8s(WidgetBox):
    def __init__(self, config: K8SConfig, **kwargs: Any) -> None:
        self.config = config
        self.base_dir = Path.home() / f".lxa_k8s/{self.config.cluster_name}"
        self.data_dir = self.config.data_dir or self.base_dir
        self.config_dir = self.data_dir / "config"
        self.resources = K8sResources(self.config, self.config_dir)

        self.node_list = cast(list[_Widget], self.get_node_list())

        super().__init__(
            config=WidgetBoxConfig(
                name=self.config.cluster_name,
                widgets=self.node_list,
                close_button_location=self.config.widgetbox_close_button_location,
                text_closed=self.config.widgetbox_text_closed,
                text_open=self.config.widgetbox_text_open,
                timeout=self.config.widgetbox_timeout,
                **kwargs,
            )
        )

    def get_node_list(self) -> list[MultipassVM | VagrantVM]:
        nodes: list[MultipassVM | VagrantVM] = []

        match self.config.platform:
            case "multipass":
                master_node = multipass.get_master_vm(
                    config_dir=self.config_dir,
                    k8s_config=self.config,
                    k8s_resources=self.resources,
                )
                agent_nodes = multipass.get_worker_vms(
                    config_dir=self.config_dir,
                    k8s_config=self.config,
                    k8s_resources=self.resources,
                    replicas=self.config.agent_count,
                )
            case "virtualbox":
                master_node = virtualbox.get_master_vm(
                    config_dir=self.config_dir,
                    k8s_config=self.config,
                    k8s_resources=self.resources,
                )
                agent_nodes = virtualbox.get_worker_vms(
                    config_dir=self.config_dir,
                    k8s_config=self.config,
                    k8s_resources=self.resources,
                    replicas=self.config.agent_count,
                )
            case "libvirt":
                master_node = libvirt.get_master_vm(
                    config_dir=self.config_dir,
                    k8s_config=self.config,
                    k8s_resources=self.resources,
                )
                agent_nodes = libvirt.get_worker_vms(
                    config_dir=self.config_dir,
                    k8s_config=self.config,
                    k8s_resources=self.resources,
                    replicas=self.config.agent_count,
                )
        if not self.config.worker_only:
            nodes.append(master_node)
        nodes.extend(agent_nodes)

        return nodes
