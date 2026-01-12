# eSim Docker

<p align="center">
  <img src="assets/esim_logo.png" alt="eSim Logo" width="80"/>
  <img src="assets/esim_text.png" alt="eSim" width="200"/>
</p>

<p align="center">
  <b>Run eSim anywhere using Docker - No installation required!</b>
</p>

<p align="center">
  <a href="../../releases/latest">Download Launcher</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#troubleshooting">Troubleshooting</a>
</p>

---

## About

This project provides a Docker-based solution to run **eSim** (Electronic Circuit Simulation) on any operating system. eSim is developed by FOSSEE, IIT Bombay and integrates KiCad, Ngspice, and Python for circuit design and simulation.

Instead of going through the complex native installation, you can just download our launcher and start using eSim in minutes.

**What's included:**
- KiCad for schematic design
- Ngspice for SPICE simulation  
- GAW3 analog waveform viewer
- All eSim libraries pre-configured

---

## Quick Start

### Step 1: Get Docker

Download and install [Docker Desktop](https://www.docker.com/products/docker-desktop) for your OS.

### Step 2: Download the Launcher

Go to [Releases](../../releases/latest) and download:
- Windows: `eSim-Launcher-Windows.exe`
- Linux: `eSim-Launcher-Linux`
- macOS: `eSim-Launcher-macOS`

### Step 3: Run it

Double-click the launcher. You'll see a menu:

```
1. Launch VNC Mode (Browser - Recommended)
2. Launch Native X11 Mode  
3. Update / Reinstall Image
4. Build from Source
0. Exit
```

Choose option 1 and eSim will open in your browser!

<!-- 
Screenshot placeholder - add actual screenshot here
![eSim in VNC Mode](screenshots/vnc_mode.png)
-->

---

## How it Works

The launcher pulls a pre-built Docker image (~1.5GB download) containing the complete eSim environment. Your projects are saved to `~/eSim_Workspace` on your computer, so they persist even after closing the container.

**VNC Mode** opens eSim in your web browser - works everywhere, no extra software needed.

**X11 Mode** opens eSim in a native window - requires an X server (VcXsrv on Windows, XQuartz on macOS).

---

## Command Line Usage

If you prefer the terminal:

```bash
# Interactive menu
python run_esim_docker.py

# Direct VNC mode
python run_esim_docker.py --vnc

# Direct X11 mode
python run_esim_docker.py --x11

# Force update image
python run_esim_docker.py --pull
```

---

## Troubleshooting

### Docker not running
Make sure Docker Desktop is open and fully started (the whale icon should be stable).

### Port already in use
The launcher auto-finds free ports. If it still fails, restart your computer.

### VNC shows blank/error
Wait a few seconds and refresh the browser. eSim takes a moment to start.

### Windows: Virtualization error
Enable Intel VT-x or AMD-V in your BIOS settings.

---

## Building from Source

If you want to build the Docker image yourself instead of pulling:

```bash
docker build -t esim:latest .
python run_esim_docker.py --build
```

---

## Project Structure

```
├── Dockerfile           # Multi-stage Docker build
├── run_esim_docker.py   # Launcher script
├── eSim.spec            # PyInstaller config
├── README.md            # This file
└── .github/workflows/   # CI/CD for releases
```

---

## Credits

- **eSim** - FOSSEE Team, IIT Bombay
- **KiCad** - KiCad Developers
- **Ngspice** - Ngspice Team
- **GAW3** - Hervé Quillévéré, Stefan Schippers

This Docker launcher was created as part of the FOSSEE Internship program.

---

## License

GPL-3.0 - Same as eSim
