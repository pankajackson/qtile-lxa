from pathlib import Path
from libqtile.widget.base import _Widget
from qtile_lxa import __ASSETS_DIR__
from qtile_lxa.widget.multipass import (
    MultipassVM,
    MultipassConfig,
    MultipassNetwork,
    MultipassSharedVolume,
    MultipassScript,
    MultipassVMOnlyScript,
)
from qtile_lxa.widget.widgetbox import WidgetBox, WidgetBoxConfig
from typing import Any, cast
from .typing import K8SConfig
from .resources import K8sResources


class K8s(WidgetBox):
    def __init__(self, config: K8SConfig, **kwargs: Any) -> None:
        self.config = config
        self.assets_dir = __ASSETS_DIR__ / "k8s"
        self.base_dir = Path.home() / f".lxa_k8s/{self.config.cluster_name}"
        self.data_dir = self.config.data_dir or self.base_dir
        self.master_data_dir = self.data_dir / "master"
        self.worker_data_dir = self.data_dir / "worker"
        self.common_data_dir = self.data_dir / "common"
        self.resources = K8sResources(self.config, self.data_dir)

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

    def get_master_network(self) -> MultipassNetwork | None:
        if not self.config.network:
            return

        config = {
            "adapter": self.config.network.adapter,
            "multipass_network": self.config.network.network,  # make sure key matches dataclass
            "addresses": [self.config.network.master_ip()],  # wrap in list
        }
        return MultipassNetwork(**config)

    def get_agent_network(self, count: int) -> MultipassNetwork | None:
        if not self.config.network:
            return
        agent_ips = self.config.network.agent_ips(count=self.config.agent_count)

        config = {
            "adapter": self.config.network.adapter,
            "multipass_network": self.config.network.network,  # make sure key matches dataclass
            "addresses": [agent_ips[count]],  # wrap in list
        }
        return MultipassNetwork(**config)

    def get_node_list(self) -> list[MultipassVM]:
        master_node = MultipassVM(
            config=MultipassConfig(
                instance_name=f"lxa-{self.config.cluster_name}-master",
                label="M",
                cpus=self.config.master_cpus,
                memory=self.config.master_memory,
                disk=self.config.master_disk,
                network=self.get_master_network(),
                shared_volumes=[
                    MultipassSharedVolume(self.master_data_dir, Path("/data")),
                    MultipassSharedVolume(self.common_data_dir, Path("/common")),
                ],
                userdata_script=MultipassVMOnlyScript(
                    self.resources.master_userdata_path
                ),
            ),
            update_interval=10,
        )

        agent_nodes = [
            MultipassVM(
                config=MultipassConfig(
                    instance_name=f"lxa-{self.config.cluster_name}-agent-{i}",
                    label=f"W{i}",
                    cpus=self.config.agent_cpus,
                    memory=self.config.agent_memory,
                    disk=self.config.agent_disk,
                    network=self.get_agent_network(i),
                    shared_volumes=[
                        MultipassSharedVolume(self.worker_data_dir, Path("/data")),
                        MultipassSharedVolume(self.common_data_dir, Path("/common")),
                    ],
                    userdata_script=MultipassVMOnlyScript(
                        self.resources.agent_userdata_path
                    ),
                    post_launch_script=MultipassScript(
                        self.resources.agent_post_start_script_path, inside_vm=True
                    ),
                    post_start_script=MultipassScript(
                        self.resources.agent_post_start_script_path, inside_vm=True
                    ),
                    pre_delete_script=MultipassScript(
                        self.resources.agent_pre_remove_script_path,
                        inside_vm=True,
                        ignore_errors=True,
                    ),
                    pre_stop_script=MultipassScript(
                        self.resources.agent_pre_remove_script_path,
                        inside_vm=True,
                        ignore_errors=True,
                    ),
                ),
                update_interval=10,
            )
            for i in range(self.config.agent_count)
        ]
        return [master_node] + agent_nodes
