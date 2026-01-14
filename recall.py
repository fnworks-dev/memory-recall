#!/usr/bin/env python3
"""
Recall v1.2.0 - Portable Memory for AI Assistants
Single-file memory with history, search, and entity tracking.

Usage:
    # Multi-project management
    python3 recall.py pack [path] --name [alias]  # Pack to central store
    python3 recall.py list                        # Show all saved memories
    python3 recall.py use [alias]                 # Switch active project
    python3 recall.py update                      # Re-pack current project
    
    # Context & notes
    python3 recall.py load [file.mem]             # Output context for AI
    python3 recall.py load --at "2026-01-05"      # Time-travel to past state
    python3 recall.py describe "description"      # Set project description
    python3 recall.py note "your note"            # Add a decision/note
    python3 recall.py session "topic"             # Log a session
    python3 recall.py show [file.mem]             # Show full memory contents
    
    # Search & analysis
    python3 recall.py find "query"                # Search with BM25 ranking
    python3 recall.py diff                        # Show changes since last pack
    python3 recall.py deps [file]                 # Show dependencies
    
    # History & entity tracking (v2.5)
    python3 recall.py history                     # List past snapshots
    python3 recall.py queries                     # Show search history
    python3 recall.py entity [file]               # Show facts about file
"""

import argparse
import ast
import json
import os
import re
import sys
import gzip
import base64
import subprocess
import math
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Set, Tuple

# === Configuration ===
MEM_EXTENSION = ".mem"
DEFAULT_MEM_FILE = "project.mem"
RECALL_HOME = Path.home() / ".recall"
MEMORIES_DIR = RECALL_HOME / "memories"
HISTORY_DIR = RECALL_HOME / "history"
QUERIES_FILE = RECALL_HOME / "queries.json"
CURRENT_FILE = RECALL_HOME / "current"

# File extensions to analyze
CODE_EXTENSIONS = {
    '.py', '.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte',
    '.go', '.rs', '.java', '.kt', '.swift', '.rb', '.php',
    '.css', '.scss', '.html', '.md', '.json', '.yaml', '.yml'
}

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.git', '.next', '__pycache__', 'dist', 'build',
    '.venv', 'venv', 'env', '.env', 'coverage', '.nyc_output',
    '.recall', '.cache', 'vendor', '.turbo'
}

# Key file scoring weights (higher = more important)
KEY_FILE_WEIGHTS = {
    'pages/api/': 10, '/api/': 8, 'lib/': 7, 'src/lib/': 7,
    'hooks/': 6, 'context/': 6, 'store/': 6, 'pages/': 5,
    'app/': 5, 'routes/': 5, 'utils/': 4, 'helpers/': 4,
    'services/': 5, 'components/': 3, 'styles/': 1, 'types/': 2,
    'test': 0, 'spec': 0, '__test': 0,
}

# Purpose detection patterns
PURPOSE_PATTERNS = [
    (r'pages/api/', 'API endpoint'), (r'/api/', 'API endpoint'),
    (r'auth|login|signup|signin', 'Authentication'),
    (r'hooks?/', 'React hook'), (r'context/', 'Context provider'),
    (r'store/', 'State management'), (r'lib/', 'Core library'),
    (r'services?/', 'Service layer'), (r'utils?/', 'Utility functions'),
    (r'helpers?/', 'Helper functions'), (r'types?/', 'Type definitions'),
    (r'components?/', 'UI component'), (r'pages?/', 'Page/Route'),
    (r'styles?/|\.css$|\.scss$', 'Styles'), (r'config', 'Configuration'),
    (r'middleware', 'Middleware'), (r'test|spec', 'Tests'),
]


# === BM25 Search Implementation ===

class BM25:
    """Simple BM25 implementation for ranking search results."""
    
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_lengths = [len(doc.split()) for doc in documents]
        self.avg_doc_length = sum(self.doc_lengths) / len(documents) if documents else 0
        self.doc_freqs = self._compute_doc_freqs()
        self.idf = self._compute_idf()
    
    def _compute_doc_freqs(self) -> Dict[str, int]:
        """Compute document frequency for each term."""
        df = Counter()
        for doc in self.documents:
            terms = set(doc.lower().split())
            for term in terms:
                df[term] += 1
        return df
    
    def _compute_idf(self) -> Dict[str, float]:
        """Compute IDF for each term."""
        idf = {}
        n = len(self.documents)
        for term, df in self.doc_freqs.items():
            idf[term] = math.log((n - df + 0.5) / (df + 0.5) + 1)
        return idf
    
    def score(self, query: str, doc_idx: int) -> float:
        """Compute BM25 score for a document given a query."""
        doc = self.documents[doc_idx]
        doc_terms = doc.lower().split()
        doc_length = self.doc_lengths[doc_idx]
        term_freqs = Counter(doc_terms)
        
        score = 0.0
        for term in query.lower().split():
            if term not in self.idf:
                continue
            tf = term_freqs.get(term, 0)
            idf = self.idf[term]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
            score += idf * (numerator / denominator) if denominator else 0
        
        return score
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """Search documents and return top-k results with scores."""
        scores = [(i, self.score(query, i)) for i in range(len(self.documents))]
        scores = [(i, s) for i, s in scores if s > 0]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# === Entity Extraction ===

