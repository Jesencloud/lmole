import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Any
from ..core.system import run_command, get_os_id
from ..core.file_ops import get_size, safe_remove, bytes_to_human

class UninstallManager:
    def __init__(self):
        self.apps: List[Dict[str, Any]] = []

    def _parse_size_to_bytes(self, size_str: str) -> int:
        if not size_str or size_str == "N/A": return 0
        try:
            val_str = ''.join(c for c in size_str if c.isdigit() or c == '.')
            val = float(val_str)
            # Use Base-10 (1000) for consistency with bytes_to_human
            if "GB" in size_str: val *= 1000**3
            elif "MB" in size_str: val *= 1000**2
            elif "KB" in size_str: val *= 1000
            return int(val)
        except:
            return 0

    def scan_flatpaks(self):
        if not shutil.which("flatpak"): return
        try:
            res = subprocess.run(["flatpak", "list", "--columns=name,application,size"], 
                                capture_output=True, text=True)
            if res.returncode == 0:
                for line in res.stdout.strip().split('\n'):
                    parts = line.split('\t')
                    if len(parts) >= 3:
                        name, app_id, size_str = parts[0], parts[1], parts[2]
                        install_path = Path(f"/var/lib/flatpak/app/{app_id}")
                        if not install_path.exists():
                            install_path = Path.home() / f".local/share/flatpak/app/{app_id}"
                        
                        self.apps.append({
                            "name": name,
                            "id": app_id,
                            "type": "Flatpak",
                            "size_str": size_str,
                            "size_bytes": self._parse_size_to_bytes(size_str),
                            "install_time": os.path.getctime(install_path) if install_path.exists() else 0,
                            "data_paths": [Path.home() / f".var/app/{app_id}"]
                        })
        except: pass

    def scan_snaps(self):
        if not shutil.which("snap"): return
        try:
            res = subprocess.run(["snap", "list"], capture_output=True, text=True)
            if res.returncode == 0:
                lines = res.stdout.strip().split('\n')[1:]
                for line in lines:
                    parts = line.split()
                    if parts:
                        name = parts[0]
                        # Snap sizes are tricky, using a placeholder for now
                        self.apps.append({
                            "name": name,
                            "id": name,
                            "type": "Snap",
                            "size_str": "N/A",
                            "size_bytes": 0,
                            "install_time": os.path.getctime(f"/snap/{name}") if os.path.exists(f"/snap/{name}") else 0,
                            "data_paths": [Path.home() / f"snap/{name}"]
                        })
        except: pass

    def scan_native(self):
        os_id = get_os_id()
        desktop_globs = [
            "/usr/share/applications/*.desktop",
            str(Path.home() / ".local/share/applications/*.desktop")
        ]
        
        if os_id in ("fedora", "rhel"):
            try:
                for glob in desktop_globs:
                    cmd = f"rpm -qf {glob} --qf '%{{NAME}}\\t%{{INSTALLTIME}}\\n' 2>/dev/null | sort -u"
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if res.returncode == 0:
                        for line in res.stdout.strip().split('\n'):
                            if not line or "is not owned" in line: continue
                            parts = line.split('\t')
                            name = parts[0]
                            itime = float(parts[1]) if len(parts) > 1 else 0
                            if not any(a['id'] == name for a in self.apps):
                                self.apps.append({
                                    "name": name, "id": name, "type": "DNF",
                                    "size_str": "N/A", "size_bytes": 0,
                                    "install_time": itime,
                                    "data_paths": self._find_user_data(name)
                                })
            except: pass
        elif os_id in ("ubuntu", "debian", "linuxmint"):
            try:
                for glob in desktop_globs:
                    cmd = f"dpkg -S {glob} 2>/dev/null | cut -d: -f1 | sort -u"
                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                    if res.returncode == 0:
                        for name in res.stdout.strip().split('\n'):
                            if not name: continue
                            list_file = Path(f"/var/lib/dpkg/info/{name}.list")
                            if not any(a['id'] == name for a in self.apps):
                                self.apps.append({
                                    "name": name, "id": name, "type": "APT",
                                    "size_str": "N/A", "size_bytes": 0,
                                    "install_time": os.path.getctime(list_file) if list_file.exists() else 0,
                                    "data_paths": self._find_user_data(name)
                                })
            except: pass

    def _find_user_data(self, app_name: str) -> List[Path]:
        paths = []
        # Try multiple naming variants
        variants = [
            app_name.lower(),
            app_name.lower().replace("-", ""),
            app_name.lower().replace(" ", ""),
            app_name.capitalize()
        ]
        
        search_roots = [
            Path.home() / ".config",
            Path.home() / ".local/share",
            Path.home() / ".cache",
            Path.home() / ".var/app" # Flatpak data
        ]
        
        seen = set()
        for root in search_roots:
            if not root.exists(): continue
            for variant in variants:
                p = root / variant
                if p.exists() and str(p) not in seen:
                    paths.append(p)
                    seen.add(str(p))
                    
        return paths

    def run_full_scan(self):
        print("  ⏳ Scanning for installed applications...")
        self.apps = []
        self.scan_flatpaks()
        self.scan_snaps()
        self.scan_native()
        return self.apps

    def uninstall_app(self, app_idx: int, remove_data: bool = True):
        app = self.apps[app_idx]
        removed_details = []
        # Start with the app's own size if it's known
        app_freed_bytes = app['size_bytes']
        
        # 1. System Removal
        success = False
        if app['type'] == "Flatpak":
            res = run_command(["flatpak", "uninstall", "-y", app['id']], capture=False)
            success = (res.returncode == 0)
            if success:
                removed_details.append((True, f"Flatpak: {app['id']}"))
        elif app['type'] == "Snap":
            res = run_command(["snap", "remove", app['id']], use_sudo=True, capture=False)
            success = (res.returncode == 0)
            if success:
                removed_details.append((True, f"Snap: {app['id']}"))
        elif app['type'] in ("DNF", "APT"):
            if app['type'] == "DNF":
                res = run_command(["dnf", "remove", "-y", app['id']], use_sudo=True, capture=False)
                if res.returncode == 0:
                    removed_details.append((True, f"Package: {app['id']}"))
                    run_command(["dnf", "autoremove", "-y"], use_sudo=True, capture=True)
            else:
                res = run_command(["apt-get", "purge", "-y", app['id']], use_sudo=True, capture=False)
                if res.returncode == 0:
                    removed_details.append((True, f"Package: {app['id']} (purged)"))
                    run_command(["apt-get", "autoremove", "-y"], use_sudo=True, capture=True)
            success = (res.returncode == 0)

        # 2. Data Removal
        if success and remove_data:
            for p in app['data_paths']:
                if p.exists():
                    s = get_size(p)
                    if safe_remove(p, use_trash=True)[0]:
                        app_freed_bytes += s
                        removed_details.append((True, str(p.relative_to(Path.home()))))
        
        return success, app_freed_bytes, removed_details
