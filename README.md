# 🧩 QtileLXA

**`QtileLXA`** is a modular extension suite for the [Qtile window manager](https://qtile.org/), offering advanced desktop enhancements like custom widgets, utility scripts, dynamic theming, screen locking, Docker integration, and more — designed to streamline advanced Linux desktop setups.

---

## 📦 Features

- 🎨 **Dynamic Theme Manager**:

  - PyWall & VidWall support
  - Wallpaper rotation with NASA/Bing/Git repo sources
  - Live decoration and color scheme switching

- 🔐 **Auto Screen Lock**:

  - Integrates with `xautolock` or `betterlockscreen`

- 🔊 **Device Controllers**:

  - Volume, microphone, brightness toggles and indicators

- 🖥️ **Multi-screen Management**:

  - Profile switcher for workspace and layout presets

- 📡 **Smart Network Profile Detection**

- 🪄 **Custom Power Menu**:

  - Shutdown, reboot, sleep, hybrid-sleep, hibernate, etc.

- 🧩 **Modular Codebase**:
  - Easily extensible and cleanly organized Python modules

---

## 📂 Project Structure

<details>
<summary><strong>Click to expand</strong></summary>

```text
qtile_lxa/
├── src/qtile_lxa/           # Main package
│   ├── assets/              # Icons, sounds, wallpapers
│   ├── utils/               # Utilities (lock, controllers, notifications)
│   └── widget/              # Custom widgets by category
├── test/                    # Widget test scripts
├── dist/                    # Build artifacts
├── pyproject.toml           # Build config
├── requirements.txt         # Dependencies
├── README.md                # You’re reading it!
└── LICENSE                  # MIT License
```

</details>

---

## 🚀 Installation

### 1. Clone the repository

```bash
pip install qtile-lxa
```

> **Dependencies**: `docker`, `qtile`, `xautolock`, `betterlockscreen`, `dunst`, etc.

---

## 🛠️ Setup in Qtile Config

In your `~/.config/qtile/config.py`:

```python
from pathlib import Path
from qtile_lxa import widget as lxa_widgets
from qtile_lxa.widget.theme.bar import DecoratedBar
from libqtile.config import Screen
```

Use your favorite widgets like:

```python
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

```

---

## 🧠 Example Use Cases

- Auto lock screen after idle time with Qtile hooks
- Monitor containerized environments (Docker, Podman, K8s)
- Instantly switch wallpapers, themes, and bar decorations
- Get visual feedback for volume and mic status with `dunst`

---

## 🧪 Development & Testing

### Run import tests

```bash
python test/import_widgets.py
```

### Build the package

```bash
python -m build
```

---

## 📷 Screenshots

<table> <tr> <td align="center"> <strong>Top Left Bar</strong><br> <em>Workspaces Controller</em><br> <a href="docs/images/top_workspace_manager.png"> <img src="docs/images/top_workspace_manager.png" width="320px"> </a> </td> <td align="center"> <strong>Top Right Bar</strong><br> <em>System Monitors</em><br> <a href="docs/images/top_status_bar.png"> <img src="docs/images/top_status_bar.png" width="320px"> </a> </td> </tr> <tr> <td align="center"> <strong>Bottom Right Bar</strong><br> <em>Other Custom Widgets</em><br> <a href="docs/images/bottom_bar.png"> <img src="docs/images/bottom_bar.png" width="320px"> </a> </td> <td align="center"> <strong>Theme Manager</strong><br> <em>Wallpaper, Color, Decorations</em><br> <a href="docs/images/theme_manager.png"> <img src="docs/images/theme_manager.png" width="320px"> </a> </td> </tr> <tr> <td align="center"> <strong>Video Wallpaper</strong><br> <em>Dynamic Background Control</em><br> <a href="docs/images/vidwall_widget.png"> <img src="docs/images/vidwall_widget.png" width="320px"> </a> </td> <td align="center"> <strong>Power Menu</strong><br> <em>Shutdown, Restart, Sleep</em><br> <a href="docs/images/power_menu.png"> <img src="docs/images/power_menu.png" width="320px"> </a> </td> </tr> </table>

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributing

Contributions are welcome! Please open an issue or pull request for suggestions, bug fixes, or new widgets.

---

## 🧠 Credits

Built with ❤️ by Pankaj Kumar Patel (Pankaj Jackson) for the Arch/Qtile community.

Wallpaper credits: NASA, Bing Images, and LXA originals.
