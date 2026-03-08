"""
llm.py — Ollama inference: environment check, model pull, generation with streaming.

Design notes:
  - ensure_ollama() is cross-platform (Linux auto-install, macOS/Windows guided).
  - All generate calls use stream=True → real-time token progress in terminal.
  - _stream() is the single streaming helper used by every public function.
"""

import sys
import platform
import subprocess
from pathlib import Path

import ollama

from src.utils import logger, timer, log_step

# ──────────────────────────────────────────────
# Environment setup
# ──────────────────────────────────────────────

@log_step("Checking Ollama installation")
def ensure_ollama() -> None:
    """Verify Ollama is available; auto-install on Linux, guide on other OS."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info(f"Ollama found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        system = platform.system()
        logger.warning("Ollama not found on this system.")

        if system == "Linux":
            logger.info("Installing Ollama via official script…")
            subprocess.run(
                "curl -fsSL https://ollama.com/install.sh | sh",
                shell=True,
                check=True,
            )
            logger.info("Ollama installed successfully.")
        else:
            url = "https://ollama.com/download"
            logger.error(
                f"Automatic installation is only supported on Linux.\n"
                f"Please download Ollama for {system} at: {url}"
            )
            sys.exit(1)


@log_step("Pulling model")
def ensure_model(model: str) -> None:
    """Pull the requested model (no-op if already present locally)."""
    logger.info(f"Pulling '{model}' — skipped if already cached…")
    subprocess.run(["ollama", "pull", model], check=True)


# ──────────────────────────────────────────────
# Private streaming helper
# ──────────────────────────────────────────────

def _stream(prompt: str, model: str, label: str = "Generating") -> str:
    """
    Send a prompt to Ollama and stream the response token-by-token,
    printing live progress to the terminal.
    """
    response_gen = ollama.generate(
        model=model,
        prompt=prompt,
        options={"temperature": 0.0, "num_ctx": 8192},
        stream=True,
    )

    chunks: list[str] = []
    token_count = 0

    for chunk in response_gen:
        # ollama >= 0.1 returns GenerateResponse objects with .response attribute
        token: str = chunk.response if hasattr(chunk, "response") else chunk.get("response", "")
        chunks.append(token)
        token_count += 1
        if token_count % 25 == 0:
            print(f"\r  ↳ {label}: {token_count} tokens…", end="", flush=True)

    print(f"\r  ↳ {label}: {token_count} tokens ✓          ")
    return "".join(chunks)


# ──────────────────────────────────────────────
# Generation functions
# ──────────────────────────────────────────────

@timer
def generate_readme(
    context: str,
    tree: str,
    doc_refs: list[str],
    model: str,
) -> str:
    """
    Generate the main README.md for the project.

    Args:
        context:  Aggregated source code context.
        tree:     ASCII directory tree string.
        doc_refs: List of relative paths to per-module doc files (for linking).
        model:    Ollama model name.
    """
    doc_links = "\n".join(f"- [{ref}](docs/{ref})" for ref in doc_refs)

    prompt = f"""Act as a Lead Developer. Generate a complete, professional README.md.

Follow this EXACT structure — use Markdown headers:
# <Project Name>
## Description
## Clone & Install
## Environment Configuration (.env)
## Running the Project
## Architecture
## Documentation
List each module doc here:
{doc_links if doc_links else "(no module docs)"}

PROJECT TREE:
{tree}

SOURCE CODE:
{context}

Rules:
- Be concise and technical.
- Use code blocks for commands.
- Do NOT invent features not visible in the code.
"""
    logger.info("Sending README prompt to LLM…")
    return _stream(prompt, model, label="README.md")


@timer
def generate_module_doc(file_path: Path, content: str, model: str) -> str:
    """Generate technical documentation for a single source file."""
    prompt = f"""Act as a Lead Developer. Write concise Markdown documentation for this module.

Include:
- **Purpose** — what this module does
- **Key components** — functions/classes and their responsibilities
- **Dependencies** — imports and what they're used for
- **Usage example** — minimal working snippet

FILE: {file_path.name}

```
{content[:5000]}
```

Keep it under 400 words. No fluff.
"""
    return _stream(prompt, model, label=file_path.name)
