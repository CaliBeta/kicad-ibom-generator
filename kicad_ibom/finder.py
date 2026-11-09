"""
Auto-detection utilities for KiCad Python executable, PCB project files,
and InteractiveHtmlBom module directories across Windows, macOS, and Linux.
"""

import os
import sys
import glob
import shutil
import platform
import subprocess
from pathlib import Path
from typing import Optional, List


def is_python_with_pcbnew(python_exec: str) -> bool:
    """Test whether a given python executable can successfully import pcbnew."""
    if not python_exec:
        return False
    # If it's current python, check directly
    if Path(python_exec).resolve() == Path(sys.executable).resolve():
        try:
            import pcbnew  # type: ignore
            return True
        except ImportError:
            return False

    try:
        res = subprocess.run(
            [python_exec, "-c", "import pcbnew; print('OK')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
        return res.returncode == 0 and "OK" in res.stdout
    except Exception:
        return False


def find_kicad_python(explicit_path: Optional[str] = None) -> Optional[str]:
    """
    Locate KiCad's internal Python executable with pcbnew support.

    Lookup hierarchy:
      1. Explicit path supplied by caller (--kicad-python)
      2. Environment variable KICAD_PYTHON
      3. Current Python interpreter (if pcbnew is already present)
      4. OS-specific standard installation directories (KiCad 9, 8, 7)
      5. PATH lookups (kicad-cli or kicad binary neighbors)
    """
    # 1. Explicit path
    if explicit_path:
        p = Path(explicit_path)
        if p.is_file():
            return str(p.resolve())
        elif shutil.which(explicit_path):
            return shutil.which(explicit_path)

    # 2. Environment variable
    env_override = os.environ.get("KICAD_PYTHON")
    if env_override:
        p = Path(env_override)
        if p.is_file():
            return str(p.resolve())
        elif shutil.which(env_override):
            return shutil.which(env_override)

    # 3. Current Python environment
    try:
        import pcbnew  # type: ignore
        return sys.executable
    except ImportError:
        pass

    os_type = platform.system()

    # 4. Windows discovery
    if os_type == "Windows":
        # Known default paths (prioritize KiCad 9, then 8, then 7)
        fixed_candidates = [
            Path(r"C:\Program Files\KiCad\9.0\bin\python.exe"),
            Path(r"C:\Program Files\KiCad\8.0\bin\python.exe"),
            Path(r"C:\Program Files\KiCad\7.0\bin\python.exe"),
            Path(r"C:\Program Files (x86)\KiCad\9.0\bin\python.exe"),
            Path(r"C:\Program Files (x86)\KiCad\8.0\bin\python.exe"),
        ]
        for cand in fixed_candidates:
            if cand.is_file():
                return str(cand.resolve())

        # Dynamic search in Program Files
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        globbed = sorted(
            glob.glob(os.path.join(prog_files, "KiCad", "*", "bin", "python.exe")),
            reverse=True,
        )
        for g_cand in globbed:
            if Path(g_cand).is_file():
                return str(Path(g_cand).resolve())

        # LocalAppData search
        local_app = os.environ.get("LOCALAPPDATA")
        if local_app:
            local_glob = sorted(
                glob.glob(os.path.join(local_app, "Programs", "KiCad", "*", "bin", "python.exe")),
                reverse=True,
            )
            for g_cand in local_glob:
                if Path(g_cand).is_file():
                    return str(Path(g_cand).resolve())

        # Check sibling of kicad-cli or kicad if present in PATH
        cli_path = shutil.which("kicad-cli") or shutil.which("kicad")
        if cli_path:
            sibling_python = Path(cli_path).resolve().parent / "python.exe"
            if sibling_python.is_file():
                return str(sibling_python)

    # 5. macOS discovery
    elif os_type == "Darwin":
        mac_candidates = [
            Path("/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"),
            Path("/Applications/KiCad/KiCad.app/Contents/MacOS/python3"),
            Path("/Applications/KiCad 9.0/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"),
            Path("/Applications/KiCad 8.0/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"),
        ]
        for cand in mac_candidates:
            if cand.is_file():
                return str(cand.resolve())

        globbed_mac = sorted(
            glob.glob("/Applications/KiCad*/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3"),
            reverse=True,
        )
        for g_cand in globbed_mac:
            if Path(g_cand).is_file():
                return str(Path(g_cand).resolve())

    # 6. Linux discovery
    else:
        # Standard system python with pcbnew package (e.g. python3-kicad or python3-pcbnew)
        candidates = ["python3", "/usr/bin/python3", "/usr/local/bin/python3"]
        for cand in candidates:
            resolved = shutil.which(cand) or cand
            if is_python_with_pcbnew(resolved):
                return resolved

    return None


def get_3rdparty_search_paths() -> List[Path]:
    """Return standard KiCad 3rdparty / Plugin directories where InteractiveHtmlBom might reside."""
    paths: List[Path] = []
    os_type = platform.system()

    if os_type == "Windows":
        user_docs = Path.home() / "Documents" / "KiCad"
        if user_docs.is_dir():
            # Check 9.0, 8.0, 7.0 subfolders
            for ver_dir in sorted(user_docs.glob("*"), reverse=True):
                if ver_dir.is_dir():
                    # Check 3rdparty/Python*/site-packages
                    for py_pkg in ver_dir.glob("3rdparty/Python*/site-packages"):
                        if py_pkg.is_dir():
                            paths.append(py_pkg)
                    # Check 3rdparty/plugins
                    plugins_dir = ver_dir / "3rdparty" / "plugins"
                    if plugins_dir.is_dir():
                        paths.append(plugins_dir)

    elif os_type == "Darwin":
        app_support = Path.home() / "Library" / "Application Support" / "kicad"
        if app_support.is_dir():
            for ver_dir in sorted(app_support.glob("*"), reverse=True):
                p = ver_dir / "3rdparty" / "plugins"
                if p.is_dir():
                    paths.append(p)

    else:
        # Linux
        local_share = Path.home() / ".local" / "share" / "kicad"
        if local_share.is_dir():
            for ver_dir in sorted(local_share.glob("*"), reverse=True):
                p = ver_dir / "3rdparty" / "plugins"
                if p.is_dir():
                    paths.append(p)

    return paths


def find_pcb_file(start_path: Optional[str] = None) -> Optional[Path]:
    """
    Search for a .kicad_pcb file.
    If start_path is a file, verify and return it.
    If start_path is a directory (or None for current dir), search inside it.
    """
    if start_path:
        p = Path(start_path).resolve()
        if p.is_file():
            if p.suffix.lower() == ".kicad_pcb":
                return p
            return None
        if p.is_dir():
            search_dir = p
        else:
            return None
    else:
        search_dir = Path.cwd().resolve()

    # Direct match in target directory
    pcb_files = list(search_dir.glob("*.kicad_pcb"))
    # Filter out auto-save and backup files
    pcb_files = [f for f in pcb_files if not f.name.endswith(("-bak.kicad_pcb", "-save.kicad_pcb"))]

    if pcb_files:
        # Return newest if multiple
        pcb_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return pcb_files[0]

    # Search 1 level deeper
    nested = list(search_dir.glob("*/*.kicad_pcb"))
    nested = [f for f in nested if not f.name.endswith(("-bak.kicad_pcb", "-save.kicad_pcb"))]
    if nested:
        nested.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return nested[0]

    return None
