#!/bin/sh
# 🧠 Recall Auto-Pack Hook
# This hook automatically updates the recall memory after each commit.
#
# INSTALLATION:
#   1. Copy this file to your project's .git/hooks/post-commit
#   2. Make it executable: chmod +x .git/hooks/post-commit
#
# Or install globally:
#   git config --global core.hooksPath ~/.git-hooks
#   mkdir -p ~/.git-hooks && cp this_file ~/.git-hooks/post-commit

# Check if recall is installed
if ! command -v recall &> /dev/null; then
    exit 0
fi

# Check if this project has a .mem file
if [ -f "*.mem" ] || recall list 2>/dev/null | grep -q "$(basename $(pwd))"; then
    echo "🧠 Updating recall memory..."
    recall update 2>/dev/null || true
fi
