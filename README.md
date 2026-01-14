# 🧠 Memory Recall

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)]()

**Portable memory for AI assistants.** Pack your codebase into a single `.mem` file that gives AI instant context about your project structure, dependencies, and key files.

---

## 📋 TL;DR - Concepts

### What is a Memory?
A **Memory** (`.mem` file) is a compressed snapshot of your project containing:
- Tech stack (React, Next.js, Supabase, etc.)
- File structure and key files
- Function/class index for search
- Import graph for dependency tracking

**One memory per project.** Can be stored locally in project folder or centrally in `~/.recall/memories/`.

### What is a Snapshot?
A **Snapshot** is a saved version of a memory (for time-travel). Created automatically when you run `recall update`.

### Command Summary

| Action | Command | Creates |
|--------|---------|---------|
| **Create memory** | `recall init` or `recall pack --name alias` | Memory + Auto-switch + Context |
| **Update memory** | `recall update` | Snapshot + updated Memory |
| **Read memory** | `recall load` | Nothing (just outputs) |
| **Time-travel** | `recall load --at 2026-01-05` | Nothing (reads old snapshot) |
| **Delete memory** | `recall clear` | Nothing (removes files) |

---

## 🤖 For AI Assistants

> **IMPORTANT**: If you're an AI assistant (ChatGPT, Claude, Cursor, etc.), read this first.

### Quick Workflow

```bash
cd ~/myproject
recall pack --name myproject    # Creates memory, auto-switches, shows context
recall deps <filename>          # See dependencies before editing
```

That's it. `recall pack` now shows the full project context, so you don't need a separate `recall load`.

### Before Modifying ANY File

```bash
recall deps <filename>         # See what imports this file AND what depends on it
```

This prevents breaking changes. The `deps` command shows:
- 🔽 **Imports** - What this file uses
- 🔼 **Imported by** - What files depend on this (CRITICAL for avoiding breaks)
- ⚠️ **Change impact** - How many files could be affected

### Quick Reference

| When | Command | Why |
|------|---------|-----|
| Starting session | `cd project && recall load` | Loads local .mem or central project |
| Starting session | `recall pack --name X` | Pack to central + auto-switch + show context |
| Before editing | `recall deps <file>` | See dependencies + impact |
| Looking for code | `recall find "query"` | BM25-ranked search |
| Check what changed | `recall diff` | Files modified since last pack |

---

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
# Option 1: Local .mem file (stays in project folder)
cd ~/projects/myapp
recall pack                    # Creates myapp.mem locally
recall load                    # Loads from current folder

# Option 2: Central store (accessible from anywhere)
recall pack ~/projects/myapp --name myapp
recall deps lib/auth.ts        # Works from any folder
```

That's it. Your AI now knows your project.

---

## 📖 Commands

### Project Management
```bash
recall init                          # Initialize memory for current directory
recall init --name myalias           # Initialize with custom alias
recall pack <path> --name <alias>    # Pack project, auto-switch, and show context
recall list                          # List all projects
recall use <alias>                   # Switch projects (usually not needed)
recall update                        # Re-pack current project
recall clear <alias>                 # Remove a memory (with confirmation)
recall clear                         # Interactive selector to pick which to delete
recall clear <alias> -f              # Remove without confirmation
```

### Context for AI
```bash
recall load                    # Loads local .mem, or central project if no local file
recall load --at "2026-01-05"  # Time-travel to past state
recall show                    # View full details
```

### Dependencies & Search
```bash
recall deps <file>             # Show imports AND what depends on this file
recall deps supabase           # Partial names work! Finds lib/supabase/client.ts
recall deps --top              # Show top 10 most-depended-on files
recall find "query"            # BM25-ranked search
recall diff                    # Changes since last pack
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

---

## 🔄 Typical Workflow

### 1. Starting a Session
```bash
$ cd ~/projects/myapp
$ recall pack --name myapp

📦 Packing myapp...
✅ Created myapp.mem (12.3 KB)
   371 files, 96,987 lines indexed
   Active project: myapp

# Project: myapp
Updated: 2026-01-14

## Stack
- Frontend: React, Next.js
- Backend: Supabase
- Language: TypeScript

## Directory Overview
- `components/` (253 files) - UI components
- `pages/` (61 files) - Page routes
- `lib/` (28 files) - Core libraries
...
```

### 2. Before Editing a File
```bash
$ recall deps lib/auth.ts

📁 lib/auth.ts
   🔽 Imports (3 dependencies):
      ← ./supabase
      ← ./types
   🔼 Imported by (12 files):
      → pages/login.tsx
      → pages/dashboard.tsx
      → components/ProtectedRoute.tsx
      ...
   ⚠️  Change impact: 12 files depend on this
```

### 3. Searching for Code
```bash
$ recall find "authentication"

📁 Files (ranked by relevance):
   lib/auth.ts (0.85)
   pages/login.tsx (0.72)

⚡ Functions:
   useAuth
   validateToken
```

---

## ✨ Features

- **Zero Dependencies** - Pure Python stdlib
- **BM25 Search** - Relevance-ranked results
- **Reverse Dependencies** - See what files depend on any file
- **Time Travel** - Load past project states
- **Entity Extraction** - Auto-extracts TODOs, notes from code
- **Local or Central** - Store .mem in project folder or central `~/.recall/`
- **Auto-Discovery** - `recall load` finds local .mem files automatically

## 📁 Storage

```
# Local mode (stays in your project)
~/projects/myapp/myapp.mem

# Central mode (accessible from anywhere)
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
