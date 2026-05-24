import os
import subprocess
import json
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any
from .file_ops import get_size, bytes_to_human
from ..ui.navigator import Navigator, AnalyzeSelector

# ANSI Colors
BLUE = "\033[1;34m"
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
YELLOW = "\033[1;33m"
WHITE = "\033[1;37m"
GRAY = "\033[1;90m"
RESET = "\033[0m"
BOLD = "\033[1m"

VIRTUAL_DIRS = {
    "proc", "sys", "dev", "run", "snap", "flatpak", 
    "mnt", "media", "lost+found", 
    "ollama", "cuda",
    "usr", "lib", "lib64", "boot", "sbin", "bin"
}

# Simple singleton-like cache for scan results
class ScanCache:
    _data = {}

    @classmethod
    def get(cls, path: Path):
        return cls._data.get(str(path))

    @classmethod
    def set(cls, path: Path, data):
        cls._data[str(path)] = data

def get_rust_scan_data(path: Path) -> Dict[str, Any]:
    """Calls the Rust core to scan a directory and returns JSON data with caching."""
    cached = ScanCache.get(path)
    if cached:
        return cached

    bin_path = Path(__file__).parent / "bin" / "lmo-core"
    if not bin_path.exists():
        return None
    try:
        res = subprocess.run([str(bin_path), str(path)], capture_output=True, text=True, timeout=30)
        if res.returncode == 0:
            data = json.loads(res.stdout)
            ScanCache.set(path, data)
            return data
    except: pass
    return None

def get_dir_size_recursive(path: Path) -> int:
    """Fast size calculation using Rust core, falls back to du."""
    if str(path) == "/":
        try: return shutil.disk_usage("/").used
        except: pass

    data = get_rust_scan_data(path)
    if data: return data.get("total_size_bytes", 0)
    
    try:
        res = subprocess.run(["du", "-sbx", str(path)], capture_output=True, text=True, timeout=5)
        if res.returncode == 0: return int(res.stdout.split()[0])
    except: pass
    return 0

def run_deep_analysis():
    # Path stack to track navigation history
    path_stack = [None] 
    
    while path_stack:
        current_target = path_stack[-1]
        results = []
        view_title = "Analyze Disk"
        
        target_to_scan = current_target or Path.home()
        
        print(f"   🚀 Rust Engine: Intelligence Scan on {target_to_scan.name if current_target else 'Home'}...", end="\r")
        data = get_rust_scan_data(target_to_scan)
        
        if not data:
            print(f"\n   ❌ Engine scan failed for {target_to_scan}")
            time.sleep(1.5); path_stack.pop(); continue

        total_scan_size = data.get("total_size_bytes", 0)
        
        if current_target is None:
            # Root View (Special Case: Show major categories)
            total_used = shutil.disk_usage("/").used
            targets = [
                {"name": "Home", "path": Path.home(), "color": CYAN},
                {"name": "Applications", "path": Path("/usr/share/applications"), "color": MAGENTA},
                {"name": "System", "path": Path("/usr"), "color": BLUE},
                {"name": "Root (/)", "path": Path("/"), "color": WHITE},
            ]
            for t in targets:
                if t['path'].exists():
                    # Optimization: Use already fetched data for Home
                    if t['path'] == Path.home():
                        size = total_scan_size
                    elif str(t['path']) == "/":
                        size = total_used
                    else:
                        # Use get_rust_scan_data which is now cached
                        t_data = get_rust_scan_data(t['path'])
                        size = t_data.get("total_size_bytes", 0) if t_data else get_dir_size_recursive(t['path'])
                    
                    results.append({"name": t['name'], "path": t['path'], "size": size, "percent": (size / total_used) * 100, "color": t['color']})
        else:
            # Subdirectory View: POWERED BY RUST DATA
            view_title = f"Exploring: {current_target}"
            total_path_size = total_scan_size or 1
            
            # Directly use the subdirs map provided by Rust - NO MORE LOOPS!
            subdir_map = data.get("subdirs", {})
            for name, size in subdir_map.items():
                if name.startswith('.'): continue # Skip hidden
                full_path = current_target / name
                # We don't check is_dir() here to save syscalls, 
                # Rust already filtered for directories in subdir_map
                results.append({
                    "name": name, 
                    "path": full_path, 
                    "size": size, 
                    "percent": (size / total_path_size) * 100, 
                    "color": CYAN
                })
            
            results.sort(key=lambda x: x['size'], reverse=True)
            results = results[:25] # Show top 25

        from ..ui.tui import show_banner
        selector = AnalyzeSelector(view_title, results, show_banner=show_banner if current_target is None else None)
        action, idx = selector.run()
        
        if action == "QUIT": break
        elif action == "BACK":
            if current_target is not None: path_stack.pop()
            else: break
        elif action == "REFRESH": continue
        elif action == "OPEN":
            subprocess.run(["xdg-open", str(results[idx]['path'])], capture_output=True)
        elif action == "SWITCH_FILES":
            # Pass the already collected data to avoid re-scanning!
            _render_top_files(data)
        elif action == "DRILL_DOWN":
            target = results[idx]['path']
            if target.name in VIRTUAL_DIRS and str(target) != "/":
                print(f"\n   🛡️  System Directory Protected. Deep scan disabled."); time.sleep(1)
                continue
            path_stack.append(target)

def _render_top_files(data):
    """Renders the top files view using pre-existing scan data."""
    top_files = data.get("top_files", [])
    os.system('clear')
    print(f"\033[1;33m🏆 Top {len(top_files)} Largest Files (Powered by Rust)\033[0m")
    print("-" * 60)
    for i, f in enumerate(top_files):
        print(f"[{i+1:2}] {bytes_to_human(f['size_bytes']):>12} | {f['path']}")
        if i >= 19: break
    input("\nPress Enter to return...")

def _run_top_files_view(search_path="~"):
    root = Path(search_path).expanduser().resolve()
    print(f"\n🚀 Rust Engine: Scanning for top files in {root}...")
    data = get_rust_scan_data(root)
    if not data:
        print("   ❌ Rust engine failed.")
        time.sleep(1.5)
        return
    top_files = data.get("top_files", [])
    os.system('clear')
    print(f"\033[1;33m🏆 Top {len(top_files)} Largest Files (Powered by Rust)\033[0m")
    print("-" * 60)
    for i, f in enumerate(top_files):
        print(f"[{i+1:2}] {bytes_to_human(f['size_bytes']):>12} | {f['path']}")
        if i >= 19: break
    input("\nPress Enter to return...")
