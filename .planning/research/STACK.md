# Technology Stack

**Project:** imessage-ai
**Researched:** 2026-02-16
**Confidence:** HIGH

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Python** | 3.10+ | Runtime | Minimum 3.10 required for sentence-transformers; 3.10-3.13 supported by all dependencies |
| **Typer** | 0.23.1 | CLI framework | Modern, type-hint-based CLI builder on top of Click. Zero boilerplate, automatic help text, FastAPI sibling. Perfect for Python 3.10+ projects. |
| **Rich** | 14.3.2 | Terminal output | Beautiful terminal formatting, tables, progress bars, markdown rendering. Standard for modern CLI tools. |
| **prompt_toolkit** | 3.0.52 | REPL interface | Powers interactive prompts with history, auto-completion, syntax highlighting. Standard for building Python REPLs. |

### AI & Embeddings

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Ollama Python** | 0.6.1 | Local LLM client | Official Ollama Python SDK with async support. Simplest integration for local models (llama3.2, mistral, etc). |
| **sentence-transformers** | 5.2.2 | Embedding generation | State-of-the-art local embeddings. 15,000+ pretrained models on HuggingFace. all-MiniLM-L6-v2 is fast, lightweight, production-ready. |
| **ChromaDB** | 1.5.0 | Vector database | Open-source, local-first vector DB. Simple API (4 core functions), built-in embedding support, file-system persistence. No server required. |

### Cloud LLM Clients (Optional)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **anthropic** | 0.79.0 | Claude API client | Official Anthropic SDK. Use for higher-quality responses when user opts in with API key. |
| **openai** | 2.21.0 | OpenAI API client | Official OpenAI SDK. Use for GPT-4 integration when user opts in with API key. |

### Data & Validation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Pydantic** | 2.12.5 | Data validation | Runtime type validation with type hints. 5-50x faster than v1 (Rust core). Standard for Python data validation. |
| **Python stdlib sqlite3** | (builtin) | SQLite access | Built-in, no dependencies. chat.db is SQLite, no ORM needed for read-only queries. |

### Development & Packaging

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest** | 9.0.2 | Testing framework | Industry standard. Fixtures, parametrization, async support. Requires Python 3.10+. |
| **setuptools** | >=70.0.0 | Build backend | Standard build backend for pyproject.toml. Use [build-system] with setuptools.build_meta. |
| **build** | latest | Build tool | PEP 517 builder. Use `python -m build` for creating sdist/wheels for PyPI and Homebrew. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| CLI Framework | Typer | Click | Typer is built on Click but uses type hints instead of decorators. Less boilerplate, more Pythonic for 3.10+. |
| CLI Framework | Typer | argparse | argparse is verbose and stdlib-only. Typer provides better DX with type hints + automatic validation. |
| Vector DB | ChromaDB | LangChain | LangChain has 400+ dependencies and heavyweight abstractions. For this project, ChromaDB + direct LLM clients is simpler. |
| Vector DB | ChromaDB | Pinecone/Weaviate | Cloud-first. This is local-first project. ChromaDB runs in-process with file-system persistence. |
| Embeddings | sentence-transformers | OpenAI embeddings | sentence-transformers runs locally, no API key required. Aligns with local-first philosophy. |
| REPL | prompt_toolkit | Custom readline wrapper | prompt_toolkit is battle-tested (powers IPython, ptpython). Handles edge cases (multiline, history, keybindings). |
| Terminal Output | Rich | colorama/termcolor | Rich provides tables, progress bars, markdown rendering, not just colors. Modern standard. |
| LLM Framework | Direct API clients | LangChain | LangChain adds complexity and 400+ dependencies. This project needs: chat, embeddings, RAG patterns. Direct clients are sufficient. |

## Installation

### Production Dependencies

```bash
# Core CLI
pip install typer==0.23.1 rich==14.3.2 prompt-toolkit==3.0.52

# AI & Embeddings
pip install ollama==0.6.1 sentence-transformers==5.2.2 chromadb==1.5.0

# Optional: Cloud LLM clients
pip install anthropic==0.79.0 openai==2.21.0

# Data validation
pip install pydantic==2.12.5
```

### Development Dependencies

```bash
# Testing
pip install pytest==9.0.2 pytest-asyncio pytest-cov

# Build tools
pip install build twine
```

### pyproject.toml Example

```toml
[build-system]
requires = ["setuptools>=70.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "imessage-ai"
version = "0.1.0"
description = "Chat with your iMessage history using AI"
requires-python = ">=3.10"
dependencies = [
    "typer>=0.23.1",
    "rich>=14.3.2",
    "prompt-toolkit>=3.0.52",
    "ollama>=0.6.1",
    "sentence-transformers>=5.2.2",
    "chromadb>=1.5.0",
    "pydantic>=2.12.5",
]

[project.optional-dependencies]
cloud = [
    "anthropic>=0.79.0",
    "openai>=2.21.0",
]
dev = [
    "pytest>=9.0.2",
    "pytest-asyncio",
    "pytest-cov",
    "build",
    "twine",
]

[project.scripts]
imessage-ai = "imessage_ai.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

## Python Version Decision

**Minimum: Python 3.10**

Rationale:
- sentence-transformers requires 3.10+ (verified: PyPI states ">=3.10")
- pytest 9.0.2 requires 3.10+
- All other dependencies support 3.10-3.14
- 3.10 introduced pattern matching, better type hints (useful for CLI parsing)
- Homebrew Python formula typically uses latest stable (3.12-3.13 in 2026)

**Target: Python 3.10-3.13**

Do NOT target 3.14 yet:
- Pydantic v2 has limited 3.14 support (v1 incompatible)
- Let ecosystem mature on 3.14 before adopting

## Homebrew Distribution Notes

For Homebrew tap distribution:
1. Package must be on PyPI with sdist (not just wheels)
2. Use `python -m build` to create sdist + wheel
3. Use homebrew-pypi-poet to generate Ruby formula
4. Define entry point in `[project.scripts]` (see above)
5. Test formula in fresh venv before publishing to tap

Homebrew will install dependencies via pip, so keep dependency tree lean.

## Architecture Notes

### No LangChain Justification

LangChain provides:
- LLM abstraction (chat, streaming, embeddings)
- Vector store abstraction (ChromaDB, Pinecone, etc)
- RAG chains (retrieval + generation)
- 400+ transitive dependencies

This project needs:
- Chat with Ollama: `ollama.chat()` (5 lines)
- Embeddings: `SentenceTransformer.encode()` (2 lines)
- Vector store: ChromaDB API (4 functions)
- RAG pattern: Query ChromaDB, pass results to LLM (10 lines)

**Decision:** Use direct API clients. LangChain is overkill and adds 400+ dependencies for features we don't need.

### RAG Pattern (Without LangChain)

```python
# Simple RAG implementation (no framework needed)
from chromadb import Client
from sentence_transformers import SentenceTransformer
import ollama

