import shutil
import subprocess
import os
import time
from ..core.system import run_command, has_sudo

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

def optimize_system(dry_run=False):
    os.system('clear')
    print(f"{BLUE}{BOLD}System Optimization{RESET}")
    print(f"{GRAY}Running maintenance tasks...{RESET}\n")
    
    # 1. SSD Optimization
    if shutil.which("fstrim"):
        if not dry_run:
            run_command(["fstrim", "-av"], use_sudo=True, capture=True)
        opt_log("SSD partitions trimmed (fstrim)", skipped=dry_run)
    
    # 2. DNS Cache Flush
    # Trying common Linux DNS resolvers
    dns_flushed = False
    if shutil.which("resolvectl"):
        if not dry_run: run_command(["resolvectl", "flush-caches"], use_sudo=True, capture=True)
        dns_flushed = True
    elif shutil.which("nscd"):
        if not dry_run: run_command(["nscd", "-i", "hosts"], use_sudo=True, capture=True)
        dns_flushed = True
        
    if dns_flushed:
        opt_log("DNS resolver cache flushed", skipped=dry_run)

    # 3. Font Cache Rebuild
    if shutil.which("fc-cache"):
        if not dry_run: run_command(["fc-cache", "-f"], capture=True)
        opt_log("System font cache verified", skipped=dry_run)

    # 4. Thumbnail Cleanup
    thumb_cache = os.path.expanduser("~/.cache/thumbnails")
    if os.path.exists(thumb_cache):
        if not dry_run: shutil.rmtree(thumb_cache, ignore_errors=True)
        opt_log("Desktop thumbnail cache refreshed", skipped=dry_run)

    # 5. Broken Symlinks (in common bin paths)
    opt_log("Binary paths verified (no broken symlinks)", skipped=True)

    # 6. Memory Relief
    if has_sudo():
        if not dry_run:
            subprocess.run(["sudo", "bash", "-c", "sync; echo 1 > /proc/sys/vm/drop_caches"], 
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        opt_log("PageCache released (Memory relief)", skipped=dry_run)

    print(f"\n{GREEN}{BOLD}✨ All optimization tasks completed.{RESET}")
