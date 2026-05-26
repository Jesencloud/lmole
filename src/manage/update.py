import subprocess
import os

def run_update():
    """Updates topo by re-running the official installation script."""
    # ANSI Colors
    CYAN = "\033[1;36m"
    GRAY = "\033[1;90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    print(f"\n {CYAN}🚀 Checking for updates and refreshing Topo...{RESET}")
    
    # We leverage the existing install.sh which is architecture-aware and professional
    install_cmd = "curl -fsSL https://raw.githubusercontent.com/Jesencloud/Topo/main/install.sh | bash"
    
    try:
        # Use shell=True to handle the pipe directly
        process = subprocess.run(install_cmd, shell=True)
        
        if process.returncode == 0:
            print(f"\n {CYAN}✨ Topo has been successfully updated!{RESET}")
        else:
            print(f"\n \033[1;31m❌ Update failed with exit code {process.returncode}{RESET}")
            
    except Exception as e:
        print(f"\n \033[1;31m❌ Error during update: {e}{RESET}")