def extract_entities(content: str, file_path: str, suffix: str) -> Dict[str, List[str]]:
    """Extract facts/entities from code comments and docstrings."""
    entities = {
        "todos": [],
        "notes": [],
        "decisions": [],
        "warnings": [],
        "descriptions": []
    }
    
    # Extract TODO, NOTE, FIXME, DECISION comments
    patterns = [
        (r'(?://|#)\s*TODO[:\s]+(.+?)(?:\n|$)', 'todos'),
        (r'(?://|#)\s*NOTE[:\s]+(.+?)(?:\n|$)', 'notes'),
        (r'(?://|#)\s*FIXME[:\s]+(.+?)(?:\n|$)', 'warnings'),
        (r'(?://|#)\s*DECISION[:\s]+(.+?)(?:\n|$)', 'decisions'),
        (r'(?://|#)\s*WARN(?:ING)?[:\s]+(.+?)(?:\n|$)', 'warnings'),
    ]
    
    for pattern, key in patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            entities[key].append(match.group(1).strip())
    
    # Extract docstrings (Python)
    if suffix == '.py':
        for match in re.finditer(r'"""([^"]+)"""', content):
            doc = match.group(1).strip()
            if len(doc) < 200:  # Only short docstrings
                entities["descriptions"].append(doc.split('\n')[0])
    
    # Extract JSDoc comments (JS/TS)
    if suffix in {'.ts', '.tsx', '.js', '.jsx'}:
        for match in re.finditer(r'/\*\*\s*\n?\s*\*?\s*([^*]+)\s*\*/', content):
            doc = match.group(1).strip()
            if len(doc) < 200:
                # Get first line
                first_line = doc.split('\n')[0].strip()
                if first_line and not first_line.startswith('@'):
                    entities["descriptions"].append(first_line)
    
    return entities


# === Recall Home Management ===

def ensure_recall_home() -> None:
    """Ensure ~/.recall directory structure exists."""
    MEMORIES_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def get_current_project() -> Optional[str]:
    """Get the currently active project alias."""
    if CURRENT_FILE.exists():
        return CURRENT_FILE.read_text().strip()
    return None


def set_current_project(alias: str) -> None:
    """Set the currently active project."""
    ensure_recall_home()
    CURRENT_FILE.write_text(alias)


def get_memory_path(alias: str) -> Path:
    """Get path to a memory file by alias."""
    return MEMORIES_DIR / f"{alias}{MEM_EXTENSION}"


def get_history_dir(alias: str) -> Path:
    """Get path to history directory for an alias."""
    return HISTORY_DIR / alias


def log_query(query: str, command: str, results_count: int) -> None:
    """Log a query to the queries file."""
    ensure_recall_home()
    queries = []
    if QUERIES_FILE.exists():
        try:
            queries = json.loads(QUERIES_FILE.read_text())
        except:
            queries = []
    
    queries.append({
        "date": datetime.now().isoformat(),
        "command": command,
        "query": query,
        "results": results_count,
        "project": get_current_project() or "unknown"
    })
    
    # Keep last 100 queries
    queries = queries[-100:]
    QUERIES_FILE.write_text(json.dumps(queries, indent=2))


def list_memories() -> List[Dict]:
    """List all saved memories with metadata."""
    ensure_recall_home()
    memories = []
    
    for mem_file in MEMORIES_DIR.glob(f"*{MEM_EXTENSION}"):
        try:
            memory = load_memory(mem_file)
            memories.append({
                "alias": mem_file.stem,
                "project": memory.get("project", "Unknown"),
                "path": memory.get("path", ""),
                "updated": memory.get("updated", "")[:10],
                "stats": memory.get("stats", {}),
                "description": memory.get("description", ""),
                "snapshots": len(list(get_history_dir(mem_file.stem).glob("*.mem"))) if get_history_dir(mem_file.stem).exists() else 0
            })
        except:
            memories.append({
                "alias": mem_file.stem, "project": "Error loading",
                "path": "", "updated": "", "stats": {}, "description": "", "snapshots": 0
            })
    
    return memories


# === Memory File Structure ===

def create_empty_memory(project_name: str, project_path: str) -> Dict:
    """Create a new empty memory structure."""
    return {
        "version": "2.5",
        "project": project_name,
        "path": project_path,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat(),
        
        "description": "",
        "summary": "",
        "stack": {},
        "structure": {},
        "directories": {},
        "key_files": [],
        "stats": {},
        "entities": {},  # NEW: extracted facts per file
        
        "decisions": [],
        "notes": [],
        "sessions": [],
        
        "index": {},
        "last_commit": "",
    }


def save_memory(memory: Dict, filepath: Path) -> None:
    """Save memory to a .mem file (compressed JSON)."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    memory["updated"] = datetime.now().isoformat()
    
    json_str = json.dumps(memory, indent=2)
    compressed = gzip.compress(json_str.encode('utf-8'))
    
    with open(filepath, 'w') as f:
        f.write("# Recall Memory File v2.5\n")
        f.write("# Do not edit manually\n")
        f.write(base64.b64encode(compressed).decode('ascii'))


def save_snapshot(memory: Dict, alias: str) -> str:
    """Save a historical snapshot and return the snapshot ID."""
    ensure_recall_home()
    history_dir = get_history_dir(alias)
    history_dir.mkdir(parents=True, exist_ok=True)
    
    # Create snapshot ID from timestamp
    snapshot_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_path = history_dir / f"{snapshot_id}{MEM_EXTENSION}"
    
    save_memory(memory, snapshot_path)
    return snapshot_id


def load_memory(filepath: Path) -> Dict:
    """Load memory from a .mem file."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    data_lines = [l for l in lines if not l.startswith('#')]
    encoded = ''.join(data_lines).strip()
    
    compressed = base64.b64decode(encoded)
    json_str = gzip.decompress(compressed).decode('utf-8')
    
    return json.loads(json_str)


