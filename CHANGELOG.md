# Changelog

All notable changes to Memory Recall will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-07

🎉 **First Public Release**

### Features
- **Zero Dependencies** - Pure Python stdlib, works anywhere
- **BM25 Search** - Results ranked by relevance using BM25 algorithm
- **History & Time-Travel** - `history` lists snapshots, `load --at` travels to past states
- **Query Logging** - All searches logged, view with `queries` command
- **Entity Extraction** - Extracts TODO/NOTE/FIXME/DECISION from comments and docstrings
- **Multi-Project Store** - Central `~/.recall/` directory for all projects
- **Project Switching** - `list`, `use`, `update` commands
- **Directory Overview** - Group files by directory with purpose detection
- **Project Description** - `describe` command for user-defined overview
- **Git Diff** - `diff` command shows changes since last pack
- **Dependency Map** - `deps` command shows file imports
- **Better Key File Detection** - Weighted scoring prioritizes API routes

### Commands
- `pack` - Create .mem file from project
- `list` - List all saved memories
- `use` - Switch active project
- `update` - Re-pack current project (creates snapshot)
- `load` - Output context for AI
- `load --at` - Time-travel to past state
- `describe` - Set project description
- `note` - Add decisions/notes
- `session` - Log session topics
- `show` - View full memory contents
- `find` - Search with BM25 ranking
- `diff` - Show changes since last pack
- `deps` - Show file dependencies
- `history` - List past snapshots
- `queries` - Show search history
- `entity` - Show facts about file

---

## Development History

Internal development versions (v1.0-v3.0) were consolidated into this public release.
See [Session 1 summary](https://github.com/fnworks-dev/memory-recall) for development notes.
