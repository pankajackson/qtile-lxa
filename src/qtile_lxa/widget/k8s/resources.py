from pathlib import Path
from jinja2 import Template, StrictUndefined, Undefined
import tempfile
from .typing import K8SConfig
from qtile_lxa import __ASSETS_DIR__


class K8sResources:
    templates_dir = __ASSETS_DIR__ / "k8s/templates"

    def __init__(self, config: K8SConfig, output_dir: Path):
        self.config = config
        self.output_dir = output_dir

        self.master_userdata, self.master_userdata_path = (
            self._generate_master_userdata()
        )
        self.agent_userdata, self.agent_userdata_path = self._generate_agent_userdata()
        self.agent_post_start_script, self.agent_post_start_script_path = (
            self._generate_agent_post_start_script()
        )
        self.agent_pre_remove_script, self.agent_pre_remove_script_path = (
            self._generate_agent_pre_remove_script()
        )

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

    def _generate_master_userdata(self) -> tuple[str, Path]:
        install_flags = (
            "--write-kubeconfig-mode 644 --node-taint CriticalAddonsOnly=true:NoExecute"
        )
        if self.config.disable_local_storage:
            install_flags += " --disable local-storage"
        if self.config.disable_traefik_ingress:
            install_flags += " --disable traefik"
        if self.config.disable_metrics_server:
            install_flags += " --disable metrics-server"

        return self.load_template(
            "scripts/master_userdata.sh",
            output_path=self.output_dir / "master_userdata.sh",
            strict=False,
            install_flags=install_flags,
            k3s_version=self.config.k3s_version,
            k3s_token=self.config.k3s_token,
            cluster_name=self.config.cluster_name,
        )

    def _generate_agent_userdata(self) -> tuple[str, Path]:
        return self.load_template(
            "scripts/worker_userdata.sh",
            output_path=self.output_dir / "agent_userdata.sh",
        )

    def _generate_agent_pre_remove_script(self) -> tuple[str, Path]:
        return self.load_template(
            "scripts/worker_pre_remove.sh",
            output_path=self.output_dir / "agent_pre_remove.sh",
        )

    def _generate_agent_post_start_script(self) -> tuple[str, Path]:
        return self.load_template(
            "scripts/worker_post_start.sh",
            output_path=self.output_dir / "agent_post_start.sh",
        )
