# 🧩 qtile_lxa

**`qtile_lxa`** is a modular extension suite for the [Qtile window manager](https://qtile.org/), providing custom widgets, utility scripts, dynamic theming, screen locking, Docker integration, and more — designed to streamline advanced Linux desktop setups.

---

## 📦 Features

- 🔧 Custom Qtile widgets:
  - Docker, Kubernetes, Podman, Vagrant
  - System monitors: Nvidia, Elasticsearch, URL pings
- 🎨 Theme manager with:
  - PyWall & VidWall support
  - Youtube/Video/Gifs support for wallpapers
  - Live theme changer widget
  - Dynamic wallpaper categories (NASA picture of the day, BING Picture of the day, Git Repo)
- 🔐 Auto screen lock with `xautolock` or `betterlockscreen`
- 🔉 Volume, microphone, and brightness controllers
- 🖥️ Multi-screen support with screen profile switcher
- 📡 Smart network profile management
- 🪄 Powerful Power Menu (shutdown, reboot, sleep, etc.)
- 📁 Modular, organized, and extensible Python codebase

---

## 📂 Project Structure

```

qtile\_lxa/
├── src/qtile\_lxa/           # Main source code
│   ├── assets/              # Icons, sounds, wallpapers
│   ├── utils/               # Core utilities
│   └── widget/              # Custom widgets grouped by feature
├── build/, dist/            # Build artifacts (wheel, tar.gz)
├── test/                    # Widget import testing
├── pyproject.toml           # Build config
├── requirements.txt         # Python dependencies
└── README.md                # You're reading it!

```

---

## 🚀 Installation

### 1. Clone the repository

```bash
pip install qtile-lxa
```

> Requires: `docker`, `qtile`, `xautolock`, `betterlockscreen`, `dunst`, etc.

---

## 🛠️ Setup in Qtile Config

In your `~/.config/qtile/config.py`:

```python
from qtile_lxa import widget as lxa_widgets
from qtile_lxa.utils import AutoScreenLock, Controllers
```

Use your favorite widgets like:

```python
screens = [
    Screen(
        top=Bar([
            lxa_widgets.PowerMenu(),
            lxa_widgets.ThemeManager.Decoration.DecorationChanger(),
            # Add more...
        ], 24),
    ),
]
```

---

## 🧠 Example Use Cases

- Auto lock screen after idle time with Qtile hooks
- Docker/POD-based dev environments with status indicators
- Switch screen profiles and theme instantly with 1 click
- Notify on mic status or volume change via `dunst`

---

## 🧪 Development & Testing

### Run import check for all widgets

```bash
python test/import_widgets.py
```

### Build the package

```bash
python -m build
```

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributing

Contributions are welcome! Please open an issue or pull request for suggestions, bug fixes, or new widgets.

---

## 🧠 Credits

Built with ❤️ by Pankaj Kumar Patel (Pankaj Jackson) for the Arch/Qtile community.

Wallpaper credits: NASA, GitHub Wallpapers, Bing Images, and LXA original sets.

---

## 📷 Screenshots

<table> <tr> <td align="center"> <strong>Top Left Bar</strong><br> <em>Workspaces Controller</em><br> <a href="docs/images/top_workspace_manager.png"> <img src="docs/images/top_workspace_manager.png" width="320px"> </a> </td> <td align="center"> <strong>Top Right Bar</strong><br> <em>System Monitors</em><br> <a href="docs/images/top_status_bar.png"> <img src="docs/images/top_status_bar.png" width="320px"> </a> </td> </tr> <tr> <td align="center"> <strong>Bottom Right Bar</strong><br> <em>Other Custom Widgets</em><br> <a href="docs/images/bottom_bar.png"> <img src="docs/images/bottom_bar.png" width="320px"> </a> </td> <td align="center"> <strong>Theme Manager</strong><br> <em>Wallpaper, Color, Decorations</em><br> <a href="docs/images/theme_manager.png"> <img src="docs/images/theme_manager.png" width="320px"> </a> </td> </tr> <tr> <td align="center"> <strong>Video Wallpaper</strong><br> <em>Dynamic Background Control</em><br> <a href="docs/images/vidwall_widget.png"> <img src="docs/images/vidwall_widget.png" width="320px"> </a> </td> <td align="center"> <strong>Power Menu</strong><br> <em>Shutdown, Restart, Sleep</em><br> <a href="docs/images/power_menu.png"> <img src="docs/images/power_menu.png" width="320px"> </a> </td> </tr> </table>
