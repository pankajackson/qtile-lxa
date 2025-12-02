from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import re, string, random
from typing import Any, Literal
from libqtile.log_utils import logger
from qtile_lxa.utils.network import get_default_interface


class VagrantProvider(Enum):
    VIRTUALBOX = "virtualbox"
    LIBVIRT = "libvirt"
    VMWARE = "vmware"


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

    type: VagrantNetworkType
    addresses: list[str] = field(default_factory=list)

    # unified interface for both “bridge” and “dev”
    interface: str | None = get_default_interface()

    # forward struct (safe default)
    forward: VagrantNetworkForward = field(default_factory=VagrantNetworkForward)

    def __post_init__(self):
        t = self.type
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
class VagrantCloudInit:
    content_type: VagrantCloudInitContentType
    path: Path | None = None
    inline: str | None = None
    type: VagrantCloudInitType = VagrantCloudInitType.UserData

    def __post_init__(self):
        if self.path is not None and self.inline is not None:
            raise ValueError("Only one of path and inline can be specified")


@dataclass
class VagrantDisk:
    name: str
    type: Literal["disk", "dvd", "floppy"] = "disk"

    # Options (depending on type)
    size: str | None = None  # Only for type="disk"
    file: str | None = None  # ISO=DVD (required), Disk/Floppy (optional)
    disk_ext: Literal["vdi", "vmdk", "vhd"] | None = None  # Only for disk

    primary: bool = False
    auto_delete: bool = False
    provider_config: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        allowed_types = {"disk", "dvd", "floppy"}
        if self.type not in allowed_types:
            raise ValueError(
                f"Invalid disk type '{self.type}'. Must be one of {allowed_types}"
            )
        if self.type == "disk":
            # Validate size (optional)
            if self.size:
                s = self.size.lower().strip()
                if s.endswith("gb"):
                    self.size_mb = int(s[:-2]) * 1024
                elif s.endswith("mb"):
                    self.size_mb = int(s[:-2])
                elif s.endswith("tb"):
                    self.size_mb = int(s[:-2]) * 1024 * 1024
                else:
                    raise ValueError("Disk size must be like '10GB', '500MB', '1TB'.")

            # Validate disk_ext
            if self.disk_ext and self.disk_ext not in {"vdi", "vmdk", "vhd"}:
                raise ValueError("disk_ext must be one of: 'vdi', 'vmdk', 'vhd'.")

        elif self.type == "dvd":
            if not self.file:
                raise ValueError("DVD type requires `file` pointing to an ISO image.")

            if self.size is not None:
                raise ValueError("DVD does not support `size`.")

            if self.disk_ext is not None:
                raise ValueError("DVD does not support `disk_ext`.")

        elif self.type == "floppy":
            if self.size is not None:
                raise ValueError("Floppy does not support `size`.")

            if self.disk_ext is not None:
                raise ValueError("Floppy does not support `disk_ext`.")

        if not isinstance(self.provider_config, dict):
            raise TypeError("provider_config must be dict[str, Any].")

        for provider, cfg in self.provider_config.items():
            if not isinstance(provider, str):
                raise TypeError(
                    f"Provider name must be string, got {type(provider).__name__}"
                )
            if not isinstance(cfg, dict):
                raise TypeError(
                    f"Provider '{provider}' config must be a dict, got {type(cfg).__name__}"
                )


class VagrantTriggerTiming(Enum):
    BEFORE = "before"
    AFTER = "after"


class VagrantTriggerAction(Enum):
    ALL = "all"
    UP = "up"
    DESTROY = "destroy"
    HALT = "halt"
    PROVISION = "provision"
    RELOAD = "reload"
    RESUME = "resume"
    SUSPEND = "suspend"


class VagrantTriggerType(Enum):
    ACTION = "action"
    COMMAND = "command"
    HOOK = "hook"


class VagrantTriggerOnError(Enum):
    HALT = ":halt"
    CONTINUE = ":continue"


@dataclass
class VagrantTriggerRunConfig:
    """Configuration for code to run on the host (run) or inside guest (run_remote)."""

    inline: str | None = None
    path: Path | None = None
    args: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.inline and not self.path:
            raise ValueError(
                "Trigger run or run_remote requires either `inline` or `path` defined."
            )


