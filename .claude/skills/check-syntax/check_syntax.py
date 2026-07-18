#!/usr/bin/env python3
"""Validate Python syntax for one or more files via ast.parse, without executing them.

Usage: check_syntax.py <file> [<file> ...]
"""
import ast
import sys


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <file> [<file> ...]", file=sys.stderr)
        return 2

    failed = False
    for path in sys.argv[1:]:
        try:
            with open(path, "r") as f:
                source = f.read()
            ast.parse(source, filename=path)
            print(f"OK: {path}")
        except SyntaxError as e:
            failed = True
            print(f"SYNTAX ERROR in {path}: {e}", file=sys.stderr)
        except OSError as e:
            failed = True
            print(f"ERROR reading {path}: {e}", file=sys.stderr)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
