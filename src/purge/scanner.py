import os
from pathlib import Path
from typing import List, Set, Iterator
from ..core.constants import PROJECT_INDICATORS, MONOREPO_INDICATORS, PURGE_TARGETS

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
            # Don't recurse deeper if we found a project root, 
            # unless it's a known monorepo (optional optimization)
            # return 

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