@dataclass
class VagrantTrigger:
    # When the trigger should run
    timing: VagrantTriggerTiming
    on_actions: list[VagrantTriggerAction] = field(default_factory=list)
    trigger_type: VagrantTriggerType | None = None

    # Optional constraints / behavior
    ignore: list[str] = field(default_factory=list)
    name: str | None = None
    info: str | None = None  # print message  at the beginning of a trigger
    warn: str | None = None  # print warning message  at the beginning of a trigger
    on_error: VagrantTriggerOnError = VagrantTriggerOnError.CONTINUE
    only_on: list[str] | None = None  # limit only these machines

    # Code to run
    run: VagrantTriggerRunConfig | None = None  # shell command(s)
    run_remote: VagrantTriggerRunConfig | None = None  # guest

    # Ruby callback (rare, advanced)
    # Represent as a string containing Ruby code, or a callable in Python if you map later
    ruby: str | None = None

    def __post_init__(self):
        # Validate actions
        if not self.on_actions:
            raise ValueError(
                "At least one action must be specified for trigger actions."
            )
        # Validate on_error
        if not isinstance(self.on_error, VagrantTriggerOnError):
            raise TypeError("on_error must be VagrantOnError enum")

        # Validate run vs run_remote
        if (
            self.run is None
            and self.run_remote is None
            and self.ruby is None
            and not self.info
            and not self.warn
        ):
            raise ValueError(
                "Trigger must have at least one: run, run_remote, ruby, info or warn"
            )

        # Validate run config objects
        if self.run:
            if not isinstance(self.run, VagrantTriggerRunConfig):
                raise TypeError("run must be a VagrantTriggerRunConfig")
        if self.run_remote:
            if not isinstance(self.run_remote, VagrantTriggerRunConfig):
                raise TypeError("run_remote must be a VagrantTriggerRunConfig")

        # only_on can be str or list
        if self.only_on and not isinstance(self.only_on, (str, list)):
            raise TypeError("only_on must be either a string or list of strings")


@dataclass
class VagrantVMConfig:
    name: str | None = None
    box: str | None = None  # e.g. "bento/ubuntu-22.04"
    box_version: str | None = None  # e.g. "20240215.01"
    hostname: str | None = None

    provider: VagrantProvider = VagrantProvider.VIRTUALBOX

    # Compute resources
    cpus: int | None = None
    memory: int | None = None  # in MB (eg. "2048", "1024")

    # Networking
    networks: list[VagrantNetwork] = field(default_factory=list)

    # Synced folders
    synced_folders: list[VagrantSyncedFolders] = field(default_factory=list)

    # Provisioners
    provisioners: list[VagrantProvisioner] = field(default_factory=list)

    # Cloud-init
    cloud_init: VagrantCloudInit | None = None

    # Additional disks
    disks: list[VagrantDisk] = field(default_factory=list)

    # Triggers
    triggers: list[VagrantTrigger] = field(default_factory=list)

    provider_config: dict[str, Any] = field(default_factory=dict)
    vagrant_dir: Path | None = None

    env: dict[str, Any] = field(default_factory=dict)

    # Status symbols
    running_symbol: str = "🟢"
    partial_running_symbol: str = "🟡"
    poweroff_symbol: str = "🔴"
    stopped_symbol: str = "🛑"
    not_created_symbol: str = "⚪"
    aborted_symbol: str = "⚡"
    saved_symbol: str = "💤"
    frozen_symbol: str = "❄️"
    shutoff_symbol: str = "🔌"
    unknown_symbol: str = "❓"
    error_symbol: str = "❌"

    label: str | None = None
    enable_logger: bool = True
    manage_vagrantfile: bool = True

    def _random_suffix(self, length: int = 4) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def _sanitize_hostname(self, name: str) -> str:
        # Replace unsupported characters with hyphens
        name = re.sub(r"[^A-Za-z0-9.-]", "-", name)

        # Collapse multiple hyphens
        name = re.sub(r"-+", "-", name)

        # Strip leading/trailing hyphens or dots
        name = name.strip("-.")

        # If empty → generate safe hostname with random suffix
        if not name:
            return f"vm-{self._random_suffix()}"

        return name

    def __post_init__(self):
        if not self.vagrant_dir and not self.name:
            raise ValueError(
                "VagrantVMConfig: Either `name` or `vagrant_dir` must be provided."
            )

        if self.vagrant_dir:
            # vagrant_dir
            if self.vagrant_dir and not isinstance(self.vagrant_dir, Path):
                raise TypeError("vagrant_dir must be Path.")
            if not self.vagrant_dir.exists():
                raise FileNotFoundError(
                    f"Vagrant directory {self.vagrant_dir} does not exist."
                )
            if not self.vagrant_dir.is_dir():
                raise TypeError(
                    f"Vagrant directory {self.vagrant_dir} is not a directory."
                )
            if not self.manage_vagrantfile:
                if not (self.vagrant_dir / "Vagrantfile").exists():
                    raise FileNotFoundError(
                        f"Vagrant directory {self.vagrant_dir} does not contain a Vagrantfile."
                    )
                if not (self.vagrant_dir / "Vagrantfile").is_file():
                    raise TypeError(
                        f"Vagrant directory {self.vagrant_dir} does not contain a Vagrantfile."
                    )
                return

        # name validation
        if not self.name:
            raise ValueError("VagrantVMConfig requires a valid VM name.")

        # box validation
        if not self.box or not isinstance(self.box, str):
            raise ValueError("VagrantVMConfig requires a box name (string).")

        # Validate box_version
        if self.box_version is not None:
            if not isinstance(self.box_version, str):
                raise TypeError("box_version must be a string.")

        # Hostname
        if self.hostname is None:
            self.hostname = self._sanitize_hostname(self.name)
        else:
            sanitize_hostname = self._sanitize_hostname(self.hostname)
            if sanitize_hostname != self.hostname:
                logger.warning(
                    f"Invalid hostname '{self.hostname}'. "
                    f"Allowed: letters, digits, hyphens, dots. "
                    f"It cannot start or end with '-' or '.'. "
                    f"using Sanitized valid hostname: '{sanitize_hostname}'."
                )
            self.hostname = sanitize_hostname

        # Provider
        if not isinstance(self.provider, VagrantProvider):
            raise TypeError("provider must be VagrantProvider enum.")

        # CPUS
        if self.cpus is not None and self.cpus <= 0:
            raise ValueError("cpus must be > 0")

        # Memory format
        if self.memory is not None and self.memory <= 0:
            raise ValueError("memory must be > 0")

        # List type validations...
        for net in self.networks:
            if not isinstance(net, VagrantNetwork):
                raise TypeError("All networks must be VagrantNetwork.")

        # Synced folders
        for sf in self.synced_folders:
            if not isinstance(sf, VagrantSyncedFolders):
                raise TypeError("All synced_folders must be VagrantSyncedFolders.")

        # Provisioners
        for p in self.provisioners:
            if not isinstance(p, VagrantProvisioner):
                raise TypeError("All provisioners must be VagrantProvisioner.")

        # Cloud init
        if self.cloud_init and not isinstance(self.cloud_init, VagrantCloudInit):
            raise TypeError("All cloud_init must be VagrantCloudInit.")

        # Disks
        for d in self.disks:
            if not isinstance(d, VagrantDisk):
                raise TypeError("All disks must be VagrantDisk.")

        # Triggers
        for t in self.triggers:
            if not isinstance(t, VagrantTrigger):
                raise TypeError("All triggers must be VagrantTrigger.")

        # provider_config
        if not isinstance(self.provider_config, dict):
            raise TypeError("provider_config must be dict[str, Any].")


