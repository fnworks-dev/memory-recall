# 🧠 Memory Recall

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

**Portable memory for AI assistants.** Give any AI instant context about your codebase.

Inspired by [Memvid](https://github.com/memvid/memvid) but built for personal productivity with zero dependencies.

## ✨ Features

- 🚀 **Zero Dependencies** - Pure Python stdlib, works anywhere
- 📦 **Single File Memory** - Everything in one portable `.mem` file
- 🔍 **BM25 Search** - Relevance-ranked results
- ⏰ **Time Travel** - Load past states of your project
- 📝 **Entity Extraction** - Auto-extracts TODOs, notes, decisions from code
- 🔄 **Multi-Project** - Switch between projects instantly

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/fnworks-dev/memory-recall.git
cd memory-recall

# Pack your project
python3 recall.py pack /path/to/your/project --name my-project

# Get context for AI (copy & paste to ChatGPT, Claude, etc.)
python3 recall.py load

# That's it! Your AI now knows your project.
```

## 📖 Usage

### Project Management

```bash
# Pack a project to central store
recall pack ~/projects/frontend --name frontend

# List all saved projects
recall list

# Switch between projects
recall use frontend
recall use backend

# Update current project (creates snapshot)
recall update
```

### Getting Context for AI

```bash
# Output context for current project
recall load

# Time-travel to past state
recall load --at "2026-01-05"

# View full memory details
recall show
```

### Search & Analysis

```bash
# Search with BM25 ranking
recall find "authentication"

# Show changes since last pack
recall diff

# Show file dependencies
recall deps pages/api/auth.ts

# View search history
recall queries
```

### Notes & Sessions

```bash
# Add project description
recall describe "E-commerce platform with React frontend and Node backend"

# Log a decision
recall note "Using Supabase for auth instead of custom JWT"

# Log a session
recall session "Fixed payment flow, added Stripe integration"
```

### Entity Tracking

```bash
# View TODOs, notes, decisions extracted from code
recall entity pages/api/

# View project history
recall history
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
- `pages/api/auth/login.ts` - API endpoint (handler)
- `lib/supabase.ts` - Core library (createClient)
- `components/Cart.tsx` - UI component (Cart, useCart)

## Decisions
- [2026-01-07] Using Supabase for auth
- [2026-01-06] Switched to App Router
```

## 🆚 Recall vs Memvid

| Feature | Memvid | Recall |
|---------|--------|--------|
| **Purpose** | AI agent memory | Developer context |
| **Language** | Rust + SDKs | Pure Python |
| **Dependencies** | Many | Zero |
| **Search** | Hybrid (Lex + Vec) | BM25 |
| **Embeddings** | Required for semantic | Not needed |
| **Time-travel** | ✅ | ✅ |
| **Use case** | Production agents | Personal productivity |

Recall is intentionally simpler. If you need production-grade AI agent memory, use Memvid.

## 🛠️ Requirements

- Python 3.7+
- Git (optional, for `diff` command)

## 📜 License

MIT License - see [LICENSE](LICENSE)

## 🔗 Links

- [Changelog](CHANGELOG.md)
- [FNworks.dev](https://fnworks.dev)

---

Made with ❤️ by [FNworks.dev](https://fnworks.dev)
