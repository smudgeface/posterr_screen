# Claude Memory

## User Information
- Personal GitHub: https://github.com/smudgeface

## Project: Posterr Screen

### Overview
Raspberry Pi kiosk system that displays Posterr in a custom Samsung S24B300 monitor frame. The system includes:
- DDC/CI monitor control over HDMI
- Python Flask HTTP server for remote control
- HomeKit integration via Homebridge HTTP Lightbulb plugin
- WiFi stability monitoring and auto-recovery

### GitHub Repository
- Repo: https://github.com/smudgeface/posterr_screen
- Files are checked into git and pushed to GitHub
- Local workspace: /Users/jordan/Development/Personal/posterr_screen

### Network Configuration
- **Posterr Server**: 192.168.20.10 (hosts Posterr kiosk interface on port 9876)
- **Raspberry Pi**: 192.168.20.146 (runs monitor control HTTP server on port 5000)
  - Username: `pi`
  - Password: `p3pp3rc4t`
  - SSH requires password authentication (publickey disabled)

### SSH Connection to Pi
**IMPORTANT**: Always use sshpass with password authentication:
```bash
sshpass -p 'p3pp3rc4t' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no pi@192.168.20.146 "command"
```

**File Transfer (SCP)**:
```bash
sshpass -p 'p3pp3rc4t' scp -o StrictHostKeyChecking=no /local/file pi@192.168.20.146:~/remote-file
```

### File Locations on Pi
**CRITICAL**: All project files are in the Pi's home directory (`/home/pi/`), NOT in a subdirectory:
- `/home/pi/monitor-http-server.py` - Flask HTTP server (main application)
- `/home/pi/monitor-http-server.service` - Systemd service definition
- `/home/pi/monitor-on.sh` - DDC/CI power on script
- `/home/pi/monitor-off.sh` - DDC/CI power off script
- `/home/pi/install-monitor-http-server.sh` - Installation script
- `/home/pi/uninstall-monitor-http-server.sh` - Uninstallation script
- `/home/pi/fix-wifi-stability.sh` - WiFi stability fix
- `/home/pi/uninstall-wifi-stability.sh` - WiFi fix uninstaller
- `/home/pi/README.md` - Project documentation

### Deployment Workflow
When making changes to Python server or scripts:
1. Edit files in local workspace
2. Commit and push to GitHub
3. Copy updated file(s) to Pi via SCP
4. Restart the service

**Example deployment**:
```bash
# After editing monitor-http-server.py locally
git add monitor-http-server.py
git commit -m "Description of changes"
git push

# Copy to Pi
sshpass -p 'p3pp3rc4t' scp -o StrictHostKeyChecking=no /Users/jordan/Development/Personal/posterr_screen/monitor-http-server.py pi@192.168.20.146:~/monitor-http-server.py

# Restart service
sshpass -p 'p3pp3rc4t' ssh -o StrictHostKeyChecking=no -o PreferredAuthentications=password -o PubkeyAuthentication=no pi@192.168.20.146 "sudo systemctl restart monitor-http-server"
```

### Service Management
The HTTP server runs as a systemd service:
```bash
# Check status
sudo systemctl status monitor-http-server

# Restart service (required after updating Python file)
sudo systemctl restart monitor-http-server

# View logs in real-time
sudo journalctl -u monitor-http-server -f

# Enable/disable auto-start
sudo systemctl enable monitor-http-server
sudo systemctl disable monitor-http-server
```

### Monitor Control
- **DDC/CI Bus**: 20 (`/dev/i2c-20`)
- **Power Feature**: d6 (01 = on, 04 = off)
- **Brightness Feature**: 10 (0-100)

**HTTP API Endpoints**:
- `http://192.168.20.146:5000/` - Web control interface
- `http://192.168.20.146:5000/on` - Turn monitor on
- `http://192.168.20.146:5000/off` - Turn monitor off
- `http://192.168.20.146:5000/status` - Get power state
- `http://192.168.20.146:5000/brightness` - Get brightness level
- `http://192.168.20.146:5000/brightness/<value>` - Set brightness (0-100)
- `http://192.168.20.146:5000/watchdog` - Get WiFi watchdog status
- `http://192.168.20.146:5000/health` - Health check

### Known Issues & Solutions
1. **Brightness wake-up issue**: When waking from brightness 0, the monitor needs 2.5 seconds to initialize before accepting brightness commands. This is handled in monitor-http-server.py by detecting 0→non-zero transitions and adding a delay.

2. **WiFi stability**: The Pi's WiFi can drop due to power management. The fix-wifi-stability.sh script disables power management and sets up a watchdog that monitors connectivity and auto-restarts the interface if needed.

3. **SSH connection**: Only password authentication works. Don't try to use SSH keys - use sshpass as shown above.

4. **File locations**: Files are NOT in a posterr_screen subdirectory on the Pi - they're directly in /home/pi/
