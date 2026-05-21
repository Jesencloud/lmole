import os
import shutil
from pathlib import Path
from ..core.system import run_command
from ..core.file_ops import safe_remove, get_size

def clean_tool_cache(description, command_args, cache_path=None, dry_run=False):
    """Helper to clean a specific tool's cache."""
    print(f"  \033[0;32m✓\033[0m {description}")
    if dry_run:
        return 0, 1

    res = run_command(command_args, capture=True)
    if res and res.returncode == 0:
        return 0, 1
    return 0, 0

def safe_clean_glob(pattern_path, description, dry_run=False):
    """Cleans files matching a glob pattern."""
    path = Path(pattern_path).expanduser()
    parent = path.parent
    pattern = path.name
    
    if not parent.exists():
        return 0, 0

    found = list(parent.glob(pattern))
    if not found:
        return 0, 0

    total_size = 0
    for item in found:
        total_size += get_size(item)

    print(f"  \033[0;32m✓\033[0m {description}")
    if dry_run:
        return total_size, len(found)

    for item in found:
        safe_remove(item, use_trash=False)
    return total_size, len(found)

def clean_docker(dry_run=False):
    """Clean unused Docker data."""
    if shutil.which("docker"):
        print("  \033[0;32m✓\033[0m Docker (unused images/volumes)")
        if not dry_run:
            # Check if docker needs sudo
            use_sudo = True
            try:
                res = subprocess.run(["docker", "info"], capture_output=True)
                if res.returncode == 0: use_sudo = False
            except: pass
            
            run_command(["docker", "system", "prune", "-f", "--volumes"], use_sudo=use_sudo, capture=True)
        return 0, 1
    return 0, 0

def clean_developer_tools(dry_run=False):
    print("\033[1;95m➤ Developer Tools Cleanup\033[0m")
    total_size = 0
    total_items = 0
    categories = 0
    
    # 1. Package Manager Caches
    if shutil.which("npm"):
        s, i = clean_tool_cache("npm cache", ["npm", "cache", "clean", "--force"], dry_run=dry_run)
        total_size += s; total_items += i; categories += 1
    
    s, i = safe_clean_glob("~/.npm/_cacache/*", "npm cacache", dry_run=dry_run)
    total_size += s; total_items += i; categories += 1
    
    if shutil.which("pip3"):
        s, i = clean_tool_cache("pip cache", ["pip3", "cache", "purge"], dry_run=dry_run)
        total_size += s; total_items += i; categories += 1

    if shutil.which("go"):
        s, i = clean_tool_cache("go cache", ["go", "clean", "-cache"], dry_run=dry_run)
        total_size += s; total_items += i; categories += 1

    # 2. IDE Caches
    # JetBrains
    s, i = safe_clean_glob("~/.cache/JetBrains/*/caches", "JetBrains IDE caches", dry_run=dry_run)
    total_size += s; total_items += i; categories += (1 if i > 0 else 0)
    s, i = safe_clean_glob("~/.cache/JetBrains/*/logs", "JetBrains IDE logs", dry_run=dry_run)
    total_size += s; total_items += i; categories += (1 if i > 0 else 0)

    # Android Studio
    s, i = safe_clean_glob("~/.cache/Google/AndroidStudio*/caches", "Android Studio caches", dry_run=dry_run)
    total_size += s; total_items += i; categories += (1 if i > 0 else 0)

    # 3. Virtualization & Containers
    s, i = clean_docker(dry_run=dry_run)
    total_size += s; total_items += i; categories += (1 if i > 0 else 0)

    return total_size, total_items, categories
