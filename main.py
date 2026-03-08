"""
main.py — Orchestrator for ai-doc-gen.

Flow:
  1. Parse CLI args
  2. Verify Ollama + pull model
  3. Scan source files (generator)
  4. Build ASCII project tree (cross-platform)
  5. Aggregate source context
  6. Generate per-module docs → docs/<path>.md
  7. Generate README.md (references doc files)
  8. Write docs/index.md
"""

import logging
import sys
from pathlib import Path

from src.cli import parse_args
from src.llm import ensure_ollama, ensure_model, generate_readme, generate_module_doc
from src.scanner import (
    load_ignore_patterns,
    iter_source_files,
    build_tree,
    aggregate_context,
)
from src.utils import logger, ProgressBar
from src.writer import (
    ensure_docs_dir,
    write_module_doc,
    write_readme,
    write_docs_index,
)


def main() -> None:
    args = parse_args()

    # ── Logging verbosity ──────────────────────────────────────────────────
    if args.verbose:
        logging.getLogger("doc_gen").setLevel(logging.DEBUG)

    # ── Path resolution ────────────────────────────────────────────────────
    root: Path = Path(args.root).resolve()
    docs_dir: Path = root / args.output

    if not root.is_dir():
        logger.error(f"Not a valid directory: {root}")
        sys.exit(1)

    # ── Banner ─────────────────────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════╗")
    print("║      🤖  AI Doc Generator v1.0       ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Root    : {root}")
    print(f"  Output  : {docs_dir}")
    print(f"  Model   : {args.model}")
    print()

    # ── Step 1: Environment ────────────────────────────────────────────────
    ensure_ollama()
    ensure_model(args.model)

    # ── Step 2: Load ignore patterns ───────────────────────────────────────
    ignore = load_ignore_patterns(args.ignore_file)
    logger.info(f"Ignoring {len(ignore)} directory/file patterns")

    # ── Step 3: Scan source files (lazy generator → materialize once) ──────
    logger.info("Scanning source files…")
    source_files: list[Path] = list(iter_source_files(root, ignore))

    if not source_files:
        logger.error("No source files found. Check --ignore-file or supported extensions.")
        sys.exit(1)

    logger.info(f"Found {len(source_files)} source file(s)")

    # ── Step 4: Build tree (pure Python, cross-platform) ──────────────────
    logger.info("Building project tree…")
    tree: str = build_tree(root, ignore)
    logger.debug(f"\n{tree}")

    # ── Step 5: Aggregate context ─────────────────────────────────────────
    logger.info("Aggregating source context…")
    context, file_count = aggregate_context(source_files, root, args.max_file_chars)
    logger.info(f"Context ready — {file_count} files, {len(context):,} chars")

    # ── Step 6: Prepare output directory ──────────────────────────────────
    ensure_docs_dir(docs_dir)

    # ── Step 7: Generate per-module docs ──────────────────────────────────
    logger.info(f"\n📂 Generating module docs → {docs_dir.relative_to(root)}/")
    print()

    doc_files: list[Path] = []
    bar = ProgressBar(total=len(source_files), label="module docs")

    for file_path in source_files:
        rel = file_path.relative_to(root)
        logger.debug(f"  Processing: {rel}")
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            doc_content = generate_module_doc(file_path, content, args.model)
            out = write_module_doc(file_path, doc_content, root, docs_dir)
            doc_files.append(out)
        except Exception as exc:
            logger.warning(f"  Skipped {rel}: {exc}")
        bar.step()

    bar.done()
    print()

    # ── Step 8: Generate README.md ────────────────────────────────────────
    logger.info("📄 Generating README.md…")
    doc_refs = [
        str(f.relative_to(docs_dir)) for f in sorted(doc_files)
    ]
    readme_content = generate_readme(context, tree, doc_refs, args.model)
    write_readme(readme_content, root)

    # ── Step 9: Write docs/index.md ───────────────────────────────────────
    write_docs_index(doc_files, docs_dir, root)

    # ── Done ───────────────────────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════╗")
    print("║         ✅  Generation Complete       ║")
    print("╚══════════════════════════════════════╝")
    print(f"  README.md  : {root / 'README.md'}")
    print(f"  Module docs: {docs_dir} ({len(doc_files)} files)")
    print(f"  Index      : {docs_dir / 'index.md'}")
    print()


if __name__ == "__main__":
    main()
