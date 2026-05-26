import os
import time
from pathlib import Path
from typing import List, Set, Iterator, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from ..core.constants import PROJECT_INDICATORS, MONOREPO_INDICATORS, PURGE_TARGETS
from ..core.file_ops import get_size, safe_remove, bytes_to_human
from ..core.config import get_purge_paths

class Scanner:
    def __init__(self, search_paths: List[str]):
        self.search_paths = [Path(p).expanduser().resolve() for p in search_paths]
        self.found_projects: Set[Path] = set()
        self.found_artifacts: List[Path] = []

    def is_project_root(self, path: Path) -> bool:
        """Checks if a directory is a project root based on indicators."""
        try:
            for entry in os.scandir(path):
                if entry.name in MONOREPO_INDICATORS or entry.name in PROJECT_INDICATORS:
                    return True
        except OSError:
            pass
        return False

    def scan_for_projects(self, max_depth: int = 4) -> Iterator[Path]:
        """Discovers project roots within search paths."""
        for root in self.search_paths:
            if not root.is_dir():
                continue
            
            yield from self._recursive_scan(root, 0, max_depth)

    def _recursive_scan(self, path: Path, depth: int, max_depth: int) -> Iterator[Path]:
        """Recursive helper for project discovery."""
        if depth > max_depth:
            return

        if self.is_project_root(path):
            yield path

        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_dir() and not entry.name.startswith('.'):
                        yield from self._recursive_scan(Path(entry.path), depth + 1, max_depth)
        except OSError:
            pass

    def scan_artifacts(self, project_path: Path) -> List[Path]:
        """Finds heavy artifacts within a discovered project root."""
        artifacts = []
        try:
            with os.scandir(project_path) as it:
                for entry in it:
                    if entry.is_dir() and entry.name in PURGE_TARGETS:
                        artifacts.append(Path(entry.path))
        except OSError:
            pass
        return artifacts

class PurgeManager:
    def __init__(self):
        self.scanner = Scanner(get_purge_paths())
        self.results: List[Dict[str, Any]] = []

    def run_scan(self):
        """Orchestrates the scanning process."""
        print("🔍 Scanning for projects and heavy artifacts...")
        
        # 1. Discover projects
        projects = list(self.scanner.scan_for_projects())
        
        # 2. Find artifacts in projects
        all_artifacts = []
        for project in projects:
            artifacts = self.scanner.scan_artifacts(project)
            all_artifacts.extend(artifacts)
        
        if not all_artifacts:
            print("✨ No heavy artifacts found. Your projects are clean!")
            return []

        # 3. Calculate sizes in parallel
        print(f"📊 Found {len(all_artifacts)} potential targets. Calculating sizes...")
        with ThreadPoolExecutor(max_workers=8) as executor:
            sizes = list(executor.map(get_size, all_artifacts))

        # 4. Filter out empty ones and prepare results
        self.results = []
        for path, size in zip(all_artifacts, sizes):
            if size > 0:
                self.results.append({
                    "path": path,
                    "size": size,
                    "human_size": bytes_to_human(size),
                    "project": path.parent.name
                })
        
        # Sort by size (largest first)
        self.results.sort(key=lambda x: x['size'], reverse=True)
        return self.results

    def execute_purge(self, selected_indices: List[int]):
        """Deletes selected artifacts."""
        freed_space = 0
        count = 0
        
        for idx in selected_indices:
            item = self.results[idx]
            success, msg = safe_remove(item['path'])
            if success:
                print(f"✅ Removed {item['path'].relative_to(Path.home())} ({item['human_size']})")
                freed_space += item['size']
                count += 1
            else:
                print(f"❌ Failed to remove {item['path']}: {msg}")
        
        return count, bytes_to_human(freed_space)
