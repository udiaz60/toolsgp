#!/usr/bin/env python3
"""
md5check.py

Script en Python para verificar hashes MD5 listados en archivos que comienzan
con "md5sum*.txt" (recursivamente). Reproduce la funcionalidad de
`md5check.ps1`:

- Busca archivos "md5sum*.txt" en el árbol de directorios
- Para cada línea no vacía ni comentario: extrae hash esperado y nombre de archivo
- Calcula MD5 del archivo relativo al directorio del archivo md5sum
- Imprime [OK]/[FAIL]/[NOT FOUND] y un resumen

Salida coloreada con códigos ANSI (sin dependencias externas).
"""

import hashlib
import os
import re
import sys
import argparse
from pathlib import Path

# Códigos ANSI simples para colores
COLORS = {
    'cyan': '\033[96m',
    'green': '\033[92m',
    'red': '\033[91m',
    'yellow': '\033[93m',
    'white': '\033[97m',
    'reset': '\033[0m',
}


def cprint(text: str, color: str = None) -> None:
    if color and color in COLORS:
        print(f"{COLORS[color]}{text}{COLORS['reset']}")
    else:
        print(text)


def compute_md5(file_path: Path) -> str | None:
    try:
        h = hashlib.md5()
        with file_path.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        cprint(f"Advertencia: error calculando hash de {file_path}: {e}", 'yellow')
        return None


def find_md5sum_files(root: Path = Path('.'), pattern: str = 'md5sum*.txt') -> list[Path]:
    # Buscar archivos que coincidan con pattern recursivamente
    return sorted(root.rglob(pattern))


def process_md5_file(md5file: Path) -> bool:
    cprint("================================================", 'cyan')
    cprint(f"Procesando: {md5file.resolve()}", 'cyan')
    cprint("================================================", 'cyan')

    base_dir = md5file.parent

    try:
        lines = md5file.read_text(encoding='utf-8', errors='replace').splitlines()
    except Exception as e:
        cprint(f"No se pudo leer {md5file}: {e}", 'red')
        return

    total = correctos = incorrectos = no_encontrados = 0

    pattern = re.compile(r'^([A-Fa-f0-9]{32})\s{2,}(.+)$')

    for line in lines:
        if not line.strip() or line.lstrip().startswith('#'):
            continue

        m = pattern.match(line)
        if not m:
            # Ignorar líneas que no respetan el formato esperado
            continue

        expected_hash = m.group(1).lower()
        filename = m.group(2).strip()
        total += 1

        file_path = (base_dir / filename).resolve()

        if file_path.exists():
            actual_hash = compute_md5(file_path)
            if actual_hash is None:
                # Error al calcular hash, contarlo como incorrecto
                cprint(f"[FAIL] {filename}", 'red')
                cprint(f"  Esperado: {expected_hash}", 'red')
                cprint(f"  Actual  : (error al calcular)", 'red')
                incorrectos += 1
            elif actual_hash.lower() == expected_hash:
                cprint(f"[OK]   {filename}", 'green')
                correctos += 1
            else:
                cprint(f"[FAIL] {filename}", 'red')
                cprint(f"  Esperado: {expected_hash}", 'red')
                cprint(f"  Actual  : {actual_hash}", 'red')
                incorrectos += 1
        else:
            cprint(f"[NOT FOUND] {filename}", 'yellow')
            no_encontrados += 1

    cprint("", None)
    cprint(f"Resumen para {md5file.name}:", 'cyan')
    cprint(f"  Total      : {total}", 'white')
    cprint(f"  Correctos  : {correctos}", 'green')
    cprint(f"  Incorrectos: {incorrectos}", 'red')
    cprint(f"  No encontr.: {no_encontrados}", 'yellow')
    cprint("", None)
    had_issue = (incorrectos > 0) or (no_encontrados > 0)
    return had_issue


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verifica MD5 según archivos md5sum*.txt. Modo sólo-lectura: NO copia, NO elimina ni altera archivos."
    )
    parser.add_argument('--root', '-r', default='.', help='Directorio raíz para buscar (por defecto: .)')
    parser.add_argument('--pattern', '-p', default='md5sum*.txt', help="Patrón de búsqueda para archivos md5 (ej. 'md5sum*.txt')")
    parser.add_argument('--quiet', '-q', action='store_true', help='Silenciar mensajes informativos')
    parser.add_argument('--fail-exit', action='store_true', help='Salir con código 2 si se detectan fallos o archivos no encontrados')
    args = parser.parse_args()

    root = Path(args.root)
    md5_files = find_md5sum_files(root, args.pattern)

    if not md5_files:
        cprint(f"No se encontraron archivos que coincidan con '{args.pattern}'", 'yellow')
        return 0

    if not args.quiet:
        cprint(f"Encontrados {len(md5_files)} archivo(s) md5sum", 'cyan')
        cprint("", None)

    had_issue = False

    for md5file in md5_files:
        if process_md5_file(md5file):
            had_issue = True

    if not args.quiet:
        cprint("Verificación completada.", 'cyan')

    if args.fail_exit and had_issue:
        return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        cprint("Interrumpido por el usuario.", 'yellow')
        sys.exit(2)
