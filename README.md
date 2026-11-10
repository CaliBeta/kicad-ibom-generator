# kicad-ibom-generator

<div align="center">

[![CI](https://github.com/CaliBeta/kicad-ibom-generator/actions/workflows/ci.yml/badge.svg)](https://github.com/CaliBeta/kicad-ibom-generator/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=flat-square)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/Python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue?style=flat-square&logo=python)](https://python.org)
[![KiCad Version](https://img.shields.io/badge/KiCad-8.0%20%7C%209.0%2B-5B9BD5?style=flat-square&logo=kicad)](https://www.kicad.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-brightgreen?style=flat-square)](https://github.com/CaliBeta/kicad-ibom-generator)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-Yes-green.svg?style=flat-square)](https://calibeta.com)

**Universal Command-Line Generator for KiCad Interactive HTML BOM with Native KiCad 8 & 9+ Headless Bug Fixes.**

*Crafted by [CaliBeta](https://calibeta.com) — Electronics Design & PCBA Engineering Services.*

</div>

---

## ⚡ The Problem: KiCad 9 Headless Assertions

When automating PCBA assembly outputs in **KiCad 9+** (via terminal scripts, Docker, or CI/CD pipelines), standard `InteractiveHtmlBom` triggers silent C++ assertion dialogs and freezes:

1. **Footprint Group Destruction Assertion (`assert m_group == nullptr`)**:  
   When components belong to a `PCB_GROUP`, cloning footprints (`pcbnew.FOOTPRINT(f)`) to calculate their neutral bounding boxes copies internal C++ pointers. When garbage collection destroys the clone, `BOARD_ITEM::~BOARD_ITEM()` aborts execution with an invisible dialog on Windows.
2. **Via Width Missing Layer Parameter (`PCB_VIA::GetWidth()`)**:  
   KiCad 9 requires an explicit layer parameter for `PCB_VIA::GetWidth(layer)`. Unparameterized calls throw `assert "false" in PCB_VIA::GetWidth(): Warning: PCB_VIA::GetWidth called without a layer argument`.
3. **Headless / No-Display wxWidgets Binding Crashes**:  
   Importing the module in unattended environments attempts GUI action registration, failing with `assert "PgmOrNull()"`.

### 🛡️ The Solution: `kicad-ibom-generator`

`kicad-ibom` is a clean, single-command CLI wrapper that:
- **Hot-patches KiCad in memory at runtime** to resolve all three issues transparently without altering your global KiCad files.
- **Auto-detects** your `*.kicad_pcb` board and KiCad's bundled Python interpreter on Windows, macOS, and Linux.
- **Operates with zero configuration**, or accepts granular flags for dark mode, copper tracks, netlists, and custom BOM grouping fields.

---

## 🚀 Key Features

- 🔍 **Zero-Config Discovery**: Simply run `kicad-ibom` inside your project directory; it finds your board and generates the HTML BOM immediately.
- 🌙 **Modern Dark Theme**: Pre-configured with sleek dark mode enabled by default for comfortable assembly bench viewing.
- 🎯 **Pin 1 Orientation Highlighting**: Highlights pin 1 on selected components to eliminate rotation assembly errors.
- ⚡ **Full Netlist & Track Support**: Includes copper traces and interactive net tracing directly in the browser.
- 🏷️ **Supply Chain Ready**: Groups identical parts by `Value,Footprint,LCSC` (or custom parameters like `Manufacturer`, `MPN`, `Tolerance`).
- 🤖 **CI/CD & DevOps Optimized**: Flawlessly integrates into GitHub Actions, GitLab CI, and build scripts.
- 🌐 **Cross-Platform**: Tested on Windows 10/11, macOS (Apple Silicon / Intel), and Ubuntu/Debian Linux.

---

## 📦 Installation

Install directly via `pip`:

```bash
# From PyPI (once published)
pip install kicad-ibom-generator

# Or directly from GitHub
pip install git+https://github.com/CaliBeta/kicad-ibom-generator.git
```

For local development or editable installation:

```bash
git clone https://github.com/CaliBeta/kicad-ibom-generator.git
cd kicad-ibom-generator
pip install -e .
```

> **Prerequisite:** KiCad 8 or KiCad 9+ installed on your system with the **Interactive HTML BOM** plugin present (available in KiCad via *Tools* &rarr; *Plugin and Content Manager*).

---

## 🛠️ Usage Guide

### 1. Zero-Configuration Mode (Run Anywhere)

Navigate to any directory containing a `.kicad_pcb` file and run:

```bash
kicad-ibom
```

The tool will:
1. Scan for `*.kicad_pcb` files in the current folder.
2. Locate the KiCad Python runtime on your OS.
3. Apply runtime memory patches for KiCad 9.
4. Export the standalone HTML visualizer to `./outputs/assembly/ibom_<board_name>.html`.

---

### 2. Explicit PCB File & Custom Output Directory

```bash
kicad-ibom Hardware/IEH-Gateway.kicad_pcb -o dist/pcba -n assembly_guide
```

---

### 3. Open Directly in Web Browser

Generate and immediately open the visualizer in your default browser:

```bash
kicad-ibom --open
```

---

### 4. Custom BOM Fields & Supplier Part Numbers (e.g. LCSC, DigiKey)

Customize the table columns and grouping fields for your contract manufacturer:

```bash
kicad-ibom MyBoard.kicad_pcb \
  --show-fields "Value,Footprint,LCSC,Manufacturer,MPN" \
  --group-fields "Value,Footprint,LCSC,MPN" \
  --dark-mode \
  --highlight-pin1 selected \
  --include-tracks \
  --include-nets
```

---

## ⚙️ CLI Reference Table

| Argument / Flag | Default | Description |
| :--- | :--- | :--- |
| `pcb_file` | Auto-detected | Path to the `*.kicad_pcb` file. If omitted, discovers automatically. |
| `-o`, `--dest-dir`, `--output-dir` | `outputs/assembly` | Destination folder for the generated HTML BOM. |
| `-n`, `--name-format` | `ibom_%f` | Output filename pattern (`%f`: board name, `%p`: title, `%r`: rev, `%d`: date). |
| `--dark-mode` / `--light-mode` | `--dark-mode` | Set default visualizer color theme. |
| `--highlight-pin1` | `selected` | Pin 1 highlight behavior (`selected`, `all`, `none`). |
| `--include-tracks` / `--no-tracks` | `--include-tracks` | Include or exclude copper traces and polygon pours. |
| `--include-nets` / `--no-nets` | `--include-nets` | Include or exclude PCB netlist for trace highlighting. |
| `--show-fields` | `Value,Footprint,LCSC` | Comma-separated list of schematic fields shown in the table. |
| `--group-fields` | `Value,Footprint,LCSC` | Comma-separated fields used to group components into single line items. |
| `--open` | `False` | Automatically launch the generated HTML BOM in the default browser. |
| `--kicad-python` | Auto-detected | Explicit path to KiCad's Python interpreter executable. |
| `-v`, `--verbose` | `False` | Print detailed debug information and forwarded flags. |
| `--version` | — | Display version number and author information. |

---

## 🧠 Technical Architecture & Runtime Patching

Unlike invasive scripts that modify installed KiCad system files, `kicad-ibom` applies non-destructive runtime monkey-patching in memory:

```
[User Terminal / CI]
        │
        ▼
   kicad-ibom (cli.py)
        │
        ├── 1. Discovers *.kicad_pcb & KiCad Python binary (finder.py)
        │
        └── 2. Spawns KiCad Python with isolated headless environment
                     │
                     ▼
             kicad_ibom.patches
                     ├── setup_headless_env()
                     │     └── INTERACTIVE_HTML_BOM_CLI_MODE = "1"
                     │     └── INTERACTIVE_HTML_BOM_NO_DISPLAY = "1"
                     ├── patch_footprint_group()
                     │     └── Detaches m_group on FOOTPRINT init to prevent C++ assert
                     └── patch_via_width()
                           └── Provides fallback F_Cu layer to PCB_VIA::GetWidth()
                     │
                     ▼
          InteractiveHtmlBom Engine
                     │
                     ▼
         [Standalone HTML Assembly Guide]
```

---

## 🔄 CI/CD Integration (GitHub Actions Example)

Add this workflow to `.github/workflows/ibom.yml` to generate your assembly visualizer on every release or commit:

```yaml
name: Generate Interactive Assembly BOM

on:
  push:
    branches: [ "main" ]

jobs:
  generate-ibom:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4

      - name: Install KiCad & Dependencies
        run: |
          sudo add-apt-repository --yes ppa:kicad/kicad-9.0-releases
          sudo apt-get update
          sudo apt-get install -y --no-install-recommends kicad python3-kicad

      - name: Install kicad-ibom-generator
        run: pip install git+https://github.com/CaliBeta/kicad-ibom-generator.git

      - name: Generate PCBA Visualizer
        run: kicad-ibom MyBoard.kicad_pcb -o dist/assembly

      - name: Upload Assembly Artifact
        uses: actions/upload-artifact@v4
        with:
          name: PCBA-Assembly-Guide
          path: dist/assembly/*.html
```

---

## 📂 Live Interactive Demo

An interactive demonstration generated directly by this tool is bundled in the repository:
- Inspect [`examples/demo_ibom.html`](examples/demo_ibom.html) to explore the dark-mode PCBA visualizer, net tracing, and BOM grouping in action.

---

## 💼 Hardware Engineering & PCBA Services by CaliBeta

Need end-to-end hardware development, rapid prototyping, or manufacturing optimization?

**CaliBeta** specializes in turn-key electronics design and embedded engineering:

- 📐 **High-Density & High-Speed PCB Layout** (KiCad)
- 📡 **IoT & Embedded Systems Architecture** (ESP32, STM32, BLE, LoRaWAN)
- 🏭 **Design for Manufacturing & Assembly (DFM / DFA)** with JLCPCB, PCBWay, and European/US fabs.
- ⚡ **Power Electronics & Analog Front-End (AFE) Design**
- 🛠️ **Custom Hardware Automation & Testing Tooling**

Ready to turn your schematic into a reliable, mass-production-ready hardware product?

👉 **Get in touch:** [info@calibeta.com](mailto:info@calibeta.com)  
👉 **Website & Portfolio:** [calibeta.com](https://calibeta.com)  
👉 **GitHub:** [@calibeta](https://github.com/calibeta)

---

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE) (GPL-3.0) to ensure full compatibility with the upstream [InteractiveHtmlBom](https://github.com/openscopeproject/InteractiveHtmlBom) ecosystem.

*Contributions, bug reports, and pull requests are warmly welcome!*

