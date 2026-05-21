import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from .file_ops import bytes_to_human

def get_mem_info():
    """Read RAM info from /proc/meminfo."""
    try:
        with open('/proc/meminfo', 'r') as f:
            lines = f.readlines()
            total = 0
            available = 0
            for line in lines:
                if 'MemTotal' in line:
                    total = int(line.split()[1]) * 1024
                if 'MemAvailable' in line:
                    available = int(line.split()[1]) * 1024
            used = total - available
            return bytes_to_human(used), bytes_to_human(total)
    except:
        return "Unknown", "Unknown"

def get_uptime():
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    except:
        return "Unknown"

def get_battery_info():
    """Get battery capacity, health, and cycle count."""
    try:
        bat_path = Path("/sys/class/power_supply/BAT0")
        if not bat_path.exists():
            return None
            
        with open(bat_path / "capacity", "r") as f:
            capacity = f.read().strip()
        
        # Health calculation
        try:
            with open(bat_path / "energy_full_design", "r") as f:
                design = int(f.read().strip())
            with open(bat_path / "energy_full", "r") as f:
                full = int(f.read().strip())
            health = (full / design) * 100
            health_str = f" (Health: {health:.1f}%)"
        except:
            health_str = ""
            
        # Cycle count
        cycles_str = ""
        try:
            with open(bat_path / "cycle_count", "r") as f:
                cycles = f.read().strip()
                if cycles and cycles != "0":
                    cycles_str = f" | Cycles: {cycles}"
        except:
            pass
            
        return f"{capacity}%{health_str}{cycles_str}"
    except:
        return "N/A"

def get_network_traffic():
    """Get total network traffic since boot."""
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:] # Skip headers
            rx = 0
            tx = 0
            for line in lines:
                parts = line.split()
                if parts[0] == "lo:": continue
                rx += int(parts[1])
                tx += int(parts[9])
            return bytes_to_human(rx), bytes_to_human(tx)
    except:
        return "N/A", "N/A"

def get_ssd_info():
    """Try to find SSD health info from /sys (limited availability without root/smartctl)."""
    try:
        # NVMe specific health (some kernels expose this)
        nvme_path = Path("/sys/class/nvme/nvme0/device/smart_log")
        if nvme_path.exists():
            # This is binary data, hard to parse without root. 
            # Fallback to model name
            pass
        
        # Check for model and temperature
        drive_path = Path("/sys/class/block/nvme0n1/device")
        if not drive_path.exists():
            drive_path = Path("/sys/class/block/sda/device")
            
        if drive_path.exists():
            with open(drive_path / "model", "r") as f:
                model = f.read().strip()
            return model
    except:
        pass
    return "Generic Drive"

def get_cpu_temp():
    """Try to read CPU temperature from /sys/class/thermal."""
    try:
        temp_path = Path("/sys/class/thermal/thermal_zone0/temp")
        if temp_path.exists():
            with open(temp_path, "r") as f:
                temp_mc = int(f.read().strip())
                return f"{temp_mc / 1000:.1f}°C"
    except:
        pass
    return "N/A"

def show_status():
    print(f"\n\033[1;36m🛡️  System Health Status ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\033[0m")
    print("-" * 50)
    
    uptime = get_uptime()
    cpu_load = os.getloadavg()
    cpu_temp = get_cpu_temp()
    used_mem, total_mem = get_mem_info()
    battery = get_battery_info()
    rx, tx = get_network_traffic()
    drive = get_ssd_info()
    
    home_stats = shutil.disk_usage(os.path.expanduser("~"))
    
    print(f"⏱️  Uptime:       {uptime}")
    print(f"📊 CPU Load:     {cpu_load[0]:.2f}, {cpu_load[1]:.2f}, {cpu_load[2]:.2f} (1m, 5m, 15m)")
    print(f"🌡️  CPU Temp:     {cpu_temp}")
    print(f"🧠 Memory:       {used_mem} / {total_mem}")
    
    # Align Disk info: Size first, then model in parentheses at the end
    disk_size_str = f"{bytes_to_human(home_stats.used)} / {bytes_to_human(home_stats.total)} used"
    print(f"💾 Disk:         {disk_size_str:<30} ({drive})")
    
    if battery:
        print(f"🔋 Battery:      {battery}")
    
    print(f"🌐 Network:      ↓ {rx} / ↑ {tx} (Total)")
    print("-" * 50)
