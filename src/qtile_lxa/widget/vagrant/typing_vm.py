from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

from dataclasses import dataclass, field
from enum import Enum


class VagrantProvider(Enum):
    Virtualbox = "virtualbox"
    Libvirt = "libvirt"
    Vmware = "vmware"


class VagrantNetworkType(Enum):
    PRIVATE = "private_network"
    PUBLIC = "public_network"
    FORWARDED = "forwarded_port"


class PortProtocol(Enum):
    TCP = "tcp"
    UDP = "udp"


@dataclass
class VagrantNetworkForward:
    guest_port: int = 0
    host_port: int = 0
    protocol: PortProtocol = PortProtocol.TCP

    def is_enabled(self) -> bool:
        """Return True only if forwarding is actually configured."""
        return self.guest_port > 0 and self.host_port > 0


@dataclass
class VagrantNetwork:
    """Vagrant network configuration with a unified 'interface' key."""

    vagrant_network: VagrantNetworkType
    addresses: list[str] = field(default_factory=list)

    # unified interface for both “bridge” and “dev”
    interface: str | None = None

    # forward struct (safe default)
    forward: VagrantNetworkForward = field(default_factory=VagrantNetworkForward)

    def __post_init__(self):
        t = self.vagrant_network
        forwarding_enabled = self.forward.is_enabled()

        # ---- PRIVATE NETWORK ----
        if t == VagrantNetworkType.PRIVATE:
            if self.interface:
                raise ValueError("PRIVATE network cannot use 'interface'.")

            if forwarding_enabled:
                raise ValueError("PRIVATE network cannot define forwarded ports.")

        # ---- PUBLIC NETWORK ----
        elif t == VagrantNetworkType.PUBLIC:
            if not self.interface:
                raise ValueError("PUBLIC network requires 'interface' (bridge/dev).")

            if forwarding_enabled:
                raise ValueError("PUBLIC network cannot define forwarded ports.")

        # ---- FORWARDED PORT ----
        elif t == VagrantNetworkType.FORWARDED:
            if not forwarding_enabled:
                raise ValueError("FORWARDED requires guest_port and host_port > 0.")

            if self.addresses:
                raise ValueError("FORWARDED cannot define static IPs.")

            if self.interface:
                raise ValueError("FORWARDED cannot use 'interface'.")


class VagrantSyncType(Enum):
    VIRTUALBOX = "virtualbox"  # Vagrant's default mechanism
    RSYNC = "rsync"
    SMB = "smb"  # Windows hosts only
    NFS = "nfs"
    NINE_P = "9p"  # Special for Libvirt
    VMWARE = "vmware"  # VMware-specific


@dataclass
class VagrantSyncedFolders:
    source_path: Path
    target_path: Path

    # Sync type
    type: VagrantSyncType = VagrantSyncType.VIRTUALBOX

    # Common options
    create: bool = True
    owner: str | None = None
    group: str | None = None
    disabled: bool = False
    mount_options: list[str] = field(default_factory=list)

    # Provider-specific options
    smb_username: str | None = None
    smb_password: str | None = None

    nfs_version: int | None = None
    nfs_udp: bool | None = None

    ninep_accessmode: str | None = None  # "mapped", "passthrough", "squash"
    ninep_readonly: bool | None = None
    ninep_mount_tag: str | None = None

    # Rsync specific
    rsync_exclude: list[str] = field(default_factory=list)
    rsync_args: list[str] = field(default_factory=list)
    rsync_auto: bool = True

    def __post_init__(self):

        # SMB requires username + password
        if self.type == VagrantSyncType.SMB:
            if not (self.smb_username and self.smb_password):
                raise ValueError(
                    "SMB synced folder requires smb_username and smb_password."
                )

        # NFS options must be valid
        if self.type == VagrantSyncType.NFS:
            if self.nfs_version not in (None, 3, 4):
                raise ValueError("NFS sync supports only versions 3 or 4.")

        # 9p options (libvirt)
        if self.type == VagrantSyncType.NINE_P:
            if self.ninep_accessmode not in (None, "mapped", "passthrough", "squash"):
                raise ValueError(
                    "9p accessmode must be 'mapped', 'passthrough', or 'squash'."
                )

        # Rsync only options
        if self.type != VagrantSyncType.RSYNC:
            if self.rsync_exclude or self.rsync_args:
                raise ValueError(
                    "rsync_exclude and rsync_args allowed only for RSYNC type."
                )


class VagrantProvisionerType(Enum):
    SHELL = "shell"
    FILE = "file"
    ANSIBLE = "ansible"
    ANSIBLE_LOCAL = "ansible_local"
    CHEF_SOLO = "chef_solo"
    CHEF_ZERO = "chef_zero"
    PUPPET = "puppet"
    PUPPET_SERVER = "puppet_server"
    SALT = "salt"
    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"


@dataclass
class VagrantShellProvisioner:
    inline: str | None = None
    script: Path | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    privileged: bool = True

    def __post_init__(self):
        if not self.inline and not self.script:
            raise ValueError("Shell provisioner requires either 'inline' or 'script'.")

        if self.script and not isinstance(self.script, Path):
            raise TypeError("script must be Path.")

        if self.inline and self.script:
            raise ValueError("Use either 'inline' OR 'script', not both.")


