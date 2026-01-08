from pathlib import Path
from qtile_lxa.widget.multipass import (
    MultipassVM,
    MultipassVMGroup,
    MultipassVMConfig,
    MultipassVMGroupConfig,
    MultipassNetwork,
    MultipassSharedVolume,
    MultipassScript,
    MultipassVMOnlyScript,
)
from ..typing import K8SConfig
from ..resources import K8sResources


def get_master_vm(
    k8s_config: K8SConfig,
    config_dir: Path,
    k8s_resources: K8sResources,
) -> MultipassVM:
    vm = MultipassVM(
        config=MultipassVMConfig(
            instance_name=f"lxa-{k8s_config.cluster_name}-master",
            image=k8s_config.master_image,
            label="M",
            cpus=k8s_config.master_cpus,
            memory=k8s_config.master_memory,
            disk=k8s_config.master_disk,
            network=(
                k8s_config.master_network
                if isinstance(k8s_config.master_network, MultipassNetwork)
                else None
            ),
            shared_volumes=[MultipassSharedVolume(config_dir, Path("/lxa_k8s"))],
            cloud_init_path=k8s_resources.cloud_init_path,
            userdata_script=MultipassVMOnlyScript(k8s_resources.master_userdata_path),
        ),
        update_interval=10,
    )
    return vm


def get_worker_vms(
    k8s_config: K8SConfig,
    config_dir: Path,
    k8s_resources: K8sResources,
    replicas: int,
) -> list[MultipassVM]:

    vm_group = MultipassVMGroup(
        config=MultipassVMGroupConfig(
            name=f"lxa-{k8s_config.cluster_name}-agent",
            instance_config=MultipassVMConfig(
                instance_name=f"lxa-{k8s_config.cluster_name}-agent",
                image=k8s_config.agent_image,
                label="Worker",
                cpus=k8s_config.agent_cpus,
                memory=k8s_config.agent_memory,
                disk=k8s_config.agent_disk,
                network=(
                    k8s_config.agent_network
                    if isinstance(k8s_config.agent_network, MultipassNetwork)
                    else None
                ),
                shared_volumes=[MultipassSharedVolume(config_dir, Path("/lxa_k8s"))],
                cloud_init_path=k8s_resources.cloud_init_path,
                userdata_script=MultipassVMOnlyScript(
                    k8s_resources.agent_userdata_path
                ),
                pre_launch_script=MultipassScript(
                    cmd=(
                        f"echo launching agent... && cp -v {k8s_config.kubeconfig_path} {config_dir/'kubeconfig'}"
                        if k8s_config.worker_only and k8s_config.kubeconfig_path
                        else f"echo launching agent..."
                    )
                ),
                post_launch_script=MultipassScript(
                    k8s_resources.agent_post_start_script_path, inside_vm=True
                ),
                post_start_script=MultipassScript(
                    k8s_resources.agent_post_start_script_path, inside_vm=True
                ),
                pre_delete_script=MultipassScript(
                    k8s_resources.agent_pre_remove_script_path,
                    inside_vm=True,
                    ignore_errors=True,
                ),
                pre_stop_script=MultipassScript(
                    k8s_resources.agent_pre_remove_script_path,
                    inside_vm=True,
                    ignore_errors=True,
                ),
            ),
            replicas=replicas,
            use_short_name=True,
        ),
        update_interval=k8s_config.update_interval,
    )

    return vm_group.get_multipass_vms()
