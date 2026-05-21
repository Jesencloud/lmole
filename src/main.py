import os
import argparse
import sys
from .clean.system import clean_package_manager, clean_journal
from .clean.dev import clean_developer_tools
from .clean.user import clean_user_data
from .clean.apps import clean_apps_deep
from .clean.optimize import optimize_system
from .core.system import get_os_id, ensure_sudo_session, setup_passwordless_sudo
from .core.status import show_status
from .core.analyze import run_deep_analysis
from .purge.manager import PurgeManager
from .ui.menu import interactive_select
from .ui.tui import main_menu

def run_clean(dry_run=False):
    from .core.file_ops import bytes_to_human
    import shutil
    
    # 1. Prepare categories
    categories = [
        {"name": "Package Manager Cache", "func": clean_package_manager},
        {"name": "System Journal Logs", "func": clean_journal},
        {"name": "User Data & Trash", "func": clean_user_data},
        {"name": "Deep App Caches", "func": clean_apps_deep},
        {"name": "Developer Artifacts", "func": clean_developer_tools}
    ]

    mode_label = "\033[1;36m[PREVIEW]\033[0m" if dry_run else "\033[1;95m[EXECUTING]\033[0m"
    print(f"{mode_label} Starting system cleanup...\n")

    total_size = 0
    total_items = 0
    total_categories = 0

    # 2. Execute all categories one by one
    for cat in categories:
        # We print a clean progress line
        s, i, c = cat["func"](dry_run=dry_run)
        total_size += s
        total_items += i
        total_categories += c

    # 3. Final Summary
    free_now = shutil.disk_usage(os.path.expanduser("~")).free
    
    print("\n" + "=" * 60)
    status_text = "Scan complete (Preview)" if dry_run else "Cleanup complete"
    print(f"\033[1;34m{status_text}\033[0m")
    
    size_label = "Space that can be freed" if dry_run else "Space freed"
    print(f"{size_label}: \033[1;32m{bytes_to_human(total_size)}\033[0m | Items: {total_items} | Categories: {total_categories}")
    
    if not dry_run:
        # Fun fact: 4K movie estimate
        movies = total_size / (8 * 1024 * 1024 * 1024)
        if movies >= 0.1:
            print(f"Equivalent to ~{movies:.1f} 4K movies of storage.")
        print(f"Free space now: {bytes_to_human(free_now)}")
    
    print("=" * 60)
    
    if dry_run:
        print(f"\n{GRAY}ℹ️  Run without --dry-run to actually delete these files.{RESET}")


from .manage.uninstall import UninstallManager
from .ui.navigator import PaginatedSelector, UninstallSelector


def run_purge(dry_run=False):
    while True:
        print("\033[1;95m➤ Project Purge\033[0m")
        manager = PurgeManager()
        results = manager.run_scan()
        
        if not results:
            print("✨ No heavy artifacts found. Your projects are clean!")
            input("\nPress Enter to return to menu...")
            return

        selector = PaginatedSelector("Select Project Artifacts to Purge", results)
        action = selector.run()
        
        if action == "MANAGE_PATHS":
            from .core.config import add_purge_path, remove_purge_path, get_purge_paths
            while True:
                os.system('clear')
                print("\n\033[1;36m⚙️  lmole Purge Settings\033[0m")
                print("-" * 50)
                paths = get_purge_paths()
                print(f"Current Purge Search Paths:")
                for i, p in enumerate(paths):
                    print(f"  [{i+1}] {p}")
                
                print("\nOptions: [A] Add Path | [R] Remove Path | [B] Back to Scan")
                c = input("➤ ").lower()
                if c == 'a':
                    new_p = input("Enter new search path: ")
                    if add_purge_path(new_p): print(f"✅ Added: {new_p}")
                    input("\nPress Enter...")
                elif c == 'r':
                    try:
                        idx = int(input("Enter index to remove: ")) - 1
                        if 0 <= idx < len(paths):
                            remove_purge_path(paths[idx])
                            print(f"✅ Removed path.")
                        else: print("❌ Invalid index.")
                    except: print("❌ Invalid input.")
                    input("\nPress Enter...")
                elif c == 'b':
                    break
            continue # Re-scan with new paths

        if action and isinstance(action, list):
            selected = action
            if dry_run:
                total_size = sum(results[i]['size'] for i in selected)
                from .core.file_ops import bytes_to_human
                print(f"\n🧪 [DRY RUN] Would remove {len(selected)} items, freeing {bytes_to_human(total_size)}")
            else:
                count, total_freed = manager.execute_purge(selected)
                print(f"\n✨ Purge complete: {count} items removed, {total_freed} space freed.")
            input("\nPress Enter to return to menu...")
            break
        else:
            break

