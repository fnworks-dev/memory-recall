# Changelog

All notable changes to Memory Recall will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-01-07

### Added
- **BM25 Search**: Results now ranked by relevance using BM25 algorithm
- **History & Time-Travel**: `history` command lists snapshots, `load --at` travels to past states
- **Query Logging**: All searches logged, view with `queries` command
- **Entity Extraction**: Extracts TODO/NOTE/FIXME/DECISION from comments and docstrings
- **Snapshot on Pack**: Every `update` creates a historical snapshot

### Changed
- Memory file size increased from ~20KB to ~36KB (includes search corpus)
- Version bumped to 2.5

## [2.0.0] - 2026-01-07

### Added
- **Multi-project Store**: Central `~/.recall/` directory for all projects
- **Project Switching**: `list`, `use`, `update` commands
- **Directory Overview**: Group files by directory with purpose detection
- **Project Description**: `describe` command for user-defined overview
- **File Search**: `find` command searches stored index
- **Git Diff**: `diff` command shows changes since last pack
- **Dependency Map**: `deps` command shows file imports
- **Better Key File Detection**: Weighted scoring prioritizes API routes

### Changed
- Memory format version bumped to 2.0
- Key files now sorted by importance score

## [1.0.0] - 2026-01-06

### Added
- Initial release
- `pack` - Create .mem file from project
- `load` - Output context for AI
- `note` - Add decisions/notes
- `session` - Log session topics
- `show` - View full memory contents
- Compressed JSON format (gzip + base64)
- Zero dependencies - pure Python stdlib
