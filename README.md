# 🧠 Memory Recall

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

**Portable memory for AI assistants.** Give any AI instant context about your codebase.

## 🚀 Install

```bash
# Clone and install globally (works like gh/vercel CLI)
git clone https://github.com/fnworks-dev/memory-recall.git
cd memory-recall
pip install .

# Now 'recall' works from anywhere
recall --help
```

## ⚡ Quick Start

```bash
# Pack your project
recall pack ~/projects/myapp --name myapp

# Get context for AI (paste into ChatGPT, Claude, etc.)
recall load
```

That's it. Your AI now knows your project.

## 📖 Commands

### Project Management
```bash
recall pack <path> --name <alias>   # Pack a project
recall list                          # List all projects
recall use <alias>                   # Switch projects
recall update                        # Re-pack current project
```

### Context for AI
```bash
recall load                    # Output context
recall load --at "2026-01-05"  # Time-travel to past state
recall show                    # View full details
```

### Search
```bash
recall find "query"            # BM25-ranked search
recall diff                    # Changes since last pack
recall deps <file>             # File dependencies
```

### Notes
```bash
recall describe "description"  # Set project description
recall note "decision"         # Log a decision
recall session "topic"         # Log session topic
```

### History
```bash
recall history                 # View past snapshots
recall queries                 # View search history
recall entity <file>           # View TODOs from code
```

## ✨ Features

- **Zero Dependencies** - Pure Python stdlib
- **BM25 Search** - Relevance-ranked results
- **Time Travel** - Load past project states
- **Entity Extraction** - Auto-extracts TODOs, notes from code
- **Multi-Project** - Switch between projects instantly

## 📁 Storage

```
~/.recall/
├── memories/          # Your .mem files
├── history/           # Snapshots for time-travel
├── queries.json       # Search history
└── current            # Active project
```

## 🛠️ Requirements

- Python 3.7+
- Git (optional, for `diff` command)

## 📜 License

MIT - see [LICENSE](LICENSE)

---

Made with ❤️ by [FNworks.dev](https://fnworks.dev)