@dataclass
class VagrantVMGroupConfig:
    name: str | None = None
    vm_config: VagrantVMConfig | None = None
    replicas: int = 1
    vagrant_dir: Path | None = None
    use_short_name: bool = False
    env: dict[str, Any] = field(default_factory=dict)
    manage_vagrantfile: bool = True

    # WidgetBoxConfig
    widgetbox_close_button_location: Literal["left", "right"] = "left"
    widgetbox_text_closed: str = "  "
    widgetbox_text_open: str = "  "
    widgetbox_timeout: int = 5

    def __post_init__(self):
        if not self.vagrant_dir and not self.name:
            raise ValueError(
                "VagrantVMGroupConfig: Either `name` or `vagrant_dir` must be provided."
            )
        if not self.manage_vagrantfile:
            if self.vagrant_dir:
                # vagrant_dir
                if self.vagrant_dir and not isinstance(self.vagrant_dir, Path):
                    raise TypeError("vagrant_dir must be Path.")
                if not self.vagrant_dir.exists():
                    raise FileNotFoundError(
                        f"Vagrant directory {self.vagrant_dir} does not exist."
                    )
                if not self.vagrant_dir.is_dir():
                    raise TypeError(
                        f"Vagrant directory {self.vagrant_dir} is not a directory."
                    )
                if not (self.vagrant_dir / "Vagrantfile").exists():
                    raise FileNotFoundError(
                        f"Vagrant directory {self.vagrant_dir} does not contain a Vagrantfile."
                    )
                if not (self.vagrant_dir / "Vagrantfile").is_file():
                    raise TypeError(
                        f"Vagrant directory {self.vagrant_dir} does not contain a Vagrantfile."
                    )
            return

        # name validation
        if not self.vm_config:
            raise ValueError("VagrantVMConfig requires a valid VM config.")

        # vagrant_dir
        if self.vagrant_dir:
            if not isinstance(self.vagrant_dir, Path):
                raise TypeError("vagrant_dir must be Path.")
            if not self.vagrant_dir.exists():
                raise FileNotFoundError(
                    f"Vagrant directory {self.vagrant_dir} does not exist."
                )
            if not self.vagrant_dir.is_dir():
                raise TypeError(
                    f"Vagrant directory {self.vagrant_dir} is not a directory."
                )


@dataclass
class VagrantVMStatus:
    name: str
    provider: str
    state: str
    state_short: str
    state_long: str
