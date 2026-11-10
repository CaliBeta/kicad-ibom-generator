"""
Universal Command-Line Interface (CLI) for KiCad Interactive HTML BOM Generator.
Designed for KiCad 8 and KiCad 9+ with native headless bug fixes.
Maintained by CaliBeta (https://calibeta.com).
"""

import os
import sys
import argparse
import subprocess
import webbrowser
from pathlib import Path
from typing import List, Optional

from . import __version__, __author__
from .finder import find_kicad_python, find_pcb_file, get_3rdparty_search_paths
from .patches import apply_patches


BANNER = f"""
================================================================================
  kicad-ibom v{__version__} - Universal Interactive HTML BOM Generator
  Crafted by {__author__} | Hardware Engineering & PCBA Services (calibeta.com)
================================================================================
"""


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser with comprehensive options and defaults."""
    parser = argparse.ArgumentParser(
        prog="kicad-ibom",
        description="Universal CLI for KiCad Interactive HTML BOM with native KiCad 8 & 9+ headless bug fixes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Positional board file
    parser.add_argument(
        "pcb_file",
        nargs="?",
        default=None,
        help="Path to the *.kicad_pcb file. If omitted, auto-discovers in current directory.",
    )

    # Destination and naming
    parser.add_argument(
        "-o",
        "--dest-dir",
        "--output-dir",
        dest="dest_dir",
        default="outputs/assembly",
        help="Destination directory for the generated HTML BOM.",
    )
    parser.add_argument(
        "-n",
        "--name-format",
        dest="name_format",
        default="ibom_%f",
        help="Output filename pattern (%%f: board name, %%p: title, %%r: revision, %%d: date).",
    )

    # Visual and layer options
    parser.add_argument(
        "--dark-mode",
        dest="dark_mode",
        action="store_true",
        default=True,
        help="Enable dark mode theme by default.",
    )
    parser.add_argument(
        "--light-mode",
        dest="dark_mode",
        action="store_false",
        help="Force light mode theme.",
    )
    parser.add_argument(
        "--highlight-pin1",
        choices=["none", "all", "selected"],
        default="selected",
        help="Pin 1 highlight behavior.",
    )
    parser.add_argument(
        "--include-tracks",
        dest="include_tracks",
        action="store_true",
        default=True,
        help="Include PCB copper tracks and zones in the interactive visualizer.",
    )
    parser.add_argument(
        "--no-tracks",
        dest="include_tracks",
        action="store_false",
        help="Exclude copper tracks and zones from output.",
    )
    parser.add_argument(
        "--include-nets",
        dest="include_nets",
        action="store_true",
        default=True,
        help="Include full netlist data for interactive signal tracing.",
    )
    parser.add_argument(
        "--no-nets",
        dest="include_nets",
        action="store_false",
        help="Exclude netlist information from output.",
    )

    # Fields and grouping
    parser.add_argument(
        "--show-fields",
        default="Value,Footprint,LCSC",
        help="Comma-separated list of component fields to display in BOM table.",
    )
    parser.add_argument(
        "--group-fields",
        default="Value,Footprint,LCSC",
        help="Comma-separated list of component fields to group identical parts by.",
    )

    # Browser & execution control
    parser.add_argument(
        "--open",
        action="store_true",
        default=False,
        help="Automatically open the generated HTML BOM in the default web browser.",
    )
    parser.add_argument(
        "--kicad-python",
        default=None,
        help="Explicit path to KiCad's Python interpreter executable.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"kicad-ibom {__version__} by {__author__}",
    )

    # Internal worker flag
    parser.add_argument(
        "--internal-run",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    return parser


def run_worker(args: argparse.Namespace, extra_args: List[str]) -> int:
    """
    Worker routine executed inside KiCad's Python environment.
    Applies runtime patches, verifies dependencies, and invokes InteractiveHtmlBom.
    """
    # 1. Apply runtime patches
    patch_results = apply_patches()
    if args.verbose:
        print(f"[DEBUG] Runtime patches applied: {patch_results}")

    # 2. Add 3rdparty search paths to sys.path if not present
    for p in get_3rdparty_search_paths():
        p_str = str(p)
        if p_str not in sys.path:
            sys.path.append(p_str)

    # 3. Attempt to import InteractiveHtmlBom
    try:
        import InteractiveHtmlBom.generate_interactive_bom as ibom  # type: ignore
    except ImportError:
        print("\n[ERROR] InteractiveHtmlBom module could not be found in KiCad's environment.")
        print("Please install the 'Interactive HTML BOM' plugin:")
        print("  1. Open KiCad -> Plugin and Content Manager (PCM)")
        print("  2. Search for 'Interactive HTML BOM' and click 'Install'")
        print("  3. Or install into KiCad Python via: pip install InteractiveHtmlBom\n")
        return 1

    pcb_path = Path(args.pcb_file).resolve()
    if not pcb_path.is_file():
        print(f"\n[ERROR] Board file does not exist: {pcb_path}")
        return 1

    dest_dir = Path(args.dest_dir).resolve()
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Assemble arguments for InteractiveHtmlBom
    ibom_args = [
        "InteractiveHtmlBom",
        "--no-browser",
        "--dest-dir",
        str(dest_dir),
        "--name-format",
        args.name_format,
        "--highlight-pin1",
        args.highlight_pin1,
        "--show-fields",
        args.show_fields,
        "--group-fields",
        args.group_fields,
    ]

    if args.dark_mode:
        ibom_args.append("--dark-mode")
    else:
        ibom_args.append("--no-dark-mode")

    if args.include_tracks:
        ibom_args.append("--include-tracks")
    else:
        ibom_args.append("--exclude-tracks")

    if args.include_nets:
        ibom_args.append("--include-nets")
    else:
        ibom_args.append("--exclude-nets")

    # Pass through any extra unrecognized arguments
    ibom_args.extend(extra_args)

    # Finally append the PCB file
    ibom_args.append(str(pcb_path))

    if args.verbose:
        print(f"[DEBUG] Forwarded iBOM arguments: {' '.join(ibom_args)}")

    sys.argv = ibom_args

    try:
        ibom.main()
    except SystemExit as se:
        if se.code not in (0, None):
            return int(se.code)
    except Exception as exc:
        print(f"\n[ERROR] InteractiveHtmlBom execution failed: {exc}")
        return 1

    # Locate generated file
    # Format substitutions: %f -> stem
    expected_name = args.name_format.replace("%f", pcb_path.stem)
    if not expected_name.endswith(".html"):
        expected_name += ".html"

    candidate_file = dest_dir / expected_name
    if not candidate_file.is_file():
        # Search for any recently created html file in destination directory
        html_files = sorted(dest_dir.glob("*.html"), key=lambda f: f.stat().st_mtime, reverse=True)
        if html_files:
            candidate_file = html_files[0]

    if candidate_file.is_file():
        size_kb = candidate_file.stat().st_size / 1024.0
        print(f"[OUTPUT_HTML] {candidate_file.resolve()}")
        print(f"\n[SUCCESS] Interactive HTML BOM generated successfully!")
        print(f" -> Artifact: {candidate_file.resolve()}")
        print(f" -> Size:     {size_kb:.1f} KB")
        return 0
    else:
        print(f"\n[WARNING] iBOM generation completed, but output file could not be located in {dest_dir}.")
        return 0


def main() -> None:
    """Main CLI entry point for kicad-ibom."""
    parser = build_parser()
    args, extra_args = parser.parse_known_args()

    # If invoked directly inside KiCad python worker mode
    if args.internal_run:
        sys.exit(run_worker(args, extra_args))

    # Phase 1: Parent runner (User terminal)
    print(BANNER)

    # 1. Resolve PCB file
    pcb_path = find_pcb_file(args.pcb_file)
    if not pcb_path:
        if args.pcb_file:
            print(f"[ERROR] Specified PCB file not found: {args.pcb_file}")
        else:
            print("[ERROR] No KiCad PCB (*.kicad_pcb) file detected in current directory.")
            print("Tip: Specify the file explicitly: kicad-ibom path/to/board.kicad_pcb")
        sys.exit(1)

    print(f"[*] Target PCB:       {pcb_path.resolve()}")
    dest_dir = Path(args.dest_dir).resolve()
    print(f"[*] Output Directory: {dest_dir}")

    # 2. Locate KiCad Python
    kicad_python = find_kicad_python(args.kicad_python)
    if not kicad_python:
        print("\n[ERROR] KiCad's Python interpreter could not be located automatically.")
        print("Please provide its path using --kicad-python or set the KICAD_PYTHON env variable.")
        print("Common locations:")
        print(r"  Windows: C:\Program Files\KiCad\9.0\bin\python.exe")
        print("  macOS:   /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3")
        print("  Linux:   Install python3-pcbnew or python3-kicad via package manager")
        sys.exit(1)

    print(f"[*] KiCad Python:     {kicad_python}")

    # 3. Check if current environment is already KiCad's Python
    try:
        import pcbnew  # type: ignore
        is_direct = True
    except ImportError:
        is_direct = False

    args.pcb_file = str(pcb_path)
    args.dest_dir = str(dest_dir)

    if is_direct and Path(sys.executable).resolve() == Path(kicad_python).resolve():
        ret = run_worker(args, extra_args)
        if ret == 0 and args.open:
            expected_name = args.name_format.replace("%f", pcb_path.stem)
            if not expected_name.endswith(".html"):
                expected_name += ".html"
            target_html = dest_dir / expected_name
            if target_html.is_file():
                webbrowser.open(target_html.as_uri())
        sys.exit(ret)

    # 4. Spawn KiCad Python subprocess
    env = os.environ.copy()
    env["INTERACTIVE_HTML_BOM_CLI_MODE"] = "1"
    env["INTERACTIVE_HTML_BOM_NO_DISPLAY"] = "1"

    # Ensure this package directory is on PYTHONPATH and explicitly injected into sys.path
    pkg_root = str(Path(__file__).resolve().parent.parent)
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{pkg_root}{os.pathsep}{existing_pp}" if existing_pp else pkg_root

    bootstrap_code = (
        f"import sys; "
        f"sys.path.insert(0, {repr(pkg_root)}); "
        f"from kicad_ibom.cli import main; "
        f"main()"
    )

    cmd = [
        kicad_python,
        "-c",
        bootstrap_code,
        "--internal-run",
        str(pcb_path),
        "--dest-dir",
        str(dest_dir),
        "--name-format",
        args.name_format,
        "--highlight-pin1",
        args.highlight_pin1,
        "--show-fields",
        args.show_fields,
        "--group-fields",
        args.group_fields,
    ]

    if args.dark_mode:
        cmd.append("--dark-mode")
    else:
        cmd.append("--light-mode")

    if args.include_tracks:
        cmd.append("--include-tracks")
    else:
        cmd.append("--no-tracks")

    if args.include_nets:
        cmd.append("--include-nets")
    else:
        cmd.append("--no-nets")

    if args.verbose:
        cmd.append("--verbose")

    cmd.extend(extra_args)

    proc = subprocess.run(cmd, env=env, text=True, capture_output=True)

    generated_html_path: Optional[str] = None
    if proc.stdout:
        for line in proc.stdout.splitlines():
            if line.startswith("[OUTPUT_HTML]"):
                generated_html_path = line.replace("[OUTPUT_HTML]", "").strip()
            else:
                print(line)

    if proc.stderr:
        print(proc.stderr, file=sys.stderr)

    if proc.returncode != 0:
        print(f"\n[ERROR] Generation failed with exit code {proc.returncode}")
        sys.exit(proc.returncode)

    if args.open and generated_html_path:
        p = Path(generated_html_path)
        if p.is_file():
            print(f"[*] Opening visualizer in default browser...")
            webbrowser.open(p.as_uri())

    sys.exit(0)


if __name__ == "__main__":
    main()
