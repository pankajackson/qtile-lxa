from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pathlib import Path
import tempfile
from qtile_lxa import __ASSETS_DIR__
from .typing_vm import VagrantVMConfig


class VagrantVMConfigResources:

    templates_dir = __ASSETS_DIR__ / "vagrant/templates"

    def __init__(self, config: VagrantVMConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir

        # Initialize the environment ONCE (best practice)
        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            undefined=StrictUndefined,  # catch missing variables early
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Generate + write Vagrantfile when object is created
        self.vagrantfile, self.vagrantfile_path = self.render_template(
            "vagrantfile",
            output_path=self.output_dir / "Vagrantfile",
            vm=self.config,
        )

    def render_template(
        self,
        name: str,
        output_path: Path | None = None,
        **kwargs,
    ) -> tuple[str, Path]:

        template = self.env.get_template(f"{name}.j2")
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
