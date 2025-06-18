import subprocess
from pathlib import Path


def send_notification(
    title: str,
    msg: str,
    progress: int | None = None,
    app_name: str | None = None,
    app_id: int | None = None,
    icon: Path | str | None = None,
    timeout: int | None = None,
) -> None:
    cmd = ["dunstify"]

    if app_name:
        cmd.extend(["-a", app_name])

    if app_id is not None:
        cmd.extend(["-r", str(app_id)])

    if icon:
        cmd.extend(["-i", str(icon)])

    if progress is not None:
        cmd.extend(["-h", f"'int:value:{progress}'", f"{title}: {progress}%"])
    else:
        cmd.append(title)

    cmd.append(msg)

    if timeout is not None:
        cmd.extend(["-t", str(timeout)])

    subprocess.run(cmd, check=True)
