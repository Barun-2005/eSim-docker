"""
eSim Docker Launcher
FOSSEE IIT Bombay Internship Project

Simple launcher to run eSim in Docker with VNC or X11 display.
"""

import os
import sys
import platform
import subprocess
import shutil
import socket
import webbrowser
import time
import tempfile
from pathlib import Path
from typing import Tuple, Optional

# Docker image to pull (GitHub Container Registry)
DOCKER_IMAGE = "ghcr.io/barun-2005/esim-docker:latest"
LOCAL_IMAGE = "esim:latest"
CONTAINER_NAME = "esim-container"
DOCKERFILE_DIR = Path(__file__).parent.resolve()
WORKSPACE_DIR_NAME = "eSim_Workspace"

# VcXsrv config for Windows X11 mode
VCXSRV_CONFIG = """<?xml version="1.0" encoding="UTF-8"?>
<XLaunch WindowMode="MultiWindow" ClientMode="NoClient" LocalClient="False" Display="-1" LocalProgram="xcalc" RemoteProgram="xterm" RemotePassword="" PrivateKey="" RemoteHost="" RemoteUser="" XDMCPHost="" XDMCPBroadcast="False" XDMCPIndirect="False" Clipboard="True" ClipboardPrimary="True" ExtraParams="" Wgl="True" DisableAC="True" XDMCPTerminate="False"/>
"""


def run_cmd(cmd, capture=False, check=True, shell=False):
    """Run a shell command."""
    if capture:
        return subprocess.run(cmd, capture_output=True, text=True, check=check, shell=shell)
    return subprocess.run(cmd, check=check, shell=shell)


def cmd_exists(cmd):
    """Check if command is available."""
    return shutil.which(cmd) is not None


