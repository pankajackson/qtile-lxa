from pathlib import Path
from jinja2 import Template, StrictUndefined, Undefined
import tempfile
from qtile_lxa import __ASSETS_DIR__


class K8sResources:
    templates_dir = __ASSETS_DIR__ / "k8s/templates"

    @staticmethod
    def load_template(
        name: str,
        output_path: Path | None = None,
        strict: bool = True,
        **kwargs,
    ) -> tuple[str, Path]:
        """
        Load a Jinja2 template, render it, and write to file.

        Args:
            name: Template filename without `.j2` extension.
            output_path: Optional path to write rendered content.
            strict: If True, raises error for undefined template variables.
            **kwargs: Variables to render into the template.

        Returns:
            Tuple of (rendered_text, final_path).
        """
        path = K8sResources.templates_dir / f"{name}.j2"
        if not path.exists():
            raise FileNotFoundError(f"Template not found: {path}")

        with open(path, encoding="utf-8") as f:
            template = Template(
                f.read(), undefined=StrictUndefined if strict else Undefined
            )
        rendered_text = template.render(**kwargs)

        if output_path:
            final_path = output_path
            final_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            filename = Path(name).name
            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}")
            final_path = Path(tmp_file.name)
            tmp_file.close()
        final_path.write_text(rendered_text, encoding="utf-8")

        return rendered_text, final_path

    @classmethod
    def master_userdata(
        cls,
        output_path: Path | None = None,
        disable_traefik_ingress: bool = False,
        disable_local_storage: bool = False,
        disable_metrics_server: bool = False,
        token: str | None = None,
    ) -> tuple[str, Path]:
        install_flags = "--write-kubeconfig-mode 644"
        if disable_local_storage:
            install_flags += " --disable local-storage"
        if disable_traefik_ingress:
            install_flags += " --disable traefik"
        if disable_metrics_server:
            install_flags += " --disable metrics-server"

        return cls.load_template(
            "master_userdata.sh", output_path=output_path, install_flags=install_flags
        )

    @classmethod
    def agent_userdata(cls, output_path: Path | None = None) -> tuple[str, Path]:
        return cls.load_template("agent_userdata.sh", output_path=output_path)
