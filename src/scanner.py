"""
scanner.py — Filesystem scanning: file discovery, tree building, context aggregation.

Design notes:
  - DEFAULT_IGNORE / DEFAULT_EXTENSIONS are frozensets (immutable, O(1) lookup).
  - iter_source_files is a generator → never loads all paths into memory at once.
  - build_tree is pure Python → no `tree` binary dependency (cross-platform).
"""

import os
from pathlib import Path
from typing import Generator, Iterable

from src.utils import logger, timer

# ──────────────────────────────────────────────
# Constants (immutable)
# ──────────────────────────────────────────────

DEFAULT_IGNORE: frozenset[str] = frozenset({
    ".git", ".hg", ".svn",
    "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "node_modules", ".venv", "venv", "env",
    "dist", "build", "output", ".next", ".nuxt",
    ".idea", ".vscode", ".DS_Store",
})

DEFAULT_EXTENSIONS: frozenset[str] = frozenset({
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".cpp", ".c", ".h", ".cs",
    ".rb", ".php", ".swift", ".kt",
})

_TREE_CONNECTORS = ("├── ", "└── ")
_TREE_PIPES      = ("│   ", "    ")


# ──────────────────────────────────────────────
# Ignore-list loader
# ──────────────────────────────────────────────

def load_ignore_patterns(ignore_file: str | None) -> frozenset[str]:
    """Merge DEFAULT_IGNORE with optional user-supplied patterns."""
    patterns: set[str] = set(DEFAULT_IGNORE)
    if ignore_file:
        p = Path(ignore_file)
        if p.exists():
            extra = {
                line.strip()
                for line in p.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.startswith("#")
            }
            patterns |= extra
            logger.debug(f"Loaded {len(extra)} extra ignore patterns from {p}")
        else:
            logger.warning(f"Ignore file not found: {ignore_file}")
    return frozenset(patterns)


# ──────────────────────────────────────────────
# File iterator (generator — memory-efficient)
# ──────────────────────────────────────────────

def iter_source_files(
    root: Path,
    ignore: frozenset[str],
    extensions: frozenset[str] = DEFAULT_EXTENSIONS,
) -> Generator[Path, None, None]:
    """
    Lazily yield source files under `root`, skipping ignored dirs.
    Uses os.walk with in-place dir mutation for efficient pruning.
    """
    for dirpath, dirs, files in os.walk(root):
        # Prune ignored directories in-place (avoids descending into them)
        dirs[:] = [d for d in dirs if d not in ignore]
        for fname in files:
            path = Path(dirpath) / fname
            if path.suffix in extensions:
                yield path


# ──────────────────────────────────────────────
# Pure-Python tree builder (cross-platform)
# ──────────────────────────────────────────────

def build_tree(
    root: Path,
    ignore: frozenset[str],
    _prefix: str = "",
    _max_depth: int = 4,
    _depth: int = 0,
) -> str:
    """
    Recursively build an ASCII directory tree without shelling out to `tree`.
    Works on Windows, macOS, and Linux identically.
    """
    if _depth > _max_depth:
        return ""

    lines: list[str] = []
    if _depth == 0:
        lines.append(str(root.name) or str(root))

    try:
        entries = sorted(
            [e for e in root.iterdir() if e.name not in ignore],
            key=lambda e: (e.is_file(), e.name.lower()),
        )
    except PermissionError:
        return ""

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = _TREE_CONNECTORS[1] if is_last else _TREE_CONNECTORS[0]
        lines.append(_prefix + connector + entry.name)

        if entry.is_dir():
            extension = _TREE_PIPES[1] if is_last else _TREE_PIPES[0]
            sub = build_tree(entry, ignore, _prefix + extension, _max_depth, _depth + 1)
            if sub:
                lines.append(sub)

    return "\n".join(lines)


# ──────────────────────────────────────────────
# Context aggregator
# ──────────────────────────────────────────────

@timer
def aggregate_context(
    files: Iterable[Path],
    root: Path,
    max_file_chars: int = 6_000,
) -> tuple[str, int]:
    """
    Read and concatenate source files into a single LLM context string.

    Returns:
        (context_string, file_count)
    """
    parts: list[str] = []
    count = 0

    for f in files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            rel = f.relative_to(root)
            parts.append(f"\n--- FILE: {rel} ---\n{content[:max_file_chars]}\n")
            count += 1
        except OSError as exc:
            logger.warning(f"Could not read {f}: {exc}")

    return "".join(parts), count
