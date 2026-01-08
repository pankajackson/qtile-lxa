from qtile_extras.widget import GenPollText, decorations
from typing import Any
from .typing import VagrantVMConfig
from .resources import VagrantVMConfigResources
from .runner import VagrantCLI


class VagrantVM(GenPollText):
    def __init__(self, config: VagrantVMConfig, **kwargs: Any):
        self.config = config
        self.vm_name = "unknown"
        self.vm_state = "unknown"

        self.resources = VagrantVMConfigResources(
            config=config,
            skip_vagrantfile_generation=not config.manage_vagrantfile,
        )
        self.vagrant_dir = self.resources.vagrant_dir
        self.vg_cli = VagrantCLI(self.vagrant_dir, env=config.env)

        # Vagrant → symbol mapping
        self.state_symbols_map = {
            "running": self.config.running_symbol,
            "not_created": self.config.not_created_symbol,
            "poweroff": self.config.poweroff_symbol,
            "aborted": self.config.aborted_symbol,
            "saved": self.config.saved_symbol,
            "stopped": self.config.stopped_symbol,
            "frozen": self.config.frozen_symbol,
            "shutoff": self.config.shutoff_symbol,
            "unknown": self.config.unknown_symbol,
            "error": self.config.error_symbol,
        }
        self.decorations = [
            decorations.RectDecoration(
                colour="#004040",
                radius=10,
                filled=True,
                padding_y=4,
                group=True,
                extrawidth=5,
            )
        ]
        self.format = "{symbol} {label}"
        super().__init__(func=self.check_vm_status, **kwargs)

    def check_vm_status(self):

        vm = self.vg_cli.get_vm(self.config.name)
        if not vm:
            return self.format.format(
                symbol=self.state_symbols_map["unknown"],
                label=self.config.label or self.config.name or "unknown",
            )
        self.vm_name = vm.name
        self.vm_state = vm.state
        state = vm.state
        symbol = self.state_symbols_map.get(state, self.config.unknown_symbol)
        return self.format.format(symbol=symbol, label=self.config.label or vm.name)

    def button_press(self, x, y, button):

        if button == 1:  # Left-click: Start all machines
            self.vg_cli.run_in_thread(self.handle_start_vagrant)
        elif button == 3:  # Right-click: Stop all machines
            self.vg_cli.run_in_thread(self.handle_stop_vagrant)
        elif button == 2:  # Middle-click: Destroy all machines
            self.vg_cli.run_in_thread(self.handle_destroy_vagrant)

    def handle_start_vagrant(self):
        vm = self.vg_cli.get_vm(self.vm_name, sync=True)
        if vm:
            self.vm_state = vm.state
        if self.vm_state == "running":
            self.vg_cli.ssh_vm(self.vm_name)
        else:
            self.vg_cli.start_vm(self.vm_name)

    def handle_stop_vagrant(self):

        self.vg_cli.stop_vm(self.vm_name)

    def handle_destroy_vagrant(self):

        self.vg_cli.destroy_vm(self.vm_name)