def list_snapshots(alias: str) -> List[Dict]:
    """List all snapshots for a project."""
    history_dir = get_history_dir(alias)
    if not history_dir.exists():
        return []
    
    snapshots = []
    for snap_file in sorted(history_dir.glob(f"*{MEM_EXTENSION}"), reverse=True):
        try:
            memory = load_memory(snap_file)
            snapshots.append({
                "id": snap_file.stem,
                "date": memory.get("updated", "")[:10],
                "commit": memory.get("last_commit", ""),
                "files": memory.get("stats", {}).get("total_files", 0)
            })
        except:
            pass
    
    return snapshots


def load_snapshot_at(alias: str, date_str: str) -> Optional[Dict]:
    """Load the closest snapshot to a given date."""
    history_dir = get_history_dir(alias)
    if not history_dir.exists():
        return None
    
    target_date = date_str.replace("-", "")
    
    for snap_file in sorted(history_dir.glob(f"*{MEM_EXTENSION}"), reverse=True):
        snap_date = snap_file.stem.split("_")[0]
        if snap_date <= target_date:
            return load_memory(snap_file)
    
    return None


# === Code Analysis ===

def analyze_project(project_path: Path) -> Dict:
    """Analyze a project and extract structure."""
    files_data = []
    structure = defaultdict(list)
    directories = defaultdict(lambda: {"files": 0, "lines": 0, "types": set()})
    all_functions = []
    all_classes = []
    all_imports = set()
    import_graph = defaultdict(set)
    all_entities = {}  # file -> entities
    by_extension = defaultdict(int)
    total_lines = 0
    
    # Build search corpus for BM25
    search_corpus = []
    file_to_corpus_idx = {}
    
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        rel_root = Path(root).relative_to(project_path)
        
        for file in files:
            file_path = Path(root) / file
            suffix = file_path.suffix.lower()
            
            if suffix not in CODE_EXTENSIONS:
                continue
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                lines = len(content.splitlines())
                total_lines += lines
                by_extension[suffix] += 1
                
                rel_path = file_path.relative_to(project_path)
                
                funcs, classes, imports = extract_code_structure(content, suffix)
                
                for imp in imports:
                    import_graph[str(rel_path)].add(imp)
                
                # Extract entities (NEW in v2.5)
                entities = extract_entities(content, str(rel_path), suffix)
                if any(entities.values()):
                    all_entities[str(rel_path)] = entities
                
                purpose = infer_file_purpose(str(rel_path), content, funcs, classes)
                
                file_info = {
                    "path": str(rel_path),
                    "lines": lines,
                    "functions": [f["name"] for f in funcs][:5],
                    "classes": [c["name"] for c in classes],
                    "purpose": purpose
                }
                
                # Build search corpus entry
                corpus_entry = f"{str(rel_path)} {purpose} {' '.join(file_info['functions'])} {' '.join(file_info['classes'])}"
                file_to_corpus_idx[str(rel_path)] = len(search_corpus)
                search_corpus.append(corpus_entry)
                
                files_data.append(file_info)
                all_functions.extend(funcs)
                all_classes.extend(classes)
                all_imports.update(imports)
                
                dir_name = str(rel_root) if str(rel_root) != '.' else 'root'
                structure[dir_name].append(file_info)
                
                top_dir = str(rel_path).split('/')[0] if '/' in str(rel_path) else 'root'
                directories[top_dir]["files"] += 1
                directories[top_dir]["lines"] += lines
                directories[top_dir]["types"].add(purpose)
                
            except Exception as e:
                pass
    
    stack = detect_stack(all_imports, by_extension, files_data)
    key_files = identify_key_files(files_data, all_functions, all_classes)
    dir_summaries = generate_directory_summaries(directories)
    last_commit = get_git_commit(project_path)
    
    return {
        "files": files_data,
        "structure": dict(structure),
        "directories": dir_summaries,
        "functions": all_functions,
        "classes": all_classes,
        "imports": list(all_imports),
        "import_graph": {k: list(v) for k, v in import_graph.items()},
        "entities": all_entities,
        "search_corpus": search_corpus,
        "file_to_corpus_idx": file_to_corpus_idx,
        "stack": stack,
        "key_files": key_files,
        "last_commit": last_commit,
        "stats": {
            "total_files": len(files_data),
            "total_lines": total_lines,
            "by_extension": dict(by_extension),
            "total_functions": len(all_functions),
            "total_classes": len(all_classes)
        }
    }


