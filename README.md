# 🦔 lmole

**lmole** (Linux Mole) is a high-performance system optimization and cleanup tool designed specifically for the Linux platform. Inspired by the minimalist philosophy of the famous `Mole` tool on macOS, `lmole` provides a fast, safe, and intuitive experience for maintaining system health and reclaiming disk space.

Built with a hybrid architecture of **Python logic** and a custom **Rust scanning engine**, `lmole` is up to 10x faster than traditional shell-based tools for large-scale filesystem analysis.

---

## ✨ Key Features

1.  **🧽 One-Key Clean**  
    A streamlined, one-action cleanup process. Covers package manager caches (DNF/APT/Pacman), system journal logs, user trash, and developer caches (NPM, Pip, Go). Now features **AI/LLM Model Cleanup** (Ollama, Hugging Face) and Docker system pruning.

2.  **📦 Deep Uninstall**  
    Completely remove applications including their hidden residues. Uses **intelligent keyword extraction** from `.desktop` files and fuzzy matching to locate configurations in `~/.config`, `~/.cache`, and `~/.local`. Automatically **terminates running processes** before removal to prevent "ghost" apps.

3.  **⚡ System Optimize**  
    Advanced maintenance beyond simple cleaning. Includes **SQLite Database Vacuuming** for browsers (Firefox, Chrome, Brave) to improve startup speed, **Zombie Autostart Cleanup**, SSD Trim, and **Intelligent Memory/Swap Management**.

4.  **📊 Intelligence Analyze**  
    An ultra-fast disk usage analyzer powered by a dedicated Rust engine. Features multi-threaded scanning and a built-in **ScanCache** for instant directory navigation without rescanning.

5.  **🛡️ Health Status**  
    Comprehensive system monitoring dashboard. Displays CPU load, core temperature, memory pressure, disk utilization, network traffic, **GPU Status (NVIDIA/AMD)**, and a list of **Top Resource-Consuming Processes**.

---

## 🚀 Technical Advantages

*   **Rust Engine**: Core scanning logic implemented in `lmo-core` (Rust), utilizing parallel I/O to analyze tens of thousands of files in milliseconds.
*   **Modern TUI**: A clean terminal user interface with full keyboard navigation and numeric hotkeys for rapid selection.
*   **Safe by Design**: Built-in global whitelist protection ensures critical system paths are never touched. Enforces strict **Home Directory Isolation** for manual cleanup tasks.
*   **Cloud & AI Ready**: Native support for cleaning Docker resources and massive AI model repositories (Ollama, Hugging Face).

---

## 🛠️ Installation & Usage

### Prerequisites
*   Python 3.10+
*   Linux OS (Fedora, Ubuntu, Debian, Arch, etc.)

### Quick Installation (Recommended)
`lmole` is designed as a standalone tool. Simply link the launcher to your local bin path:

```bash
# Clone the repository
git clone https://github.com/Jesencloud/lmole.git
cd lmole

# Create a symbolic link to your local bin directory
# (Ensure ~/.local/bin is in your PATH)
ln -s $(pwd)/lmole ~/.local/bin/lmole
```

### Build Rust Engine (Optional)
The project includes pre-compiled binaries. To build the engine manually:
```bash
cd lmo-core && cargo build --release
cp target/release/lmo-core ../src/core/bin/lmo-core
```

---

## 📖 Usage Guide

Type `lmole` to enter the interactive TUI:
```bash
lmole
```

Alternatively, use CLI commands:
*   `lmole clean` - Execute one-key cleanup
*   `lmole uninstall` - Enter application uninstallation mode
*   `lmole optimize` - Run system maintenance tasks
*   `lmole analyze` - Enter deep disk analysis mode
*   `lmole status` - View real-time system health
*   `lmole remove` - Safely remove lmole system integration
*   `lmole authorize` - Setup passwordless sudo for lmole (optional)

---

## 🤝 Contribution & Credits

*   **Inspired by**: [Mole](https://github.com/tw93/mole) (macOS)
*   **Core Logic**: Python 3
*   **Scanning Engine**: Rust (lmo-core)

`lmole` strives to be the most elegant and powerful optimization tool for the Linux community. Issues and Pull Requests are always welcome!
