from pathlib import Path
from libqtile.widget.base import _Widget
from qtile_lxa.widget.multipass import (
    MultipassVM,
    MultipassVMConfig,
    MultipassNetwork,
    MultipassSharedVolume,
    MultipassScript,
    MultipassVMOnlyScript,
)
from qtile_lxa.widget.vagrant import (
    VagrantProvider,
    VagrantVM,
    VagrantVMConfig,
    VagrantNetwork,
    VagrantSyncedFolders,
    VagrantSyncType,
    VagrantCloudInit,
    VagrantCloudInitType,
    VagrantCloudInitContentType,
    VagrantProvisioner,
    VagrantProvisionerType,
    VagrantShellProvisioner,
)
from qtile_lxa.widget.widgetbox import WidgetBox, WidgetBoxConfig
from typing import Any, cast
from .typing import K8SConfig
from .resources import K8sResources


class K8s(WidgetBox):
    def __init__(self, config: K8SConfig, **kwargs: Any) -> None:
        self.config = config
        self.base_dir = Path.home() / f".lxa_k8s/{self.config.cluster_name}"
        self.data_dir = self.config.data_dir or self.base_dir
        self.config_dir = self.data_dir / "config"
        self.config_vol = MultipassSharedVolume(self.config_dir, Path("/lxa_k8s"))
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

        # ---- Master Node ----
        master_node = None
        if not self.config.worker_only:
            if self.config.plateform == "multipass":
                master_node = MultipassVM(
                    config=MultipassVMConfig(
                        instance_name=f"lxa-{self.config.cluster_name}-master",
                        label="M",
                        cpus=self.config.master_cpus,
                        memory=self.config.master_memory,
                        disk=self.config.master_disk,
                        network=(
                            self.config.master_network
                            if isinstance(self.config.master_network, MultipassNetwork)
                            else None
                        ),
                        shared_volumes=[
                            MultipassSharedVolume(self.config_dir, Path("/lxa_k8s"))
                        ],
                        cloud_init_path=self.resources.cloud_init_path,
                        userdata_script=MultipassVMOnlyScript(
                            self.resources.master_userdata_path
                        ),
                    ),
                    update_interval=10,
                )
            elif self.config.plateform == "virtualbox":
                master_node = VagrantVM(
                    config=VagrantVMConfig(
                        name=f"lxa-{self.config.cluster_name}-master",
                        provider=VagrantProvider.VIRTUALBOX,
                        label="M",
                        cpus=self.config.master_cpus,
                        memory=self.config.master_memory_mb,
                        disk=self.config.master_disk,
                        networks=(
                            [self.config.master_network]
                            if isinstance(self.config.master_network, VagrantNetwork)
                            else []
                        ),
                        synced_folders=[
                            VagrantSyncedFolders(self.config_dir, Path("/lxa_k8s"))
                        ],
                        cloud_init=[
                            VagrantCloudInit(
                                type=VagrantCloudInitType.UserData,
                                content_type=VagrantCloudInitContentType.CloudConfig,
                                path=self.resources.cloud_init_path,
                            )
                        ],
                        provisioners=[
                            VagrantProvisioner(
                                type=VagrantProvisionerType.SHELL,
                                config=VagrantShellProvisioner(
                                    script=self.resources.master_userdata_path,
                                ),
                            )
                        ],
                    ),
                    update_interval=10,
                )
            elif self.config.plateform == "libvirt":
                master_node = VagrantVM(
                    config=VagrantVMConfig(
                        name=f"lxa-{self.config.cluster_name}-master",
                        provider=VagrantProvider.LIBVIRT,
                        label="M",
                        cpus=self.config.master_cpus,
                        memory=self.config.master_memory_mb,
                        disk=self.config.master_disk,
                        networks=(
                            [self.config.master_network]
                            if isinstance(self.config.master_network, VagrantNetwork)
                            else []
                        ),
                        synced_folders=[
                            VagrantSyncedFolders(
                                self.config_dir,
                                Path("/lxa_k8s"),
                                type=VagrantSyncType.NFS,
                                nfs_version=4,
                            )
                        ],
                        cloud_init=[
                            VagrantCloudInit(
                                type=VagrantCloudInitType.UserData,
                                content_type=VagrantCloudInitContentType.CloudConfig,
                                path=self.resources.cloud_init_path,
                            )
                        ],
                        provisioners=[
                            VagrantProvisioner(
                                type=VagrantProvisionerType.SHELL,
                                config=VagrantShellProvisioner(
                                    script=self.resources.master_userdata_path
                                ),
                            )
                        ],
                    ),
                    update_interval=10,
                )

            if master_node:
                nodes.append(master_node)

        # ---- Agent Nodes ----
        agent_nodes = [
            MultipassVM(
                config=MultipassVMConfig(
                    instance_name=f"lxa-{self.config.cluster_name}-agent-{i}",
                    label=f"W{i}",
                    cpus=self.config.agent_cpus,
                    memory=self.config.agent_memory,
                    disk=self.config.agent_disk,
                    network=self.get_agent_network(i),
                    shared_volumes=[self.config_vol],
                    cloud_init_path=self.resources.cloud_init_path,
                    userdata_script=MultipassVMOnlyScript(
                        self.resources.agent_userdata_path
                    ),
                    pre_launch_script=MultipassScript(
                        cmd=(
                            f"echo launching agent {i} && cp -v {self.config.kubeconfig_path} {self.config_dir/'kubeconfig'}"
                            if self.config.worker_only and self.config.kubeconfig_path
                            else f"echo launching agent {i}"
                        )
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

        nodes.extend(agent_nodes)
        return nodes
