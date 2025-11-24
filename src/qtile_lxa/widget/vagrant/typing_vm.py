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
class VagrantSharedVolume:
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


@dataclass
class VagrantScript:
    path: Path | None = None
    cmd: str | None = None
    args: list[str] = field(default_factory=list)
    inside_vm: bool = False
    ignore_errors: bool = False

    def __post_init__(self):
        if not self.path and not self.cmd:
            raise ValueError("Either 'path' or 'cmd' must be provided.")

        if self.path and not isinstance(self.path, Path):
            raise TypeError(f"path must be a Path, got {type(self.path).__name__}")


class VagrantVMOnlyScript(VagrantScript):
    def __init__(
        self,
        path: Path | None = None,
        cmd: str | None = None,
        args: list[str] | None = None,
        ignore_errors: bool = False,
    ):
        super().__init__(
            path=path,
            cmd=cmd,
            args=args or [],
            inside_vm=True,
            ignore_errors=ignore_errors,
        )


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
