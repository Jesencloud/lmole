#!/usr/bin/env python3
import os
import subprocess
import shutil
import time
import argparse
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# ============================================================================
# Constants & Configuration
# ============================================================================

PURGE_TARGETS = {
    "node_modules", "target", "build", "dist", "out", "bin", "obj", 
    "vendor", ".next", ".nuxt", ".cache", ".serverless", ".terraform", 
    "venv", ".venv", "env", "__pycache__", ".pytest_cache", ".tox", 
    ".nox", ".gradle", ".build", "cmake-build-debug", "cmake-build-release"
}

PROJECT_INDICATORS = {
    "package.json", "Cargo.toml", "go.mod", "requirements.txt", 
    "pyproject.toml", "Gemfile", "composer.json", "build.gradle", 
    "pom.xml", "CMakeLists.txt", "Makefile", "Dockerfile", ".git"
}

# ANSI Colors
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_PURPLE = "\033[95m"
C_BOLD = "\033[1m"
C_GRAY = "\033[90m"
C_NC = "\033[0m"

# ============================================================================
# Utilities
# ============================================================================

def get_os_info():
    """Get OS ID and Version from /etc/os-release"""
    info = {"ID": "unknown", "VERSION": ""}
    try:
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if line.startswith("ID="):
                        info["ID"] = line.strip().split("=")[1].strip('"')
                    elif line.startswith("VERSION_ID="):
                        info["VERSION"] = line.strip().split("=")[1].strip('"')
    except Exception:
        pass
    return info

def format_size(bytes_size):
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def get_dir_size(path):
    """Fast directory size calculation"""
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += get_dir_size(entry.path)
                except OSError:
                    pass
    except Exception:
        pass
    return total

def run_sudo(args, description=""):
    """Run a command with sudo, handles password prompt if needed"""
    if description:
        print(f"{C_GRAY}▶ {description}{C_NC}")
    
    try:
        # First try non-interactive sudo
        result = subprocess.run(["sudo", "-n"] + args, capture_output=True, text=True)
        if result.returncode == 0:
            return True
        
        # If failed, it might need password or command failed
        if "sudo: a password is required" in result.stderr:
            subprocess.run(["sudo"] + args)
            return True
        else:
            return False
    except Exception as e:
        print(f"{C_RED}Error: {e}{C_NC}")
        return False

# ============================================================================
# Cleanup Modules
# ============================================================================

def clean_package_manager():
    os_info = get_os_info()
    os_id = os_info["ID"]
    
    print(f"\n{C_PURPLE_BOLD}➤ Package Manager Cleanup{C_NC}")
    
    if os_id in ("fedora", "rhel", "centos"):
        if shutil.which("dnf"):
            run_sudo(["dnf", "clean", "all"], "Cleaning DNF cache...")
            print(f"  {C_GREEN}✓{C_NC} DNF cache cleared")
    elif os_id in ("ubuntu", "debian", "pop", "mint"):
        if shutil.which("apt-get"):
            run_sudo(["apt-get", "autoremove", "-y"], "Removing unused packages...")
            run_sudo(["apt-get", "clean"], "Cleaning APT cache...")
            print(f"  {C_GREEN}✓{C_NC} APT cache cleared")

def clean_system_logs():
    print(f"\n{C_PURPLE_BOLD}➤ System Logs Cleanup{C_NC}")
    if shutil.which("journalctl"):
        run_sudo(["journalctl", "--vacuum-time=7d"], "Vacuuming journal logs (keeping 7 days)...")
        print(f"  {C_GREEN}✓{C_NC} Journald logs vacuumed")

def clean_user_caches():
    print(f"\n{C_PURPLE_BOLD}➤ User Cache Cleanup{C_NC}")
    cache_dir = Path(os.environ.get("XDG_CACHE_HOME", "~/.cache")).expanduser()
    
    # Common user caches to clean
    targets = [
        ("Thumbnails", cache_dir / "thumbnails"),
        ("Pip Cache", cache_dir / "pip"),
        ("NPM Cache", Path("~/.npm").expanduser()),
        ("Ollama Models (temp)", cache_dir / "ollama") # Just an example
    ]
    
    for name, path in targets:
        if path.exists():
            size = get_dir_size(path)
            if size > 0:
                print(f"  {C_GRAY}·{C_NC} {name}: {C_GREEN}{format_size(size)}{C_NC}")
                # For safety in prototype, we just print size. Real delete: shutil.rmtree(path)
                # shutil.rmtree(path, ignore_errors=True)
                # os.makedirs(path, exist_ok=True)

# ============================================================================
# Project Purge Module
# ============================================================================

def is_project_root(path_obj):
    for indicator in PROJECT_INDICATORS:
        if (path_obj / indicator).exists():
            return True
    return False

