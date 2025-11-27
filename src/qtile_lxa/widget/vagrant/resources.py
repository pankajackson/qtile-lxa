from jinja2 import Environment, FileSystemLoader, StrictUndefined, Undefined
from pathlib import Path
import tempfile
from qtile_lxa import __ASSETS_DIR__
from .typing_vm import VagrantVMConfig
from .typing_vm_group import VagrantVMGroupConfig


class VagrantVMConfigResources:

    templates_dir = __ASSETS_DIR__ / "vagrant/templates"

    def __init__(
        self, config: VagrantVMConfig | VagrantVMGroupConfig, output_dir: Path
    ):
        self.config = config
        self.output_dir = output_dir

        if isinstance(config, VagrantVMConfig):
            template_name = "vagrantfile_vm"
            vagrant_config = {"vm": config}

        elif isinstance(config, VagrantVMGroupConfig):
            template_name = "vagrantfile_vm_group"
            vagrant_config = {"group": config}

        else:
            raise TypeError(f"Invalid type for config: {type(config)}")

        self.vagrantfile, self.vagrantfile_path = self.render_template(
            template_name,
            output_path=output_dir / "Vagrantfile",
            strict=True,
            **vagrant_config,
        )

    @staticmethod
    def render_template(
        name: str,
        output_path: Path | None = None,
        strict: bool = True,
        **kwargs,
    ) -> tuple[str, Path]:
        env = env = Environment(
            loader=FileSystemLoader(VagrantVMConfigResources.templates_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=StrictUndefined if strict else Undefined,
        )

        template = env.get_template(f"{name}.j2")
        rendered = template.render(**kwargs)

        # Determine output file path
        if output_path:
            final_path = output_path
            final_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{name}")
            final_path = Path(tmp.name)
            tmp.close()

        # Write to file
        final_path.write_text(rendered, encoding="utf-8")

        return rendered, final_path
