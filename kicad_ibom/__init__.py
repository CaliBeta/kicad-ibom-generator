"""
kicad-ibom-generator: Universal CLI generator for KiCad Interactive HTML BOM.
Maintained by CaliBeta (https://calibeta.com).
"""

from .finder import find_kicad_python, find_pcb_file
from .patches import apply_patches

__version__ = "1.0.0"
__author__ = "CaliBeta"
__all__ = [
    "__version__",
    "__author__",
    "find_kicad_python",
    "find_pcb_file",
    "apply_patches",
]

