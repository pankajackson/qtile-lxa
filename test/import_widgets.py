from pathlib import Path
from qtile_lxa import widget as lxa_widgets
from qtile_lxa.widget.theme.bar import DecoratedBar
from libqtile.config import Screen


screens = [
    Screen(
        top=DecoratedBar(
            [
                lxa_widgets.docker.DockerCompose(
                    config=lxa_widgets.docker.DockerComposeConfig(
                        compose_file=Path("docker-compose.yml"),
                    )
                ),
                lxa_widgets.theme.theme_manager.ThemeManager(),
                # Add more...
            ],
            height=24,
        ).get_bar(),
    ),
]