# 1. Embed query
embedder = SentenceTransformer('all-MiniLM-L6-v2')
query_embedding = embedder.encode("What did Alice say about vacation?")

# 2. Retrieve relevant messages
collection = client.get_collection("imessages")
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=5
)

# 3. Generate response
context = "\n".join(results['documents'][0])
response = ollama.chat(model='llama3.2', messages=[
    {"role": "system", "content": f"Context:\n{context}"},
    {"role": "user", "content": "What did Alice say about vacation?"}
])
```

This is the entire RAG pipeline. No framework needed.

## Confidence Assessment

| Component | Confidence | Source |
|-----------|------------|--------|
| Typer 0.23.1 | HIGH | PyPI official page, released Feb 13 2026 |
| Rich 14.3.2 | HIGH | PyPI official page, released Feb 1 2026 |
| prompt_toolkit 3.0.52 | HIGH | PyPI official page, released Aug 27 2025 |
| Ollama 0.6.1 | HIGH | PyPI official page, released Nov 13 2025 |
| sentence-transformers 5.2.2 | HIGH | PyPI official page, released Jan 27 2026 |
| ChromaDB 1.5.0 | HIGH | PyPI official page, released Feb 9 2026 |
| anthropic 0.79.0 | HIGH | PyPI official page, released Feb 7 2026 |
| openai 2.21.0 | HIGH | PyPI official page, released Feb 14 2026 |
| Pydantic 2.12.5 | HIGH | PyPI official page, released Nov 26 2025 |
| pytest 9.0.2 | HIGH | PyPI official page, released Dec 6 2025 |
| Python 3.10 minimum | HIGH | Verified against all dependency requirements |
| No LangChain decision | MEDIUM | Based on dependency analysis + WebSearch consensus on lightweight alternatives |
| Homebrew distribution | MEDIUM | WebSearch findings on pyproject.toml + homebrew-pypi-poet workflow |

## Sources

### Official Documentation (HIGH confidence)
- Typer: https://pypi.org/project/typer/
- Rich: https://pypi.org/project/rich/
- prompt_toolkit: https://pypi.org/project/prompt-toolkit/
- Ollama Python: https://pypi.org/project/ollama/
- sentence-transformers: https://pypi.org/project/sentence-transformers/
- ChromaDB: https://pypi.org/project/chromadb/
- anthropic: https://pypi.org/project/anthropic/
- openai: https://pypi.org/project/openai/
- Pydantic: https://pypi.org/project/pydantic/
- pytest: https://pypi.org/project/pytest/

### Ecosystem Research (MEDIUM confidence)
- [Python CLI Tools with Click and Typer: Complete Guide 2026](https://devtoolbox.dedyn.io/blog/python-click-typer-cli-guide)
- [Typer Official Docs](https://typer.tiangolo.com/)
- [Embeddings and Vector Databases With ChromaDB – Real Python](https://realpython.com/chromadb-vector-database/)
- [GitHub - chroma-core/chroma](https://github.com/chroma-core/chroma)
- [Ollama Python library](https://github.com/ollama/ollama-python)
- [Python Prompt Toolkit Documentation](https://python-prompt-toolkit.readthedocs.io/en/master/)
- [Rich GitHub Repository](https://github.com/Textualize/rich)
- [Building CLI Tools with Typer and Rich](https://dasroot.net/posts/2026/01/building-cli-tools-with-typer-and-rich/)
- [Python Packaging Best Practices 2026](https://dasroot.net/posts/2026/01/python-packaging-best-practices-setuptools-poetry-hatch/)
- [Publishing a Python CLI Tool to Homebrew](https://safjan.com/publishing-python-cli-tool-to-homebrew/)
- [33 LangChain Alternatives That Won't Leak Your Data (2026 Guide)](https://blog.premai.io/33-langchain-alternatives-that-wont-leak-your-data-2026-guide/)
- [Building RAG Applications with Python: Complete 2026 Guide](https://www.askpython.com/python/examples/building-rag-applications-with-python)

### Community Patterns (MEDIUM confidence)
- [imessage-reader PyPI](https://pypi.org/project/imessage-reader/)
- [SentenceTransformers HuggingFace](https://huggingface.co/sentence-transformers)
- [pytest Best Practices 2026](https://medium.com/@inprogrammer/best-python-testing-tools-2026-updated-884dcb78b115)
