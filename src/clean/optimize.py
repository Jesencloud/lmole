import shutil
import subprocess
import os
import time
import sqlite3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from ..core.system import run_command, has_sudo
from ..core.file_ops import get_size, bytes_to_human

# ANSI Colors
GREEN = "\033[0;32m"
YELLOW = "\033[0;33m"
BLUE = "\033[0;34m"
GRAY = "\033[0;90m"
RESET = "\033[0m"
BOLD = "\033[1m"

def opt_log(message, success=True, skipped=False):
    if skipped:
        icon = f"{GRAY}◎{RESET}"
        msg = f"{GRAY}{message} · skipped{RESET}"
    else:
        icon = f"{GREEN}✓{RESET}"
        msg = f"{message}"
    print(f"  {icon} {msg}")

def vacuum_single_db(db_file):
    """Worker function to vacuum a single database only if worth it."""
    try:
        conn = sqlite3.connect(db_file, timeout=1)
        cursor = conn.cursor()
        
        # Get page count and free pages
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA freelist_count")
        freelist_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        
        if page_count == 0:
            conn.close()
            return 0
            
        free_ratio = freelist_count / page_count
        free_bytes = freelist_count * page_size
        
        # Threshold: Only vacuum if > 10% is free OR > 5MB can be reclaimed
        if free_ratio > 0.1 or free_bytes > 5 * 1024 * 1024:
            old_size = get_size(db_file)
            conn.execute("VACUUM")
            conn.close()
            return old_size - get_size(db_file)
        
        conn.close()
        return 0
    except:
        return 0

def vacuum_databases(dry_run=False):
    """Optimizes SQLite databases in parallel."""
    targets = [
        "~/.mozilla/firefox/*/places.sqlite",
        "~/.mozilla/firefox/*/cookies.sqlite",
        "~/.config/google-chrome/Default/History",
        "~/.config/BraveSoftware/Brave-Browser/Default/History",
        "~/.config/microsoft-edge/Default/History",
    ]
    
    db_files = []
    for pattern in targets:
        path_obj = Path(pattern).expanduser()
        parent = path_obj.parent
        if not parent.exists(): continue
        for f in parent.glob(path_obj.name):
            if f.is_file(): db_files.append(f)
    
    if not db_files: return
    if dry_run:
        opt_log(f"Found {len(db_files)} browser database(s) to optimize", skipped=True)
        return

    total_saved = 0
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(vacuum_single_db, db_files))
        total_saved = sum(results)
    
    saved_str = f" (compressed {bytes_to_human(total_saved)})" if total_saved > 0 else ""
    opt_log(f"Optimized {len(db_files)} browser database(s){saved_str}")

def cleanup_zombie_autostart(dry_run=False):
    """Removes autostart entries for uninstalled applications."""
    autostart_dir = Path.home() / ".config" / "autostart"
    if not autostart_dir.exists(): return

    zombies = 0
    for desktop_file in autostart_dir.glob("*.desktop"):
        try:
            is_zombie = False
            with open(desktop_file, 'r') as f:
                for line in f:
                    if line.startswith('Exec='):
                        exec_line = line.split('=', 1)[1].strip()
                        if not exec_line: continue
                        cmd = exec_line.split()[0]
                        if cmd.startswith('/') and not os.path.exists(cmd):
                            is_zombie = True
                        elif not cmd.startswith('/') and not shutil.which(cmd):
                            is_zombie = True
                        break
            if is_zombie:
                if not dry_run: desktop_file.unlink()
                zombies += 1
        except: continue
    
    if zombies > 0:
        opt_log(f"Removed {zombies} zombie autostart entries", skipped=dry_run)

def optimize_memory_advanced(dry_run=False):
    """Quick memory optimizations."""
    if has_sudo() and not dry_run:
        # Fast non-blocking sync
        subprocess.Popen(["sync"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Drop caches is usually fast
        subprocess.run(["sudo", "bash", "-c", "echo 1 > /proc/sys/vm/drop_caches"], 
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opt_log("PageCache released (Memory relief)")

def optimize_system(dry_run=False):
    os.system('clear')
    print(f"{BLUE}{BOLD}System Optimization{RESET}")
    print(f"{GRAY}Running maintenance tasks in parallel...{RESET}\n")
    
    start_time = time.time()

    # 1. Parallel Tasks
    with ThreadPoolExecutor(max_workers=4) as executor:
        # SSD Trim (can be slow, but fstrim -a is generally efficient)
        if shutil.which("fstrim") and not dry_run:
            executor.submit(run_command, ["fstrim", "-av"], use_sudo=True, capture=True)
            opt_log("SSD partitions trimmed (fstrim)")

        # Verify font cache (Removed -f to make it much faster)
        if shutil.which("fc-cache") and not dry_run:
            executor.submit(run_command, ["fc-cache"], capture=True)
            opt_log("System font cache refreshed")

        # DNS Flush
        dns_cmd = None
        if shutil.which("resolvectl"): dns_cmd = ["resolvectl", "flush-caches"]
        elif shutil.which("nscd"): dns_cmd = ["nscd", "-i", "hosts"]
        
        if dns_cmd and not dry_run:
            executor.submit(run_command, dns_cmd, use_sudo=True, capture=True)
            opt_log("DNS resolver cache flushed")

    # 2. Sequence Tasks (but optimized)
    vacuum_databases(dry_run=dry_run)
    cleanup_zombie_autostart(dry_run=dry_run)
    
    thumb_cache = os.path.expanduser("~/.cache/thumbnails")
    if os.path.exists(thumb_cache) and not dry_run:
        shutil.rmtree(thumb_cache, ignore_errors=True)
        opt_log("Desktop thumbnail cache cleared")

    optimize_memory_advanced(dry_run=dry_run)

    duration = time.time() - start_time
    print(f"\n{GREEN}{BOLD}✨ All tasks completed in {duration:.1f}s.{RESET}")
