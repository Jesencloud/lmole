import shutil
import subprocess
import os
import time
import sqlite3
from pathlib import Path
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

def vacuum_databases(dry_run=False):
    """Ported from Mole: Optimizes SQLite databases for browsers to improve performance."""
    targets = [
        # Firefox
        "~/.mozilla/firefox/*/places.sqlite",
        "~/.mozilla/firefox/*/cookies.sqlite",
        # Chrome/Brave/Edge
        "~/.config/google-chrome/Default/History",
        "~/.config/BraveSoftware/Brave-Browser/Default/History",
        "~/.config/microsoft-edge/Default/History",
    ]
    
    count = 0
    total_saved = 0
    
    for pattern in targets:
        path_obj = Path(pattern).expanduser()
        parent = path_obj.parent
        glob_pattern = path_obj.name
        
        if not parent.exists(): continue
        
        for db_file in parent.glob(glob_pattern):
            if db_file.is_file():
                try:
                    old_size = get_size(db_file)
                    if dry_run:
                        count += 1
                        continue
                    
                    # Connect and run VACUUM
                    conn = sqlite3.connect(db_file, timeout=2)
                    conn.execute("VACUUM")
                    conn.close()
                    
                    new_size = get_size(db_file)
                    total_saved += (old_size - new_size)
                    count += 1
                except:
                    # Database probably locked by running browser, skip safely
                    continue
    
    if count > 0:
        saved_str = f" (compressed {bytes_to_human(total_saved)})" if total_saved > 0 else ""
        opt_log(f"Optimized {count} browser database(s){saved_str}", skipped=dry_run)

def cleanup_zombie_autostart(dry_run=False):
    """Ported from Mole: Removes autostart entries for uninstalled applications."""
    autostart_dir = Path.home() / ".config" / "autostart"
    if not autostart_dir.exists(): return

    zombies = 0
    for desktop_file in autostart_dir.glob("*.desktop"):
        try:
            is_zombie = False
            with open(desktop_file, 'r') as f:
                for line in f:
                    if line.startswith('Exec='):
                        cmd = line.split('=', 1)[1].strip().split()[0]
                        # If the command is an absolute path that doesn't exist
                        if cmd.startswith('/') and not os.path.exists(cmd):
                            is_zombie = True
                        # If it's a bare command that isn't in PATH
                        elif not cmd.startswith('/') and not shutil.which(cmd):
                            is_zombie = True
                        break
            
            if is_zombie:
                if not dry_run:
                    desktop_file.unlink()
                zombies += 1
        except: continue
    
    if zombies > 0:
        opt_log(f"Removed {zombies} zombie autostart entries", skipped=dry_run)

def optimize_memory_advanced(dry_run=False):
    """Advanced memory management: release PageCache and optimize Swap if needed."""
    # 1. PageCache
    if has_sudo():
        if not dry_run:
            subprocess.run(["sudo", "bash", "-c", "sync; echo 1 > /proc/sys/vm/drop_caches"], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opt_log("PageCache released (Memory relief)", skipped=dry_run)

    # 2. Swap Reset (Only if swap usage is high and RAM is plenty)
    try:
        with open("/proc/meminfo", "r") as f:
            mem = {l.split(":")[0]: int(l.split(":")[1].split()[0]) for l in f.readlines()}
        
        swap_used = mem.get("SwapTotal", 0) - mem.get("SwapFree", 0)
        ram_free = mem.get("MemAvailable", 0)
        
        # If we are using > 500MB of swap but have > 2GB RAM available
        if swap_used > 512000 and ram_free > 2048000 and has_sudo():
            if not dry_run:
                # This can take a while, so we show a sub-status
                print(f"    {GRAY}↳ Resetting Swap to improve latency...{RESET}")
                subprocess.run(["sudo", "swapoff", "-a"], capture_output=True)
                subprocess.run(["sudo", "swapon", "-a"], capture_output=True)
                opt_log("Swap space reset (Latent memory reclaimed)")
            else:
                opt_log("Swap space could be optimized", skipped=True)
    except: pass

def optimize_system(dry_run=False):
    os.system('clear')
    print(f"{BLUE}{BOLD}System Optimization{RESET}")
    print(f"{GRAY}Running maintenance tasks...{RESET}\n")
    
    # 1. Essential Maintenance
    if shutil.which("fstrim"):
        if not dry_run:
            run_command(["fstrim", "-av"], use_sudo=True, capture=True)
        opt_log("SSD partitions trimmed (fstrim)", skipped=dry_run)
    
    dns_flushed = False
    if shutil.which("resolvectl"):
        if not dry_run: run_command(["resolvectl", "flush-caches"], use_sudo=True, capture=True)
        dns_flushed = True
    elif shutil.which("nscd"):
        if not dry_run: run_command(["nscd", "-i", "hosts"], use_sudo=True, capture=True)
        dns_flushed = True
    if dns_flushed: opt_log("DNS resolver cache flushed", skipped=dry_run)

    if shutil.which("fc-cache"):
        if not dry_run: run_command(["fc-cache", "-f"], capture=True)
        opt_log("System font cache verified", skipped=dry_run)

    # 2. Ported Advanced Tasks
    vacuum_databases(dry_run=dry_run)
    cleanup_zombie_autostart(dry_run=dry_run)
    
    # 3. Memory & Storage Cleanup
    thumb_cache = os.path.expanduser("~/.cache/thumbnails")
    if os.path.exists(thumb_cache):
        if not dry_run: shutil.rmtree(thumb_cache, ignore_errors=True)
        opt_log("Desktop thumbnail cache refreshed", skipped=dry_run)

    optimize_memory_advanced(dry_run=dry_run)

    print(f"\n{GREEN}{BOLD}✨ All optimization tasks completed.{RESET}")