def extract_code_structure(content: str, suffix: str) -> tuple:
    """Extract functions, classes, and imports from code."""
    functions, classes, imports = [], [], []
    
    if suffix == '.py':
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append({"name": node.name, "line": node.lineno})
                elif isinstance(node, ast.ClassDef):
                    classes.append({"name": node.name, "line": node.lineno})
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module.split('.')[0])
        except:
            pass
    
    elif suffix in {'.ts', '.tsx', '.js', '.jsx'}:
        for pattern in [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)',
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>',
        ]:
            for match in re.finditer(pattern, content):
                functions.append({"name": match.group(1), "line": 0})
        
        for match in re.finditer(r'(?:export\s+)?(?:default\s+)?(?:const|function)\s+([A-Z]\w+)', content):
            classes.append({"name": match.group(1), "line": 0})
        
        for match in re.finditer(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content):
            imports.append(match.group(1))
    
    return functions, classes, imports


def infer_file_purpose(path: str, content: str, functions: List, classes: List) -> str:
    """Infer the purpose of a file from its path and content."""
    path_lower = path.lower()
    
    for pattern, purpose in PURPOSE_PATTERNS:
        if re.search(pattern, path_lower):
            return purpose
    
    if classes and any(c["name"][0].isupper() for c in classes):
        return "Component"
    
    return "Code"


def detect_stack(imports: Set, extensions: Dict, files: List) -> Dict:
    """Detect the tech stack."""
    stack = {}
    imports_str = str(list(imports)).lower()
    
    if 'react' in imports_str or any('.tsx' in str(f.get('path', '')) for f in files):
        stack['frontend'] = 'React'
        if 'next' in imports_str or any('pages/' in str(f.get('path', '')) for f in files):
            stack['framework'] = 'Next.js'
    
    if 'express' in imports_str:
        stack['backend'] = 'Express'
    if '@supabase' in imports_str or 'supabase' in imports_str:
        stack['database'] = 'Supabase'
    if 'prisma' in imports_str:
        stack['orm'] = 'Prisma'
    if 'tailwindcss' in imports_str or any('tailwind' in str(f.get('path', '')).lower() for f in files):
        stack['styling'] = 'Tailwind CSS'
    
    if extensions.get('.ts', 0) + extensions.get('.tsx', 0) > 0:
        stack['language'] = 'TypeScript'
    elif extensions.get('.py', 0) > 0:
        stack['language'] = 'Python'
    
    return stack


def identify_key_files(files: List, functions: List, classes: List) -> List:
    """Identify key files with weighted scoring."""
    scored_files = []
    
    for f in files:
        score = 0
        path = f["path"]
        path_lower = path.lower()
        
        for pattern, weight in KEY_FILE_WEIGHTS.items():
            if pattern in path_lower:
                score += weight
                break
        
        if 'index' in path_lower or 'main' in path_lower:
            score += 2
        if 'app' in path_lower:
            score += 2
        if len(f.get("functions", [])) > 3:
            score += 1
        if f.get("lines", 0) > 100:
            score += 1
        if f.get("lines", 0) > 300:
            score += 1
        if 'test' in path_lower or 'spec' in path_lower:
            score = 0
        
        if score > 0:
            scored_files.append({
                "path": path, "purpose": f.get("purpose", ""),
                "functions": f.get("functions", [])[:3], "score": score
            })
    
    scored_files.sort(key=lambda x: x["score"], reverse=True)
    return [{k: v for k, v in f.items() if k != "score"} for f in scored_files[:20]]


def generate_directory_summaries(directories: Dict) -> Dict:
    """Generate summaries for each directory."""
    summaries = {}
    
    for dir_name, info in directories.items():
        types = list(info["types"])
        if len(types) == 1:
            main_purpose = types[0]
        elif "API endpoint" in types:
            main_purpose = "API endpoints"
        elif "UI component" in types or "Component" in types:
            main_purpose = "UI components"
        elif "Page/Route" in types:
            main_purpose = "Pages/Routes"
        else:
            main_purpose = ", ".join(types[:2])
        
        summaries[dir_name] = {
            "files": info["files"], "lines": info["lines"], "purpose": main_purpose
        }
    
    return summaries


def get_git_commit(project_path: Path) -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_path, capture_output=True, text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()[:8]
    except:
        pass
    return ""


