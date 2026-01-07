# 🧠 Memory Recall

[![PyPI version](https://img.shields.io/pypi/v/memory-recall.svg)](https://pypi.org/project/memory-recall/)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

**Portable memory for AI assistants.** Give any AI instant context about your codebase.

```bash
pip install memory-recall
recall pack /your/project --name my-project
recall load
```

## ✨ Features

- 🚀 **Zero Dependencies** - Pure Python stdlib, works anywhere
- 📦 **Single File Memory** - Everything in one portable `.mem` file
- 🔍 **BM25 Search** - Relevance-ranked results
- ⏰ **Time Travel** - Load past states of your project
- 📝 **Entity Extraction** - Auto-extracts TODOs, notes, decisions from code
- 🔄 **Multi-Project** - Switch between projects instantly

## 🚀 Installation

```bash
# Install from PyPI
pip install memory-recall

# Or clone and use directly
git clone https://github.com/fnworks-dev/memory-recall.git
python3 recall.py pack /path/to/project --name my-project
```

## 📖 Usage

### Quick Start

```bash
# Pack your project
recall pack ~/projects/frontend --name frontend

# Get context for AI (copy & paste to ChatGPT, Claude, etc.)
recall load

# That's it! Your AI now knows your project.
```

### Project Management

```bash
recall pack ~/projects/backend --name backend   # Pack a project
recall list                                      # List all projects
recall use frontend                              # Switch projects
recall update                                    # Re-pack (creates snapshot)
```

### Getting Context for AI

```bash
recall load                    # Output context for current project
recall load --at "2026-01-05"  # Time-travel to past state
recall show                    # View full memory details
```

### Search & Analysis

```bash
recall find "authentication"   # BM25-ranked search
recall diff                    # Changes since last pack
recall deps pages/api/auth.ts  # File dependencies
recall queries                 # View search history
```

### Notes & Sessions

```bash
recall describe "E-commerce platform with React and Node"
recall note "Using Supabase for auth instead of JWT"
recall session "Fixed payment flow, added Stripe integration"
```

### Entity Tracking

```bash
recall entity pages/api/       # View TODOs, notes from code
recall history                 # View project snapshots
```

## 📁 How It Works

Memory Recall scans your codebase and creates a compressed `.mem` file containing:

- **Project Summary** - Auto-detected stack, file counts, line counts
- **Directory Overview** - Purpose of each directory
- **Key Files** - Important files ranked by relevance
- **Search Index** - BM25 corpus for fast search
- **Entities** - TODOs, notes, decisions from comments
- **Your Notes** - Decisions and session logs you add

```
~/.recall/
├── memories/
│   ├── frontend.mem     # Your projects
│   └── backend.mem
├── history/
│   └── frontend/        # Historical snapshots
│       └── 20260107_120000.mem
├── queries.json         # Search history
└── current              # Active project
```

## 📊 Example Output

```markdown
# Project: frontend
Updated: 2026-01-07

## Description
E-commerce platform with React frontend and Supabase backend

## Summary
frontend: | Stack: React, Next.js, Supabase, TypeScript | 371 files, 96,987 lines

## Directory Overview
- `components/` (253 files) - UI components
- `pages/` (61 files) - API endpoints, Routes
- `lib/` (28 files) - Core libraries

## Key Files
- `pages/api/auth/login.ts` - API endpoint
- `lib/supabase.ts` - Core library
- `components/Cart.tsx` - UI component

## Decisions
- [2026-01-07] Using Supabase for auth
```

## 🛠️ Requirements

- Python 3.7+
- Git (optional, for `diff` command)

## 📜 License

MIT License - see [LICENSE](LICENSE)

## 🔗 Links

- [PyPI Package](https://pypi.org/project/memory-recall/)
- [Changelog](CHANGELOG.md)
- [FNworks.dev](https://fnworks.dev)

---

Made with ❤️ by [FNworks.dev](https://fnworks.dev)
