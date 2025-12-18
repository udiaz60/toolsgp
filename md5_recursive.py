#!/usr/bin/env python3
"""
md5_recursive.py

Recorre recursivamente un directorio y calcula el hash MD5 de cada archivo.
- Solo lectura: no modifica ni elimina archivos.
- Imprime en stdout líneas con el formato estándar:

  <md5sum><two spaces><ruta_relativa_o_absoluta>

Opciones:
  -r, --root      Directorio raíz (por defecto: .)
  -a, --absolute  Imprimir rutas absolutas en lugar de relativas
  -s, --sort      Ordenar la salida por ruta (por defecto: sí)
  --follow-symlinks  Seguir enlaces simbólicos (por defecto: no)

Ejemplo:
  python3 md5_recursive.py -r /mi/carpeta
"""

from __future__ import annotations
import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Iterable, List, Tuple, Optional


CHUNK_SIZE = 8192


def compute_md5(path: Path) -> Optional[str]:
    try:
        h = hashlib.md5()
        with path.open('rb') as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        # No raise: report error by returning None
        print(f"Advertencia: no se pudo leer '{path}': {e}", file=sys.stderr)
        return None


def iter_files(root: Path, follow_symlinks: bool = False) -> Iterable[Path]:
    # Usamos os.walk para poder controlar followlinks y no depender de rglob
    for dirpath, dirnames, filenames in os.walk(root, followlinks=follow_symlinks):
        for name in filenames:
            p = Path(dirpath) / name
            # Asegurar que sea un archivo regular (evitar dispositivos, tuberías, etc.)
            try:
                if p.is_file():
                    yield p
            except Exception:
                # Ignorar archivos problemáticos
                continue


def collect_hashes(root: Path, follow_symlinks: bool = False) -> List[Tuple[Path, Optional[str]]]:
    results: List[Tuple[Path, Optional[str]]] = []
    for file_path in iter_files(root, follow_symlinks=follow_symlinks):
        md5 = compute_md5(file_path)
        results.append((file_path, md5))
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Calcula MD5 recursivamente (solo lectura).")
    parser.add_argument('-r', '--root', default='.', help='Directorio raíz a recorrer (por defecto: .)')
    parser.add_argument('-a', '--absolute', action='store_true', help='Imprimir rutas absolutas en la salida')
    parser.add_argument('-s', '--sort', action='store_true', default=True, help='Ordenar salida por ruta (por defecto: sí)')
    parser.add_argument('--no-sort', dest='sort', action='store_false', help='No ordenar la salida')
    parser.add_argument('--follow-symlinks', action='store_true', help='Seguir enlaces simbólicos (puede causar bucles)')
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.exists():
        print(f"El directorio raíz '{root}' no existe.", file=sys.stderr)
        return 2

    # Recolectar hashes
    entries = collect_hashes(root, follow_symlinks=args.follow_symlinks)

    # Ordenar por ruta (opcional)
    if args.sort:
        entries.sort(key=lambda t: str(t[0]))

    # Imprimir resultados en el formato: <md5><two spaces><path>
    printed = 0
    failed = 0
    for path, md5 in entries:
        display_path = str(path.resolve()) if args.absolute else str(path.relative_to(root))
        if md5 is None:
            print(f"{'0'*32}  {display_path}  # ERROR")
            failed += 1
        else:
            print(f"{md5}  {display_path}")
            printed += 1

    # Resumen en stderr
    print(file=sys.stderr)
    print(f"Total procesados : {len(entries)}", file=sys.stderr)
    print(f"Hashes calculados: {printed}", file=sys.stderr)
    print(f"Errores          : {failed}", file=sys.stderr)

    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\nInterrumpido por el usuario.', file=sys.stderr)
        sys.exit(2)
