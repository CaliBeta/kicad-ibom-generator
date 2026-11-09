# Briefing Técnico y Guía de Handover para Nuevo Repositorio: KiCad Interactive HTML BOM CLI Tool

> **Documento de transferencia técnica:** Este documento contiene todo el contexto, código base, arquitectura, soluciones a bugs de KiCad 9 y roadmap para ser entregado directamente al agente de IA en la nueva sesión dedicada al desarrollo y publicación del repositorio independiente.

---

## 🏷️ Propuestas de Nombre para el Repositorio en GitHub

Para maximizar tanto el posicionamiento en búsquedas de GitHub/Google como la marca personal de **CaliBeta**:

| Opción | Nombre del Repositorio | Enfoque / Audiencia |
| :---: | :--- | :--- |
| **Opción A (Recomendada)** | `kicad-ibom-generator` *(o `kicad-ibom-cli`)* | **Máximo SEO & Adopción comunitaria.** Los usuarios que busquen cómo generar iBOM por terminal en KiCad 8/9 encontrarán este repo de inmediato. En el README y authoring se destaca la autoría de *CaliBeta*. |
| **Opción B (Marca Personal)** | `calibeta-kicad-ibom` | **Fuerte identidad de marca personal.** Ideal para portfolio y presentación ante clientes que visiten tu perfil `@CaliBeta`. |
| **Opción C (Hardware DevOps)** | `kicad-pcba-visualizer` | **Enfoque corporativo.** Suena a suite profesional de visualización e integración continua (CI/CD). |

> **Recomendación:** **`kicad-ibom-generator`** (o `calibeta-kicad-ibom`).

---

## 🎯 Misión del Nuevo Repositorio

Crear una herramienta de línea de comandos (CLI) en Python **autónoma, universal, multiplataforma (Windows, Linux, macOS) y 100% compatible con KiCad 9+** que permita a cualquier diseñador de hardware generar su **Interactive HTML BOM** con un solo comando, sin configuraciones complejas y sin los bloqueos típicos de KiCad 9.

---

## 🧠 El "Core Secreto": Bugs de KiCad 9 Resueltos

El paquete original de la comunidad `InteractiveHtmlBom` se congela o lanza aserciones críticas en KiCad 9 (especialmente en Windows). La nueva herramienta resuelve de forma transparente estos tres problemas:

### 1. Bug de Destrucción de Huellas Agrupadas (`assert m_group == nullptr`)
* **Problema:** En KiCad 9, cuando los componentes pertenecen a un grupo (`PCB_GROUP`), al clonar la huella con `f_copy = pcbnew.FOOTPRINT(f)` para calcular su bounding box neutral, el puntero C++ `m_group` se copia. Al destruirse `f_copy`, el destructor de KiCad lanza una aserción `assert "m_group == nullptr" failed in BOARD_ITEM::~BOARD_ITEM()`, congelando la terminal de Windows en una ventana de diálogo invisible.
* **Solución aplicada:**
  ```python
  if hasattr(f_copy, 'SetParentGroup'):
      f_copy.SetParentGroup(None)
  ```

### 2. Bug de Medición de Vías (`PCB_VIA::GetWidth()`)
* **Problema:** En KiCad 9, `PCB_VIA::GetWidth()` requiere obligatoriamente el argumento de capa porque las vías admiten anchos anulares dinámicos por capa. Llamar a `track.GetWidth()` sin argumentos dispara `assert "false" in PCB_VIA::GetWidth(): Warning: PCB_VIA::GetWidth called without a layer argument`.
* **Solución aplicada:**
  ```python
  if track.GetClass() in ["VIA", "PCB_VIA"]:
      try:
          width = track.GetWidth(pcbnew.F_Cu)
      except TypeError:
          width = track.GetWidth()
  ```