def clear():
    """Clear terminal."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_banner():
    """Show the launcher banner."""
    clear()
    print("""
    ╔══════════════════════════════════════════╗
    ║          eSim Docker Launcher            ║
    ║        FOSSEE, IIT Bombay                ║
    ╚══════════════════════════════════════════╝
    """)


def info(msg):
    print(f"  [i] {msg}")

def ok(msg):
    print(f"  [+] {msg}")

def warn(msg):
    print(f"  [!] {msg}")

def err(msg):
    print(f"  [-] {msg}", file=sys.stderr)


def find_free_port(start=6080, tries=20):
    """Find an available port."""
    for port in range(start, start + tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No free port found between {start}-{start+tries}")


def get_os():
    """Detect operating system."""
    system = platform.system().lower()
    if system == "linux":
        try:
            with open("/proc/version") as f:
                if "microsoft" in f.read().lower():
                    return "wsl2"
        except:
            pass
        return "linux"
    if system == "windows":
        return "windows"
    if system == "darwin":
        return "macos"
    return system


def is_wslg():
    """Check for WSLg support."""
    return (get_os() == "wsl2" and 
            os.environ.get("WAYLAND_DISPLAY") and 
            Path("/mnt/wslg").exists())


# Windows-specific installers

def install_docker_windows():
    """Try to install Docker on Windows via winget."""
    info("Docker not found. Trying to install with winget...")
    print()
    resp = input("  Install Docker Desktop? (y/n): ").strip().lower()
    if resp != 'y':
        warn("Skipped Docker installation")
        return False
    try:
        subprocess.run(["winget", "install", "-e", "--id", "Docker.DockerDesktop", 
                       "--accept-source-agreements"], check=True)
        ok("Docker installed! Please restart your computer.")
        input("\n  Press Enter...")
        return True
    except Exception as e:
        err(f"Install failed: {e}")
        info("Download manually: https://docker.com/products/docker-desktop")
        return False


def install_vcxsrv_windows():
    """Install VcXsrv on Windows."""
    info("VcXsrv not found (needed for X11 mode)")
    resp = input("  Install VcXsrv? (y/n): ").strip().lower()
    if resp != 'y':
        return False
    try:
        subprocess.run(["winget", "install", "-e", "--id", "marha.VcXsrv",
                       "--accept-source-agreements"], check=True)
        ok("VcXsrv installed!")
        return True
    except:
        err("Install failed")
        info("Download: https://sourceforge.net/projects/vcxsrv/")
        return False


def start_vcxsrv():
    """Start VcXsrv X server on Windows."""
    # Common install paths
    paths = [
        Path(os.environ.get("PROGRAMFILES", "")) / "VcXsrv" / "vcxsrv.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "VcXsrv" / "vcxsrv.exe",
    ]
    
    vcxsrv = None
    for p in paths:
        if p.exists():
            vcxsrv = p
            break
    
    if not vcxsrv:
        if not install_vcxsrv_windows():
            return False
        for p in paths:
            if p.exists():
                vcxsrv = p
                break
        if not vcxsrv:
            err("VcXsrv not found after install")
            return False
    
    # Check if already running
    try:
        result = subprocess.run(["tasklist", "/FI", "IMAGENAME eq vcxsrv.exe"], 
                               capture_output=True, text=True)
        if "vcxsrv.exe" in result.stdout.lower():
            ok("VcXsrv already running")
            return True
    except:
        pass
    
    # Write config and launch
    config = Path(tempfile.gettempdir()) / "esim_xserver.xlaunch"
    config.write_text(VCXSRV_CONFIG)
    
    info("Starting VcXsrv...")
    try:
        xlaunch = vcxsrv.parent / "xlaunch.exe"
        if xlaunch.exists():
            subprocess.Popen([str(xlaunch), "-run", str(config)],
                           creationflags=subprocess.DETACHED_PROCESS)
        else:
            subprocess.Popen([str(vcxsrv), ":0", "-multiwindow", "-clipboard", "-wgl", "-ac"],
                           creationflags=subprocess.DETACHED_PROCESS)
        time.sleep(2)
        ok("VcXsrv started")
        return True
    except Exception as e:
        err(f"Failed to start VcXsrv: {e}")
        return False


def get_display_args(os_type):
    """Get Docker display environment for X11 mode."""
    if os_type == "linux":
        display = os.environ.get("DISPLAY", ":0")
        try:
            subprocess.run(["xhost", "+local:docker"], capture_output=True)
        except:
            pass
        return display, ["-e", f"DISPLAY={display}", "-v", "/tmp/.X11-unix:/tmp/.X11-unix:rw"]
    
    if os_type == "wsl2":
        if is_wslg():
            display = os.environ.get("DISPLAY", ":0")
            return display, ["-e", f"DISPLAY={display}", "-e", "QT_QPA_PLATFORM=xcb",
                           "-v", "/tmp/.X11-unix:/tmp/.X11-unix:rw"]
        # Legacy WSL2
        try:
            with open("/etc/resolv.conf") as f:
                for line in f:
                    if line.startswith("nameserver"):
                        host_ip = line.split()[1]
                        break
                else:
                    host_ip = "localhost"
        except:
            host_ip = "localhost"
        return f"{host_ip}:0.0", ["-e", f"DISPLAY={host_ip}:0.0", "-e", "LIBGL_ALWAYS_INDIRECT=1"]
    
    if os_type == "windows":
        return "host.docker.internal:0.0", [
            "-e", "DISPLAY=host.docker.internal:0.0",
            "-e", "QT_X11_NO_MITSHM=1", "-e", "NO_AT_BRIDGE=1", "-e", "GTK_A11Y=none"
        ]
    
    if os_type == "macos":
        return "host.docker.internal:0", [
            "-e", "DISPLAY=host.docker.internal:0", "-e", "LIBGL_ALWAYS_INDIRECT=1"
        ]
    
    return ":0", ["-e", "DISPLAY=:0"]


# Docker operations

def docker_ok():
    """Check if Docker is installed and running."""
    if not cmd_exists("docker"):
        return False
    try:
        run_cmd(["docker", "info"], capture=True)
        return True
    except:
        return False


def image_exists(image):
    """Check if Docker image exists locally."""
    try:
        result = run_cmd(["docker", "images", "-q", image], capture=True)
        return bool(result.stdout.strip())
    except:
        return False


def pull_image(image=DOCKER_IMAGE):
    """Pull image from registry."""
    info(f"Pulling {image}...")
    info("This may take a few minutes...")
    print()
    try:
        subprocess.run(["docker", "pull", image], check=True)
        print()
        ok("Image downloaded!")
        return True
    except:
        err("Pull failed")
        return False


def build_image():
    """Build image from local Dockerfile."""
    dockerfile = DOCKERFILE_DIR / "Dockerfile"
    if not dockerfile.exists():
        err(f"Dockerfile not found: {dockerfile}")
        return False
    
    info("Building from Dockerfile (this takes 10-15 min)...")
    print()
    try:
        subprocess.run(["docker", "build", "-t", LOCAL_IMAGE, str(DOCKERFILE_DIR)], check=True)
        print()
        ok("Build complete!")
        return True
    except:
        err("Build failed")
        return False


def stop_container():
    """Remove existing container if running."""
    run_cmd(["docker", "rm", "-f", CONTAINER_NAME], capture=True, check=False)


def get_workspace():
    """Create and return workspace path."""
    ws = Path.home() / WORKSPACE_DIR_NAME
    ws.mkdir(exist_ok=True)
    return ws


def get_image(build_local=False):
    """Get the Docker image to use."""
    if build_local:
        return LOCAL_IMAGE if build_image() else None
    
    # Try remote first
    if image_exists(DOCKER_IMAGE):
        return DOCKER_IMAGE
    
    print()
    if pull_image(DOCKER_IMAGE):
        return DOCKER_IMAGE
    
    # Fallback to local
    if image_exists(LOCAL_IMAGE):
        warn(f"Using local image: {LOCAL_IMAGE}")
        return LOCAL_IMAGE
    
    warn("Remote unavailable, trying local build...")
    return LOCAL_IMAGE if build_image() else None


# Launch modes

def launch_vnc(image, workspace):
    """Run eSim in VNC mode (browser)."""
    stop_container()
    
    try:
        vnc_port = find_free_port(6080)
        server_port = find_free_port(5901)
    except RuntimeError as e:
        err(str(e))
        return 1
    
    cmd = [
        "docker", "run", "--rm", "-it", "--name", CONTAINER_NAME,
        "--shm-size=256m", "--ipc=host",
        "-v", f"{workspace}:/home/esim-user/eSim-Workspace:rw",
        "-p", f"{vnc_port}:6080", "-p", f"{server_port}:5901",
        "-e", "USE_VNC=1", image, "--vnc"
    ]
    
    url = f"http://localhost:{vnc_port}/vnc.html"
    
    print()
    print("  " + "=" * 50)
    ok("VNC Mode")
    print()
    print(f"     Browser: {url}")
    print(f"     VNC:     localhost:{server_port}")
    print()
    print("     Opening browser...")
    print("  " + "=" * 50)
    print()
    
    # Open browser after delay
    def open_browser():
        time.sleep(3)
        webbrowser.open(url)
    
    import threading
    threading.Thread(target=open_browser, daemon=True).start()
    
    return subprocess.run(cmd).returncode


def launch_x11(image, workspace, os_type):
    """Run eSim in X11 mode (native window)."""
    if os_type == "windows":
        if not start_vcxsrv():
            err("X11 server not available")
            return 1
    
    display, display_args = get_display_args(os_type)
    stop_container()
    
    cmd = [
        "docker", "run", "--rm", "-it", "--name", CONTAINER_NAME,
        "--shm-size=256m", "--ipc=host",
        "-v", f"{workspace}:/home/esim-user/eSim-Workspace:rw",
    ] + display_args + [image]
    
    print()
    print("  " + "=" * 50)
    ok("X11 Mode")
    print(f"     Display: {display}")
    print("  " + "=" * 50)
    print()
    
    return subprocess.run(cmd).returncode


# Menu system

def show_menu():
    """Display interactive menu."""
    show_banner()
    os_type = get_os()
    print(f"  OS: {os_type.upper()}")
    print()
    print("  1. Launch VNC Mode (Browser)")
    print("  2. Launch X11 Mode (Native Window)")
    print("  3. Update Image")
    print("  4. Build from Source")
    print("  0. Exit")
    print()
    return input("  Choice: ").strip()


def run_menu():
    """Interactive menu loop."""
    while True:
        choice = show_menu()
        
        if choice == "0":
            print()
            info("Bye!")
            return 0
        
        if choice not in ["1", "2", "3", "4"]:
            err("Invalid choice")
            input("\n  Press Enter...")
            continue
        
        # Check Docker
        print()
        if not docker_ok():
            os_type = get_os()
            if os_type == "windows":
                err("Docker not running or not installed")
                if not install_docker_windows():
                    input("\n  Press Enter...")
                    continue
                return 0
            else:
                err("Docker not running. Start Docker Desktop first.")
                input("\n  Press Enter...")
                continue
        
        ok("Docker ready")
        os_type = get_os()
        workspace = get_workspace()
        ok(f"Workspace: {workspace}")
        
        if choice == "3":
            print()
            pull_image(DOCKER_IMAGE)
            input("\n  Press Enter...")
            continue
        
        if choice == "4":
            print()
            build_image()
            input("\n  Press Enter...")
            continue
        
        image = get_image()
        if not image:
            err("No image available")
            input("\n  Press Enter...")
            continue
        
        if choice == "1":
            return launch_vnc(image, workspace)
        if choice == "2":
            return launch_x11(image, workspace, os_type)
    
    return 0


# CLI mode

def run_cli(args):
    """Handle command-line arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(description="eSim Docker Launcher")
    parser.add_argument("--vnc", "-v", action="store_true", help="VNC mode (browser)")
    parser.add_argument("--x11", "-x", action="store_true", help="X11 mode (native)")
    parser.add_argument("--build", "-b", action="store_true", help="Build from Dockerfile")
    parser.add_argument("--pull", "-p", action="store_true", help="Force pull image")
    parser.add_argument("--shell", "-s", action="store_true", help="Open shell only")
    
    opts = parser.parse_args(args)
    
    if not docker_ok():
        os_type = get_os()
        if os_type == "windows":
            err("Docker not running")
            install_docker_windows()
            return 1
        err("Docker not running")
        return 1
    
    os_type = get_os()
    workspace = get_workspace()
    
    if opts.pull:
        if not pull_image():
            return 1
    
    image = get_image(build_local=opts.build)
    if not image:
        err("No image available")
        return 1
    
    if opts.shell:
        stop_container()
        cmd = ["docker", "run", "--rm", "-it", "--name", CONTAINER_NAME,
               "-v", f"{workspace}:/home/esim-user/eSim-Workspace:rw",
               image, "/bin/bash"]
        return subprocess.run(cmd).returncode
    
    if opts.x11:
        return launch_x11(image, workspace, os_type)
    
    return launch_vnc(image, workspace)


# Entry point

def main():
    if len(sys.argv) == 1:
        # No args = interactive menu
        try:
            return run_menu()
        except KeyboardInterrupt:
            print("\n")
            info("Cancelled")
            return 0
    else:
        # CLI mode
        show_banner()
        try:
            return run_cli(sys.argv[1:])
        except KeyboardInterrupt:
            print("\n")
            info("Cancelled")
            return 0


if __name__ == "__main__":
    sys.exit(main())
