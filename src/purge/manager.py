import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from .scanner import Scanner
from ..core.file_ops import get_size, safe_remove, bytes_to_human
from ..core.config import get_purge_paths

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