### 3. Asignación en Modo Headless / CLI
* **Problema:** Al importar el módulo fuera de la interfaz gráfica de KiCad, el plugin intenta registrarse en la barra de herramientas de wxWidgets y falla (`assert PgmOrNull()`).
* **Solución aplicada:**
  Inyectar en el entorno antes de cualquier importación:
  ```python
  os.environ["INTERACTIVE_HTML_BOM_CLI_MODE"] = "1"
  os.environ["INTERACTIVE_HTML_BOM_NO_DISPLAY"] = "1"
  ```

---

## 🏗️ Arquitectura Deseada para el Nuevo Repositorio

```text
kicad-ibom-generator/
├── .github/
│   └── workflows/
│       └── ci.yml               # Prueba de generación en GitHub Actions (Ubuntu + KiCad)
├── kicad_ibom/
│   ├── __init__.py
│   ├── cli.py                   # Parser CLI con argparse, auto-detección y flags
│   ├── finder.py                # Auto-localizador del binario de Python de KiCad (Win/Mac/Linux)
│   └── patches.py               # Inyección en tiempo de ejecución o motor adaptado
├── examples/
│   └── demo_ibom.html           # Demo interactiva generada lista para previsualizar
├── pyproject.toml               # Empaquetado estándar para pip (console_scripts: kicad-ibom)
├── LICENSE                      # Licencia GPLv3 (compatible con upstream iBOM)
└── README.md                    # Documentación profesional en inglés con badges, GIF y ejemplos
```

---

## 💻 Especificación del CLI (`cli.py`)

La herramienta debe ser capaz de ejecutarse con cero parámetros o con opciones avanzadas:

### Uso 1: Cero Configuración (Zero-Config)
```bash
# Busca automáticamente el primer archivo *.kicad_pcb en el directorio actual
# y genera el HTML en ./bom/ o ./outputs/assembly/
kicad-ibom
```

### Uso 2: Parámetros Explícitos
```bash
kicad-ibom MiProyecto.kicad_pcb --output dist/ensamble.html --dark-mode --highlight-pin1 --include-nets --include-tracks
```

### Búsqueda Inteligente del Intérprete Python de KiCad:
1. **Windows:**
   * `C:\Program Files\KiCad\9.0\bin\python.exe`
   * `C:\Program Files\KiCad\8.0\bin\python.exe`
2. **macOS:**
   * `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`
3. **Linux:**
   * `python3` del sistema (con módulo `pcbnew` disponible vía apt/dnf).

---

## 📋 Instrucciones Paso a Paso para la Nueva Sesión de IA

Copiar y pegar este bloque al iniciar la nueva conversación:

```markdown
Hola Antigravity. En esta sesión vamos a desarrollar y publicar un nuevo repositorio de código abierto en GitHub llamado `kicad-ibom-generator` (bajo la marca CaliBeta).

### Contexto Técnico del Proyecto:
Es una herramienta CLI en Python para automatizar la generación del Interactive HTML BOM en KiCad 8 y KiCad 9+, resolviendo de forma nativa los bugs conocidos de KiCad 9 en modo headless (aserciones de m_group en footprints agrupados, anchos de vía sin argumento de capa en PCB_VIA::GetWidth, y registro en modo sin pantalla).

### Objetivos de la Sesión:
1. Crear la estructura del proyecto en una carpeta dedicada fuera del hardware anterior.
2. Implementar `kicad_ibom/cli.py` y `kicad_ibom/finder.py` con soporte completo de argumentos (`argparse`), auto-detección de archivos `*.kicad_pcb` y detección automática del intérprete de Python de KiCad en Windows/Linux/Mac.
3. Empaquetar el proyecto con `pyproject.toml` para que pueda ser instalado vía `pip install .` y usado como comando de terminal (`kicad-ibom`).
4. Redactar un `README.md` de nivel profesional en inglés con insignias (badges), guía de instalación, ejemplos de uso y llamada a la acción hacia servicios de diseño de hardware de CaliBeta.
5. Dejar el repositorio listo con su primer commit formal para subir a GitHub.
```

