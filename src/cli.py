"""
cli.py — Argument parsing.
"""

import argparse

# Immutable defaults — use frozenset where applicable
_DEFAULTS: dict = {
    "root": ".",
    "output": "docs",
    "model": "llama3.1",
    "max_file_chars": 6_000,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="ai-doc-gen",
        description="🤖 AI Documentation Generator — Local & Private via Ollama",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py /path/to/project\n"
            "  python main.py /path/to/project --model mistral --output my_docs\n"
        ),
    )

    p.add_argument(
        "root",
        nargs="?",
        default=_DEFAULTS["root"],
        help="Root directory of the project to document (default: current dir)",
    )
    p.add_argument(
        "--output",
        default=_DEFAULTS["output"],
        metavar="DIR",
        help=f"Output docs folder inside the analyzed project (default: {_DEFAULTS['output']})",
    )
    p.add_argument(
        "--model",
        default=_DEFAULTS["model"],
        metavar="MODEL",
        help=f"Ollama model name (default: {_DEFAULTS['model']})",
    )
    p.add_argument(
        "--ignore-file",
        metavar="FILE",
        help="Path to a text file with extra ignore patterns (one per line)",
    )
    p.add_argument(
        "--max-file-chars",
        type=int,
        default=_DEFAULTS["max_file_chars"],
        metavar="N",
        help=f"Max characters read per source file (default: {_DEFAULTS['max_file_chars']})",
    )
    p.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable DEBUG-level logging",
    )

    return p.parse_args()
