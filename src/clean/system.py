import shutil
from src.core.system import get_os_id, run_command

def clean_package_manager(dry_run=False):
    freed = 0
    os_id = get_os_id()
    if os_id in ("fedora", "rhel", "centos"):
        if shutil.which("dnf"):
            status = "would be cleaned" if dry_run else "Cleaning"
            print(f"  \033[0;32m✓\033[0m {status} DNF cache...")
            if not dry_run:
                run_command(["dnf", "clean", "all"], use_sudo=True, capture=False)
    elif os_id in ("ubuntu", "debian"):
        if shutil.which("apt-get"):
            status = "would be cleaned" if dry_run else "Cleaning"
            print(f"  \033[0;32m✓\033[0m {status} APT cache...")
            if not dry_run:
                run_command(["apt-get", "clean"], use_sudo=True, capture=False)
                run_command(["apt-get", "autoremove", "-y"], use_sudo=True, capture=False)
    elif os_id == "arch":
        if shutil.which("pacman"):
            status = "would be cleaned" if dry_run else "Cleaning"
            print(f"  \033[0;32m✓\033[0m {status} Pacman cache...")
            if not dry_run:
                run_command(["pacman", "-Sc", "--noconfirm"], use_sudo=True, capture=False)
    return 0, 0, 1 # size, items, categories

def clean_journal(dry_run=False):
    if shutil.which("journalctl"):
        status = "would be vacuumed" if dry_run else "Vacuuming"
        print(f"  \033[0;32m✓\033[0m {status} journal logs...")
        if not dry_run:
            run_command(["journalctl", "--vacuum-time=7d"], use_sudo=True, capture=False)
    return 0, 0, 1 # size, items, categories