@dataclass
class VagrantFileProvisioner:
    source: Path
    destination: Path

    def __post_init__(self):
        if not isinstance(self.source, Path):
            raise TypeError("source must be Path.")

        if not isinstance(self.destination, Path):
            raise TypeError("destination must be Path.")


@dataclass
class VagrantAnsibleCommon:
    playbook: Path
    become: bool = False
    become_user: str = "root"
    compatibility_mode: str = "auto"  # "auto", "2.0", "1.8"
    config_file: Path | None = None
    extra_vars: dict = field(default_factory=dict)
    inventory_path: Path | None = None
    limit: str = "all"
    tags: list[str] = field(default_factory=list)
    skip_tags: list[str] = field(default_factory=list)
    vault_password_file: Path | None = None


@dataclass
class VagrantAnsibleProvisioner(VagrantAnsibleCommon):
    ask_become_pass: bool = False
    ask_sudo_pass: bool = False
    force_remote_user: bool = True
    host_key_checking: bool = False
    raw_ssh_args: list[str] = field(default_factory=list)  # eg: ['-o ControlMaster=no']

    def __post_init__(self):
        if not isinstance(self.playbook, Path):
            raise TypeError("playbook must be Path.")

        if self.inventory_path and not isinstance(self.inventory_path, Path):
            raise TypeError("inventory_path must be Path.")


class VagrantAnsibleLocalInstallMode(Enum):
    Default = "default"
    Pip = "pip"
    PipArgsOnly = "pip_args_only"


@dataclass
class VagrantAnsibleLocalProvisioner(VagrantAnsibleCommon):
    install: bool = True
    install_mode: VagrantAnsibleLocalInstallMode = (
        VagrantAnsibleLocalInstallMode.Default
    )
    pip_args: str | None = None
    provisioning_path: Path = Path("/vagrant")
    tmp_path: Path = Path("/tmp/vagrant-ansible")

    def __post_init__(self):
        if not isinstance(self.playbook, Path):
            raise TypeError("playbook must be Path.")


VagrantProvisionerConfig = (
    VagrantShellProvisioner
    | VagrantFileProvisioner
    | VagrantAnsibleProvisioner
    | VagrantAnsibleLocalProvisioner
)


@dataclass
class VagrantProvisioner:
    type: VagrantProvisionerType
    config: VagrantProvisionerConfig

    # supported provisioners mapping
    _mapping = {
        VagrantProvisionerType.SHELL: VagrantShellProvisioner,
        VagrantProvisionerType.FILE: VagrantFileProvisioner,
        VagrantProvisionerType.ANSIBLE: VagrantAnsibleProvisioner,
        VagrantProvisionerType.ANSIBLE_LOCAL: VagrantAnsibleLocalProvisioner,
    }

    def __post_init__(self):
        # reject unsupported provisioner types
        if self.type not in self._mapping:
            supported = ", ".join(t.value for t in self._mapping.keys())
            raise ValueError(
                f"Provisioner '{self.type.value}' is not supported. "
                f"Supported types: {supported}"
            )

        # validate config class
        expected_cls = self._mapping[self.type]
        if not isinstance(self.config, expected_cls):
            raise TypeError(
                f"Provisioner '{self.type.value}' expects config "
                f"{expected_cls.__name__}, got {type(self.config).__name__}"
            )


class VagrantCloudInitContentType(Enum):
    CloudBootHook = "text/cloud-boothook"
    CloudConfig = "text/cloud-config"
    CloudConfigArchive = "text/cloud-config-archive"
    Jinja2 = "text/jinja2"
    PartHandler = "text/part-handler"
    UpstartJob = "text/upstart-job"
    XIncludeOnceUrl = "text/x-include-once-url"
    XIncludeUrl = "text/x-include-url"
    XShellScript = "text/x-shellscript"


class VagrantCloudInitType(Enum):
    UserData = ":user_data"


@dataclass
class VagrantCloudInitConfig:
    content_type: VagrantCloudInitContentType
    path: Path | None = None
    inline: str | None = None
    type: VagrantCloudInitType = VagrantCloudInitType.UserData

    def __post_init__(self):
        if self.path is not None and self.inline is not None:
            raise ValueError("Only one of path and inline can be specified")


@dataclass(frozen=True)
class MultipassConfig:
    instance_name: str
    cloud_init_path: Path | None = None
    image: str | None = None
    cpus: int | None = None  # default 1
    memory: str | None = None  # default "1G"
    disk: str | None = None  # default "5G"
    network: MultipassNetwork | None = None
    shared_volumes: list[MultipassSharedVolume] = field(default_factory=list)
    userdata_script: MultipassVMOnlyScript | None = None
    pre_launch_script: MultipassScript | None = None
    post_launch_script: MultipassScript | None = None
    pre_start_script: MultipassScript | None = None
    post_start_script: MultipassScript | None = None
    pre_stop_script: MultipassScript | None = None
    post_stop_script: MultipassScript | None = None
    pre_delete_script: MultipassScript | None = None
    post_delete_script: MultipassScript | None = None
    label: str | None = None
    not_created_symbol: str = "⚪"
    running_symbol: str = "🟢"
    stopped_symbol: str = "🔴"
    deleted_symbol: str = "🗑️"
    starting_symbol: str = "🟡"
    restarting_symbol: str = "🔄"
    delayed_shutdown_symbol: str = "🛑"
    suspending_symbol: str = "⏱️"
    suspended_symbol: str = "❄️"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"
    enable_logger: bool = False
