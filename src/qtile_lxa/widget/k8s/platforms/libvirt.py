from pathlib import Path
from qtile_lxa.widget.vagrant import (
    VagrantVM,
    VagrantVMConfig,
    VagrantVMGroup,
    VagrantVMGroupConfig,
    VagrantProvider,
    VagrantNetwork,
    VagrantDisk,
    VagrantSyncedFolders,
    VagrantSyncType,
    VagrantCloudInit,
    VagrantCloudInitType,
    VagrantCloudInitContentType,
    VagrantProvisioner,
    VagrantProvisionerType,
    VagrantShellProvisioner,
    VagrantTrigger,
    VagrantTriggerTiming,
    VagrantTriggerAction,
    VagrantTriggerType,
    VagrantTriggerRunConfig,
    VagrantTriggerOnError,
)
from ..typing import K8SConfig
from ..resources import K8sResources
from .common import validate_size_mb


def get_master_vm(
    k8s_config: K8SConfig,
    config_dir: Path,
    k8s_resources: K8sResources,
) -> VagrantVM:
    vm = VagrantVM(
        config=VagrantVMConfig(
            name=f"lxa-{k8s_config.cluster_name}-master",
            box=k8s_config.master_image or "generic/ubuntu2004",
            provider=VagrantProvider.LIBVIRT,
            label="M",
            cpus=k8s_config.master_cpus,
            memory=(
                validate_size_mb(k8s_config.master_memory)
                if k8s_config.master_memory
                else None
            ),
            disks=(
                [
                    VagrantDisk(
                        name="root-disk",
                        type="disk",
                        size=k8s_config.master_disk,
                    )
                ]
                if k8s_config.master_disk
                else []
            ),
            networks=(
                [k8s_config.master_network]
                if isinstance(k8s_config.master_network, VagrantNetwork)
                else []
            ),
            synced_folders=[
                VagrantSyncedFolders(
                    config_dir,
                    Path("/lxa_k8s"),
                    type=VagrantSyncType.NFS,
                    nfs_version=4,
                )
            ],
            cloud_init=VagrantCloudInit(
                type=VagrantCloudInitType.UserData,
                content_type=VagrantCloudInitContentType.CloudConfig,
                path=k8s_resources.cloud_init_path,
            ),
            provisioners=[
                VagrantProvisioner(
                    type=VagrantProvisionerType.SHELL,
                    config=VagrantShellProvisioner(
                        script=k8s_resources.master_userdata_path,
                    ),
                )
            ],
        ),
        update_interval=10,
    )
    return vm


def get_worker_vms(
    k8s_config: K8SConfig,
    config_dir: Path,
    k8s_resources: K8sResources,
    replicas: int,
) -> list[VagrantVM]:

    vm_group = VagrantVMGroup(
        config=VagrantVMGroupConfig(
            name=f"lxa-{k8s_config.cluster_name}-agent",
            vm_config=VagrantVMConfig(
                name=f"lxa-{k8s_config.cluster_name}-agent",
                box=k8s_config.agent_image or "generic/ubuntu2004",
                label="Worker",
                provider=VagrantProvider.LIBVIRT,
                cpus=k8s_config.agent_cpus,
                memory=(
                    validate_size_mb(k8s_config.agent_memory)
                    if k8s_config.agent_memory
                    else None
                ),
                disks=(
                    [
                        VagrantDisk(
                            name="root-disk",
                            type="disk",
                            size=k8s_config.agent_disk,
                        )
                    ]
                    if k8s_config.agent_disk
                    else []
                ),
                networks=(
                    [k8s_config.agent_network]
                    if isinstance(k8s_config.agent_network, VagrantNetwork)
                    else []
                ),
                synced_folders=[
                    VagrantSyncedFolders(
                        config_dir,
                        Path("/lxa_k8s"),
                        type=VagrantSyncType.NFS,
                        nfs_version=4,
                    )
                ],
                cloud_init=VagrantCloudInit(
                    type=VagrantCloudInitType.UserData,
                    content_type=VagrantCloudInitContentType.CloudConfig,
                    path=k8s_resources.cloud_init_path,
                ),
                provisioners=[
                    VagrantProvisioner(
                        type=VagrantProvisionerType.SHELL,
                        config=VagrantShellProvisioner(
                            script=k8s_resources.agent_userdata_path,
                        ),
                    )
                ],
                triggers=[
                    VagrantTrigger(
                        timing=VagrantTriggerTiming.BEFORE,
                        on_actions=[VagrantTriggerAction.UP],
                        trigger_type=VagrantTriggerType.HOOK,
                        run=VagrantTriggerRunConfig(
                            inline=(
                                f"echo launching agent... && cp -v {k8s_config.kubeconfig_path} {config_dir/'kubeconfig'}"
                                if k8s_config.worker_only and k8s_config.kubeconfig_path
                                else f"echo launching agent..."
                            ),
                        ),
                        on_error=VagrantTriggerOnError.HALT,
                    )
                ],
            ),
            replicas=replicas,
            use_short_name=True,
        ),
        update_interval=k8s_config.update_interval,
    )

    return vm_group.get_vagrant_vms()