def run_uninstall():
    manager = UninstallManager()
    
    while True:
        print("\033[1;95m➤ Uninstall Mode\033[0m")
        apps = manager.run_full_scan()
        
        if not apps:
            print("   No uninstallable apps found.")
            input("\nPress Enter to return to menu...")
            return

        selector = UninstallSelector("Select Application to Uninstall", apps)
        selected_indices = selector.run()
        
        if not selected_indices:
            return # Back to main menu

        # Replicating Screenshot Header
        os.system('clear')
        print(f"\033[1;35m☉ Selected {len(selected_indices)} apps:\033[0m")
        for i, idx in enumerate(selected_indices):
            app = apps[idx]
            last_val = selector._format_time_ago(app['install_time']).replace(" ago", "")
            print(f"{i+1}. {app['name']:<20} {app['size_str']:>10} | Last: {last_val}")
        
        print(f"\n\033[1;35mFiles to be removed:\033[0m\n")
        
        # Confirmation
        confirm = input("➤ Confirm uninstallation? (y/N): ").lower()
        if confirm != 'y':
            continue

        total_freed_all = 0
        removed_names = []
        
        for idx in selected_indices:
            app = apps[idx]
            print(f"\033[1;35m☉ {app['name']}\033[0m , {app['size_str']}")
            
            success, freed_bytes, details = manager.uninstall_app(idx)
            if success:
                total_freed_all += freed_bytes
                removed_names.append(app['name'])
                for is_ok, path in details:
                    icon = "\033[0;32m✓\033[0m" if is_ok else "\033[1;35m☉\033[0m"
                    print(f"  {icon} {path}")
            print(f"\033[0;32m[✓]\033[0m {app['name']}\n")

        # Final Summary (Matching Screenshot)
        from .core.file_ops import bytes_to_human
        print("=" * 70)
        print("\033[1;34mUninstall complete\033[0m")
        names_str = ", ".join(removed_names)
        print(f"Removed {len(removed_names)} app(s), freed \033[1;32m{bytes_to_human(total_freed_all)}\033[0m: {names_str}")
        print("=" * 70)

        choice = input("\nPress Enter to return to application list, any other key to exit... ")
        if choice != "":
            break

from .core.whitelist import add_to_whitelist, remove_from_whitelist

def main():
    parser = argparse.ArgumentParser(description="lmole - Linux System Optimizer (Inspired by Mole)")
    parser.add_argument("command", choices=["clean", "purge", "uninstall", "optimize", "analyze", "status", "whitelist", "authorize", "all"], nargs="?", default=None)
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without deleting")
    parser.add_argument("--version", action="version", version="lmole 0.5.0")
    
    # Whitelist sub-arguments
    parser.add_argument("action", nargs="?", help="Whitelist action: add, remove, list")
    parser.add_argument("path", nargs="?", help="Path for whitelist action")
    
    args = parser.parse_args()

    # Authorization setup command
    if args.command == "authorize":
        setup_passwordless_sudo()
        return

    # Whitelist Management CLI
    if args.command == "whitelist":
        if args.action == "add" and args.path:
            if add_to_whitelist(args.path):
                print(f"✅ Added to whitelist: {args.path}")
            else:
                print(f"ℹ️  Path already whitelisted: {args.path}")
        elif args.action == "remove" and args.path:
            if remove_from_whitelist(args.path):
                print(f"✅ Removed from whitelist: {args.path}")
            else:
                print(f"❌ Path not found in whitelist: {args.path}")
        elif args.action == "list" or not args.action:
            from .core.whitelist import get_whitelist
            w = get_whitelist()
            print("\033[1;36m🛡️  Current Whitelist:\033[0m")
            if not w:
                print("   (Empty)")
            for p in w:
                print(f"   - {p}")
        else:
            print("Usage: lmole whitelist <add|remove|list> [path]")
        return

    # If no command is provided, enter TUI
    if args.command is None:
        while True:
            choice = main_menu()
            if choice == "1":
                run_clean(args.dry_run)
                input("\n\033[1;90mPress Enter to return to Main Menu...\033[0m")
            elif choice == "2":
                run_uninstall()
            elif choice == "3":
                print("🔒 Authorizing optimization tasks...")
                ensure_sudo_session()
                optimize_system(args.dry_run)
                input("\nPress Enter to return to menu...")
            elif choice == "4":
                run_deep_analysis()
            elif choice == "5":
                show_status()
                input("\nPress Enter to return to menu...")
            elif choice == "0" or choice.lower() == "q":
                print("Goodbye!")
                break
        return

    # CLI Mode
    print(f"\033[1;34mlmole 0.5.0 (Python Edition)\033[0m")
    os_id = get_os_id()
    print(f"System: {os_id}\n")

    if args.command in ("clean", "all"):
        run_clean(args.dry_run)

    if args.command in ("purge", "all"):
        run_purge(args.dry_run)

if __name__ == "__main__":
    main()