def get_git_diff(project_path: Path, since_commit: str) -> List[Dict]:
    """Get files changed since a commit."""
    changes = []
    try:
        result = subprocess.run(
            ["git", "diff", "--name-status", f"{since_commit}..HEAD"],
            cwd=project_path, capture_output=True, text=True
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status, file_path = parts[0], parts[1]
                        change_type = {"A": "added", "M": "modified", "D": "deleted"}.get(status, "changed")
                        changes.append({"file": file_path, "type": change_type})
    except:
        pass
    return changes


def generate_summary(analysis: Dict, project_name: str) -> str:
    """Generate human-readable summary."""
    stats = analysis["stats"]
    stack = analysis["stack"]
    
    parts = [f"{project_name}:"]
    if stack:
        stack_str = ", ".join(f"{k}: {v}" for k, v in stack.items())
        parts.append(f"Stack: {stack_str}")
    parts.append(f"{stats['total_files']} files, {stats['total_lines']:,} lines")
    parts.append(f"{stats['total_functions']} functions, {stats['total_classes']} components")
    
    return " | ".join(parts)


# === CLI Commands ===

def cmd_pack(args) -> None:
    """Create a .mem file from a project."""
    project_path = Path(args.path or '.').resolve()
    
    if not project_path.exists():
        print(f"❌ Path does not exist: {project_path}")
        sys.exit(1)
    
    project_name = project_path.name
    alias = args.name or project_name
    
    if args.output:
        output_file = Path(args.output)
    elif args.name:
        ensure_recall_home()
        output_file = get_memory_path(alias)
    else:
        output_file = project_path / f"{project_name}{MEM_EXTENSION}"
    
    print(f"📦 Packing {project_name}...")
    
    analysis = analyze_project(project_path)
    
    # Load existing memory to preserve user data
    existing_memory = None
    if output_file.exists():
        try:
            existing_memory = load_memory(output_file)
            # Save snapshot before overwriting (v2.5: append-only history)
            if args.name:
                snapshot_id = save_snapshot(existing_memory, alias)
                print(f"   📸 Snapshot saved: {snapshot_id}")
        except:
            pass
    
    memory = create_empty_memory(project_name, str(project_path))
    
    if existing_memory:
        memory["description"] = existing_memory.get("description", "")
        memory["decisions"] = existing_memory.get("decisions", [])
        memory["notes"] = existing_memory.get("notes", [])
        memory["sessions"] = existing_memory.get("sessions", [])
        memory["created"] = existing_memory.get("created", memory["created"])
    
    memory["summary"] = generate_summary(analysis, project_name)
    memory["stack"] = analysis["stack"]
    memory["structure"] = {k: len(v) for k, v in analysis["structure"].items()}
    memory["directories"] = analysis["directories"]
    memory["key_files"] = analysis["key_files"]
    memory["stats"] = analysis["stats"]
    memory["last_commit"] = analysis["last_commit"]
    memory["entities"] = analysis["entities"]
    
    memory["index"] = {
        "files": [f["path"] for f in analysis["files"]],
        "functions": [f["name"] for f in analysis["functions"]],
        "classes": [c["name"] for c in analysis["classes"]],
        "imports": analysis.get("import_graph", {}),
        "search_corpus": analysis.get("search_corpus", []),
        "file_to_corpus_idx": analysis.get("file_to_corpus_idx", {})
    }
    
    save_memory(memory, output_file)
    
    file_size = output_file.stat().st_size / 1024
    print(f"✅ Created {output_file.name} ({file_size:.1f} KB)")
    print(f"   {analysis['stats']['total_files']} files, {analysis['stats']['total_lines']:,} lines indexed")
    
    # Count entities
    total_entities = sum(len(v.get('todos', [])) + len(v.get('notes', [])) + len(v.get('decisions', [])) 
                        for v in analysis['entities'].values())
    if total_entities:
        print(f"   📝 {total_entities} entities extracted")
    
    if args.name:
        set_current_project(alias)
        print(f"   Active project: {alias}")
        print()
        print_memory_context(memory)


def cmd_list(args) -> None:
    """List all saved memories."""
    memories = list_memories()
    
    if not memories:
        print("No saved memories. Run 'recall pack <path> --name <alias>' to create one.")
        return
    
    current = get_current_project()
    
    print("📚 Saved Memories:\n")
    for mem in memories:
        indicator = "→ " if mem["alias"] == current else "  "
        stats = mem.get("stats", {})
        files = stats.get("total_files", 0)
        lines = stats.get("total_lines", 0)
        desc = f'"{mem["description"][:40]}..."' if mem.get("description") else ""
        snapshots = mem.get("snapshots", 0)
        
        print(f"{indicator}{mem['alias']}")
        print(f"     📁 {mem['project']} | {files} files, {lines:,} lines")
        if snapshots:
            print(f"     📸 {snapshots} snapshots")
        if desc:
            print(f"     📝 {desc}")
        print(f"     🔄 Updated: {mem['updated']}")
        print()


def cmd_use(args) -> None:
    """Switch to a different project."""
    alias = args.alias
    mem_path = get_memory_path(alias)
    
    if not mem_path.exists():
        print(f"❌ No memory found for '{alias}'")
        print("   Run 'recall list' to see available projects")
        sys.exit(1)
    
    set_current_project(alias)
    memory = load_memory(mem_path)
    
    print(f"✅ Switched to: {alias}")
    print(f"   📁 {memory.get('project', 'Unknown')}")
    if memory.get("description"):
        print(f"   📝 {memory['description']}")


def cmd_update(args) -> None:
    """Re-pack the currently active project."""
    current = get_current_project()
    
    if not current:
        print("❌ No active project. Run 'recall use <alias>' first.")
        sys.exit(1)
    
    mem_path = get_memory_path(current)
    if not mem_path.exists():
        print(f"❌ Memory file not found for '{current}'")
        sys.exit(1)
    
    memory = load_memory(mem_path)
    project_path = memory.get("path", "")
    
    if not project_path or not Path(project_path).exists():
        print(f"❌ Project path not found: {project_path}")
        sys.exit(1)
    
    class Args:
        path = project_path
        name = current
        output = None
    
    cmd_pack(Args())


def print_memory_context(memory: Dict, show_hints: bool = True) -> None:
    """Print project context for AI consumption."""
    output = []
    output.append(f"# Project: {memory['project']}")
    output.append(f"Updated: {memory['updated'][:10]}")
    output.append("")

    if memory.get('description'):
        output.append("## Description")
        output.append(memory['description'])
        output.append("")

    output.append("## Summary")
    output.append(memory['summary'])
    output.append("")

    if memory.get('stack'):
        output.append("## Stack")
        for k, v in memory['stack'].items():
            output.append(f"- {k}: {v}")
        output.append("")

    if memory.get('directories'):
        output.append("## Directory Overview")
        sorted_dirs = sorted(memory['directories'].items(),
                           key=lambda x: x[1].get('files', 0), reverse=True)
        for dir_name, info in sorted_dirs[:10]:
            files = info.get('files', 0)
            purpose = info.get('purpose', '')
            output.append(f"- `{dir_name}/` ({files} files) - {purpose}")
        output.append("")

    if memory.get('key_files'):
        output.append("## Key Files")
        for f in memory['key_files'][:15]:
            funcs = ", ".join(f.get('functions', []))
            func_str = f" ({funcs})" if funcs else ""
            output.append(f"- `{f['path']}` - {f.get('purpose', '')}{func_str}")
        output.append("")

    if memory.get('decisions'):
        output.append("## Decisions")
        for d in memory['decisions'][-5:]:
            output.append(f"- [{d['date'][:10]}] {d['note']}")
        output.append("")

    if memory.get('sessions'):
        output.append("## Recent Sessions")
        for s in memory['sessions'][-3:]:
            output.append(f"- [{s['date'][:10]}] {s['topic']}")
        output.append("")

    if show_hints:
        output.append("---")
        output.append("💡 **Commands:**")
        output.append("   `recall deps <file>` → See imports AND what files depend on this (check before editing!)")
        output.append("   `recall find <query>` → Search with BM25 ranking")
        output.append("   `recall diff` → See changes since last pack")

    print("\n".join(output))


def cmd_load(args) -> None:
    """Output context from a .mem file for AI consumption."""
    # Handle time-travel
    if args.at:
        current = get_current_project()
        if not current:
            print("❌ No active project for time-travel")
            sys.exit(1)
        memory = load_snapshot_at(current, args.at)
        if not memory:
            print(f"❌ No snapshot found for date: {args.at}")
            sys.exit(1)
        print(f"⏰ Time-traveling to {args.at}\n")
    elif args.file:
        mem_file = Path(args.file)
        if not mem_file.exists():
            print("❌ File not found")
            sys.exit(1)
        memory = load_memory(mem_file)
    else:
        # Priority: 1) local .mem file, 2) active project in central store
        mem_file = find_mem_file()
        if not mem_file:
            current = get_current_project()
            if current:
                mem_file = get_memory_path(current)

        if not mem_file or not mem_file.exists():
            print("❌ No .mem file found in current directory or central store.")
            print("   Run 'recall pack --name <alias>' to create one, or 'recall pack' for local .mem file.")
            sys.exit(1)
        memory = load_memory(mem_file)

    print_memory_context(memory)


def cmd_describe(args) -> None:
    """Set the project description."""
    current = get_current_project()
    mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file or not mem_file.exists():
        print("❌ No .mem file found. Run 'recall pack' first.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    memory["description"] = args.text
    save_memory(memory, mem_file)
    
    print(f"✅ Description updated for {memory['project']}")
    print(f"   📝 {args.text}")


def cmd_note(args) -> None:
    """Add a note/decision to the memory."""
    current = get_current_project()
    mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file:
        print("❌ No .mem file found. Run 'recall pack' first.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    
    if "decisions" not in memory:
        memory["decisions"] = []
    
    memory["decisions"].append({
        "date": datetime.now().isoformat(),
        "note": args.text
    })
    save_memory(memory, mem_file)
    
    print(f"✅ Added note: {args.text}")


def cmd_session(args) -> None:
    """Log a session to the memory."""
    current = get_current_project()
    mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file:
        print("❌ No .mem file found. Run 'recall pack' first.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    
    if "sessions" not in memory:
        memory["sessions"] = []
    
    memory["sessions"].append({
        "date": datetime.now().isoformat(),
        "topic": args.topic
    })
    save_memory(memory, mem_file)
    
    print(f"✅ Logged session: {args.topic}")


def cmd_show(args) -> None:
    """Show full memory contents."""
    if args.file:
        mem_file = Path(args.file)
    else:
        current = get_current_project()
        mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file or not mem_file.exists():
        print("❌ No .mem file found.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    
    print("=" * 60)
    print(f"📁 {memory['project']}")
    print("=" * 60)
    print()
    
    if memory.get('description'):
        print(f"📝 {memory['description']}")
        print()
    
    print(f"📊 Summary: {memory['summary']}")
    print(f"📅 Created: {memory['created'][:10]}")
    print(f"🔄 Updated: {memory['updated'][:10]}")
    if memory.get('last_commit'):
        print(f"🔗 Git: {memory['last_commit']}")
    print()
    
    if memory.get('stack'):
        print("🛠️  Stack:")
        for k, v in memory['stack'].items():
            print(f"   {k}: {v}")
        print()
    
    if memory.get('directories'):
        print("📂 Directories:")
        sorted_dirs = sorted(memory['directories'].items(), 
                           key=lambda x: x[1].get('files', 0), reverse=True)
        for dir_name, info in sorted_dirs[:8]:
            print(f"   {dir_name}/ ({info.get('files', 0)} files) - {info.get('purpose', '')}")
        print()
    
    stats = memory.get('stats', {})
    print(f"📈 Stats:")
    print(f"   Files: {stats.get('total_files', 0)}")
    print(f"   Lines: {stats.get('total_lines', 0):,}")
    print(f"   Functions: {stats.get('total_functions', 0)}")
    print(f"   Components: {stats.get('total_classes', 0)}")
    print()
    
    if memory.get('entities'):
        total = sum(len(v.get('todos', [])) + len(v.get('notes', [])) 
                   for v in memory['entities'].values())
        print(f"📝 Entities: {total} extracted from {len(memory['entities'])} files")
        print()
    
    if memory.get('decisions'):
        print(f"📝 Decisions ({len(memory['decisions'])}):")
        for d in memory['decisions'][-5:]:
            print(f"   [{d['date'][:10]}] {d['note']}")
        print()
    
    if memory.get('sessions'):
        print(f"💬 Sessions ({len(memory['sessions'])}):")
        for s in memory['sessions'][-5:]:
            print(f"   [{s['date'][:10]}] {s['topic']}")
        print()
    
    print("=" * 60)


# === Search Commands ===

def cmd_find(args) -> None:
    """Search with BM25 ranking."""
    current = get_current_project()
    mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file or not mem_file.exists():
        print("❌ No .mem file found.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    query = args.query
    index = memory.get("index", {})
    
    # Use BM25 for file search
    corpus = index.get("search_corpus", [])
    file_to_idx = index.get("file_to_corpus_idx", {})
    files = index.get("files", [])
    
    results = {"files": [], "functions": [], "classes": []}
    
    if corpus:
        bm25 = BM25(corpus)
        search_results = bm25.search(query, top_k=10)
        
        idx_to_file = {v: k for k, v in file_to_idx.items()}
        for idx, score in search_results:
            if idx in idx_to_file:
                results["files"].append((idx_to_file[idx], score))
    else:
        # Fallback to substring matching
        for f in files:
            if query.lower() in f.lower():
                results["files"].append((f, 1.0))
    
    # Search functions and classes (substring)
    for f in index.get("functions", []):
        if query.lower() in f.lower():
            results["functions"].append(f)
    
    for c in index.get("classes", []):
        if query.lower() in c.lower():
            results["classes"].append(c)
    
    total = len(results["files"]) + len(results["functions"]) + len(results["classes"])
    
    # Log query
    log_query(query, "find", total)
    
    if total == 0:
        print(f"No results for '{query}'")
        return
    
    print(f"🔍 Results for '{query}':\n")
    
    if results["files"]:
        print("📁 Files (ranked by relevance):")
        for f, score in results["files"][:10]:
            print(f"   {f} ({score:.2f})")
        print()
    
    if results["functions"]:
        print("⚡ Functions:")
        for f in results["functions"][:10]:
            print(f"   {f}")
        print()
    
    if results["classes"]:
        print("🧩 Classes/Components:")
        for c in results["classes"][:10]:
            print(f"   {c}")


def cmd_diff(args) -> None:
    """Show changes since last pack."""
    current = get_current_project()
    mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file or not mem_file.exists():
        print("❌ No .mem file found.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    last_commit = memory.get("last_commit", "")
    project_path = memory.get("path", "")
    
    if not last_commit:
        print("❌ No git commit recorded. Run 'recall update' first.")
        return
    
    if not project_path or not Path(project_path).exists():
        print(f"❌ Project path not found: {project_path}")
        return
    
    changes = get_git_diff(Path(project_path), last_commit)
    
    if not changes:
        print("✅ No changes since last pack")
        return
    
    print(f"📝 Changes since last pack ({last_commit}):\n")
    
    for change in changes[:20]:
        icon = {"added": "+", "modified": "~", "deleted": "-"}.get(change["type"], "?")
        print(f"   {icon} {change['file']} ({change['type']})")
    
    if len(changes) > 20:
        print(f"\n   ... and {len(changes) - 20} more")
    
    print(f"\n💡 Run 'recall update' to refresh the memory")


def cmd_deps(args) -> None:
    """Show dependencies for a file."""
    current = get_current_project()
    mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file or not mem_file.exists():
        print("❌ No .mem file found.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    target_file = args.file
    import_graph = memory.get("index", {}).get("imports", {})
    
    matching_files = [f for f in import_graph.keys() if target_file in f]
    
    if not matching_files:
        print(f"❌ File not found: {target_file}")
        return
    
    for file_path in matching_files[:3]:
        print(f"📁 {file_path}")
        imports = import_graph.get(file_path, [])
        if imports:
            print("   Imports:")
            for imp in imports[:10]:
                print(f"      ← {imp}")
        else:
            print("   No imports tracked")
        print()


# === v2.5 Commands ===

def cmd_history(args) -> None:
    """List past snapshots."""
    current = get_current_project()
    
    if not current:
        print("❌ No active project. Run 'recall use <alias>' first.")
        sys.exit(1)
    
    snapshots = list_snapshots(current)
    
    if not snapshots:
        print(f"No history for '{current}'. Snapshots are created on each 'recall update'.")
        return
    
    print(f"📸 History for {current}:\n")
    for snap in snapshots[:10]:
        print(f"   {snap['id']} | {snap['date']} | {snap['commit']} | {snap['files']} files")
    
    if len(snapshots) > 10:
        print(f"\n   ... and {len(snapshots) - 10} more")
    
    print(f"\n💡 Use 'recall load --at YYYY-MM-DD' to time-travel")


def cmd_queries(args) -> None:
    """Show search history."""
    if not QUERIES_FILE.exists():
        print("No queries logged yet.")
        return
    
    try:
        queries = json.loads(QUERIES_FILE.read_text())
    except:
        print("Error reading queries file.")
        return
    
    current = get_current_project()
    
    # Filter by current project if set
    if current:
        queries = [q for q in queries if q.get("project") == current]
    
    if not queries:
        print("No queries logged for current project.")
        return
    
    print(f"🔍 Recent Queries:\n")
    for q in queries[-15:]:
        date = q['date'][:10]
        cmd = q['command']
        query = q['query'][:30]
        results = q['results']
        print(f"   [{date}] {cmd}: \"{query}\" ({results} results)")


def cmd_entity(args) -> None:
    """Show facts about a file."""
    current = get_current_project()
    mem_file = get_memory_path(current) if current else find_mem_file()
    
    if not mem_file or not mem_file.exists():
        print("❌ No .mem file found.")
        sys.exit(1)
    
    memory = load_memory(mem_file)
    target = args.file
    entities = memory.get("entities", {})
    
    # Find matching files
    matches = [(f, e) for f, e in entities.items() if target in f]
    
    if not matches:
        print(f"❌ No entities found for: {target}")
        print("   (Entities are extracted from TODO, NOTE, FIXME comments and docstrings)")
        return
    
    for file_path, ents in matches[:5]:
        print(f"📁 {file_path}")
        
        if ents.get("todos"):
            print("   📌 TODOs:")
            for t in ents["todos"][:3]:
                print(f"      - {t}")
        
        if ents.get("notes"):
            print("   📝 Notes:")
            for n in ents["notes"][:3]:
                print(f"      - {n}")
        
        if ents.get("decisions"):
            print("   🎯 Decisions:")
            for d in ents["decisions"][:3]:
                print(f"      - {d}")
        
        if ents.get("warnings"):
            print("   ⚠️  Warnings:")
            for w in ents["warnings"][:3]:
                print(f"      - {w}")
        
        if ents.get("descriptions"):
            print("   📄 Descriptions:")
            for d in ents["descriptions"][:3]:
                print(f"      - {d}")
        
        print()


def find_mem_file() -> Optional[Path]:
    """Find a .mem file in current or parent directories."""
    current = Path.cwd()
    
    while current != current.parent:
        for f in current.glob(f"*{MEM_EXTENSION}"):
            return f
        current = current.parent
    
    return None


def main():
    parser = argparse.ArgumentParser(
        description='Recall v1.0.0 - Portable Memory for AI Assistants',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # pack
    pack_parser = subparsers.add_parser('pack', help='Create .mem file from project')
    pack_parser.add_argument('path', nargs='?', help='Path to project')
    pack_parser.add_argument('-n', '--name', help='Alias for central store')
    pack_parser.add_argument('-o', '--output', help='Output file path')
    pack_parser.set_defaults(func=cmd_pack)
    
    # list
    list_parser = subparsers.add_parser('list', help='List all saved memories')
    list_parser.set_defaults(func=cmd_list)
    
    # use
    use_parser = subparsers.add_parser('use', help='Switch active project')
    use_parser.add_argument('alias', help='Project alias')
    use_parser.set_defaults(func=cmd_use)
    
    # update
    update_parser = subparsers.add_parser('update', help='Re-pack current project')
    update_parser.set_defaults(func=cmd_update)
    
    # load
    load_parser = subparsers.add_parser('load', help='Output context for AI')
    load_parser.add_argument('file', nargs='?', help='.mem file')
    load_parser.add_argument('--at', help='Time-travel to date (YYYY-MM-DD)')
    load_parser.set_defaults(func=cmd_load)
    
    # describe
    describe_parser = subparsers.add_parser('describe', help='Set project description')
    describe_parser.add_argument('text', help='Description')
    describe_parser.set_defaults(func=cmd_describe)
    
    # note
    note_parser = subparsers.add_parser('note', help='Add a decision/note')
    note_parser.add_argument('text', help='Note text')
    note_parser.set_defaults(func=cmd_note)
    
    # session
    session_parser = subparsers.add_parser('session', help='Log a session')
    session_parser.add_argument('topic', help='Session topic')
    session_parser.set_defaults(func=cmd_session)
    
    # show
    show_parser = subparsers.add_parser('show', help='Show full memory')
    show_parser.add_argument('file', nargs='?', help='.mem file')
    show_parser.set_defaults(func=cmd_show)
    
    # find
    find_parser = subparsers.add_parser('find', help='Search with BM25 ranking')
    find_parser.add_argument('query', help='Search query')
    find_parser.set_defaults(func=cmd_find)
    
    # diff
    diff_parser = subparsers.add_parser('diff', help='Show changes since last pack')
    diff_parser.set_defaults(func=cmd_diff)
    
    # deps
    deps_parser = subparsers.add_parser('deps', help='Show file dependencies')
    deps_parser.add_argument('file', help='File to check')
    deps_parser.set_defaults(func=cmd_deps)
    
    # history (v2.5)
    history_parser = subparsers.add_parser('history', help='List past snapshots')
    history_parser.set_defaults(func=cmd_history)
    
    # queries (v2.5)
    queries_parser = subparsers.add_parser('queries', help='Show search history')
    queries_parser.set_defaults(func=cmd_queries)
    
    # entity (v2.5)
    entity_parser = subparsers.add_parser('entity', help='Show facts about file')
    entity_parser.add_argument('file', help='File to check')
    entity_parser.set_defaults(func=cmd_entity)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
