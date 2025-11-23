#!/usr/bin/env python3
"""
Script di build per creare il pacchetto .mcpb per Claude Desktop.

Uso:
    python build.py [--output NOME]

Crea un archivio ZIP con estensione .mcpb contenente:
- manifest.json
- server/ (codice Python)
- lib/ (dipendenze bundled)
- icon.svg
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def install_dependencies(lib_dir: Path):
    """Installa le dipendenze Python nella directory lib/."""
    requirements = Path(__file__).parent / "requirements.txt"

    if not requirements.exists():
        print("ATTENZIONE: requirements.txt non trovato, salto l'installazione delle dipendenze")
        return

    print(f"Installazione dipendenze in {lib_dir}...")

    # Installa le dipendenze nella directory lib
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "-r", str(requirements),
        "--target", str(lib_dir),
        "--quiet"
    ], check=True)

    print(f"Dipendenze installate in {lib_dir}")


def create_mcpb(output_name: str = None, include_deps: bool = False):
    """Crea il file .mcpb."""
    project_dir = Path(__file__).parent

    # Leggi il manifest per ottenere nome e versione
    manifest_path = project_dir / "manifest.json"
    if not manifest_path.exists():
        print("ERRORE: manifest.json non trovato")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    name = manifest.get("name", "extension")
    version = manifest.get("version", "1.0.0")

    # Nome del file output
    if output_name:
        output_file = output_name if output_name.endswith(".mcpb") else f"{output_name}.mcpb"
    else:
        output_file = f"{name}-{version}.mcpb"

    output_path = project_dir / "dist" / output_file
    output_path.parent.mkdir(exist_ok=True)

    # Crea un archivio ZIP
    print(f"Creazione {output_file}...")

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Aggiungi manifest.json
        zf.write(manifest_path, "manifest.json")
        print("  + manifest.json")

        # Aggiungi la directory server/
        server_dir = project_dir / "server"
        if server_dir.exists():
            for file_path in server_dir.rglob("*"):
                if file_path.is_file() and "__pycache__" not in str(file_path):
                    arc_name = file_path.relative_to(project_dir)
                    zf.write(file_path, arc_name)
                    print(f"  + {arc_name}")

        # Aggiungi l'icona se esiste
        icon_path = project_dir / "icon.svg"
        if icon_path.exists():
            zf.write(icon_path, "icon.svg")
            print("  + icon.svg")

        # Aggiungi requirements.txt per riferimento
        req_path = project_dir / "requirements.txt"
        if req_path.exists():
            zf.write(req_path, "requirements.txt")
            print("  + requirements.txt")

        # Opzionale: bundle delle dipendenze
        if include_deps:
            with tempfile.TemporaryDirectory() as tmp_dir:
                lib_dir = Path(tmp_dir) / "lib"
                lib_dir.mkdir()
                install_dependencies(lib_dir)

                for file_path in lib_dir.rglob("*"):
                    if file_path.is_file():
                        arc_name = "lib" / file_path.relative_to(lib_dir)
                        zf.write(file_path, arc_name)

    file_size = output_path.stat().st_size
    print(f"\nPacchetto creato: {output_path}")
    print(f"Dimensione: {file_size / 1024:.1f} KB")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Crea il pacchetto .mcpb per Claude Desktop")
    parser.add_argument("--output", "-o", help="Nome del file di output")
    parser.add_argument("--with-deps", action="store_true", help="Include le dipendenze nel pacchetto")

    args = parser.parse_args()

    create_mcpb(args.output, args.with_deps)


if __name__ == "__main__":
    main()