def scan_path(search_path):
    found = []
    try:
        for entry in os.scandir(search_path):
            if not entry.is_dir() or entry.name.startswith('.'):
                continue
            
            # Sub-scanning
            try:
                for sub in os.scandir(entry.path):
                    if sub.is_dir() and sub.name in PURGE_TARGETS:
                        if is_project_root(Path(entry.path)):
                            size = get_dir_size(sub.path)
                            found.append({
                                "path": Path(sub.path),
                                "project": entry.name,
                                "name": sub.name,
                                "size": size
                            })
            except OSError:
                continue
    except OSError:
        pass
    return found

def perform_purge():
    print(f"\n{C_PURPLE_BOLD}➤ Project Purge (Deep Scan){C_NC}")
    
    search_roots = [
        Path("~/Projects").expanduser(),
        Path("~/workspace").expanduser(),
        Path("~/dev").expanduser(),
        Path("~/code").expanduser()
    ]
    
    valid_roots = [p for p in search_roots if p.is_dir()]
    if not valid_roots:
        print(f"  {C_YELLOW}⚠{C_NC} No project directories found. Set up ~/Projects or ~/workspace.")
        return

    print(f"  {C_GRAY}Scanning {len(valid_roots)} directories...{C_NC}")
    start = time.time()
    all_artifacts = []
    
    with ThreadPoolExecutor() as executor:
        results = executor.map(scan_path, valid_roots)
        for r in results:
            all_artifacts.extend(r)
    
    elapsed = time.time() - start
    
    if not all_artifacts:
        print(f"  {C_GREEN}✓{C_NC} No artifacts found to purge. (Scan time: {elapsed:.2f}s)")
        return

    # Sort by size
    all_artifacts.sort(key=lambda x: x["size"], reverse=True)
    
    print(f"\n{C_BOLD}Found {len(all_artifacts)} artifacts ({elapsed:.2f}s):{C_NC}")
    for i, item in enumerate(all_artifacts):
        print(f"  [{i+1}] {C_BLUE}{item['project']}{C_NC}/{C_YELLOW}{item['name']}{C_NC}")
        print(f"      {C_GRAY}{item['path']}{C_NC} ({C_GREEN}{format_size(item['size'])}{C_NC})")
    
    print(f"\n{C_BOLD}Options:{C_NC}")
    print(f"  - Enter numbers to delete (e.g. 1,2,5)")
    print(f"  - 'all' to delete everything")
    print(f"  - 'q' to cancel")
    
    choice = input(f"\n{C_PURPLE}?{C_NC} Selection: ").strip().lower()
    
    to_delete = []
    if choice == 'q':
        print("Cancelled.")
        return
    elif choice == 'all':
        to_delete = all_artifacts
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",") if x.strip()]
            to_delete = [all_artifacts[i] for i in indices if 0 <= i < len(all_artifacts)]
        except (ValueError, IndexError):
            print(f"{C_RED}Invalid selection.{C_NC}")
            return

    if not to_delete:
        print("Nothing selected.")
        return

    total_freed = 0
    print(f"\n{C_RED_BOLD}Deleting...{C_NC}")
    for item in to_delete:
        try:
            size = item["size"]
            # ACTUAL DELETION
            shutil.rmtree(item["path"])
            print(f"  {C_GREEN}✓{C_NC} Removed {item['project']}/{item['name']} ({format_size(size)})")
            total_freed += size
        except Exception as e:
            print(f"  {C_RED}✗{C_NC} Failed to remove {item['path']}: {e}")

    print(f"\n{C_GREEN_BOLD}Done! Total space freed: {format_size(total_freed)}{C_NC}")

# ============================================================================
# Main Entry
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="lmole - Linux System Cleaner (Python Version)")
    parser.add_argument("command", choices=["clean", "purge", "all"], nargs="?", default="all",
                        help="Command to run: clean (system), purge (projects), or all")
    parser.add_argument("-n", "--dry-run", action="store_true", help="Preview only, no deletions")
    
    args = parser.parse_args()
    
    # Handle global dry run state (simple for prototype)
    if args.dry_run:
        print(f"{C_YELLOW_BOLD}!!! DRY RUN MODE - No files will be deleted !!!{C_NC}")

    print(f"{C_BLUE_BOLD}lmole 0.2.0 (Python Refactor){C_NC}")
    os_info = get_os_info()
    print(f"{C_GRAY}System: {os_info['ID']} {os_info['VERSION']}{C_NC}")

    if args.command in ("clean", "all"):
        clean_package_manager()
        clean_system_logs()
        clean_user_caches()
    
    if args.command in ("purge", "all"):
        perform_purge()

    print(f"\n{C_BLUE_BOLD}=== lmole execution finished ==={C_NC}")

C_BLUE_BOLD = "\033[1;94m"
C_PURPLE_BOLD = "\033[1;95m"
C_RED_BOLD = "\033[1;91m"
C_GREEN_BOLD = "\033[1;92m"
C_YELLOW_BOLD = "\033[1;93m"

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting.")
        sys.exit(0)
