# Raspberry Pi Kiosk Setup

## Hardware
- **Device**: Raspberry Pi Model B (4GB RAM)
- **Display**: Samsung S24B300 monitor (manufactured 2013, week 6)
  - Disassembled and mounted in a custom frame
  - Original buttons/controls removed (not accessible)
  - Connected via HDMI-1 port
  - Rotated 90 degrees (portrait orientation)

## Network
- **IP Address**: 192.168.20.10 (hosting Postarr)
- **Pi IP**: 192.168.20.146
- **User**: pi
- **Password**: p3pp3rc4t

## Kiosk Configuration

### Auto-start on Boot (~/.bash_profile)
The Pi automatically starts the graphical kiosk when logged in at the physical console (tty1):

```bash
if [ "$(tty)" == "/dev/tty1" ]; then
  startx -- -nocursor
fi
```

This prevents X from starting when logging in via SSH.

### X Session Configuration (~/.xinitrc)
When X starts, it:
1. Disables screen blanking and power management
2. Rotates display 90 degrees to portrait mode (HDMI-1)
3. Hides mouse cursor after 5 seconds of inactivity
4. Launches Openbox window manager
5. Opens Chromium in kiosk mode pointing to Postarr at http://192.168.20.10:9876/

**Important**: Monitor is connected to HDMI-1. The xrandr rotation command uses `--output HDMI-1 --rotate right`.

## Monitor Power Control

### DDC/CI Setup
The Samsung monitor supports DDC/CI (Display Data Channel Command Interface) for remote control over HDMI.

**Requirements**:
- I2C must be enabled on the Pi: `sudo raspi-config` → Interface Options → I2C → Yes
- Or add `dtparam=i2c_arm=on` to `/boot/config.txt`
- Install ddcutil: `sudo apt-get install ddcutil`

**Monitor Details**:
- Bus: `/dev/i2c-20`
- VCP version: 2.0
- Supported power states (feature D6):
  - `01`: On
  - `04`: Off (DPM: Off, DPMS: Off)

### Power Control Scripts

**Turn monitor OFF**:
```bash
~/monitor-off.sh
```
Executes: `sudo ddcutil setvcp d6 04 --bus 20`

**Turn monitor ON**:
```bash
~/monitor-on.sh
```
Executes: `sudo ddcutil setvcp d6 01 --bus 20`

**Check power status**:
```bash
sudo ddcutil getvcp d6 --bus 20
```

**View all monitor capabilities**:
```bash
sudo ddcutil capabilities --bus 20
```

### Scheduling Automatic On/Off
To schedule automatic power control, use cron:

```bash
crontab -e
```

Example (off at 11 PM, on at 7 AM):
```
0 23 * * * /home/pi/monitor-off.sh
0 7 * * * /home/pi/monitor-on.sh
```

## Other Monitor Features (via DDC/CI)

The monitor supports these additional VCP features:
- **Brightness (feature 10)** - Implemented in HTTP server (see API endpoints above)
- Contrast (feature 12)
- Color presets (feature 14): 4000K, 5000K, Native, 8200K, 9300K, User 1
- Video gain (RGB): features 16, 18, 1A
- Sharpness (feature 87)
- Display modes (feature DC): Productivity, Mixed, Movie, User defined, Games, Sports

Example - set brightness directly via ddcutil:
```bash
sudo ddcutil setvcp 10 50 --bus 20
```

**Note**: Brightness is now controllable via the HTTP server web interface and API endpoints for easier integration with HomeKit and other automation systems.

## WiFi Stability

**Problem**: The Pi may become unreachable over WiFi after running for a while, stopping response to pings and disappearing from the network.

**Cause**: WiFi power management is enabled by default, causing the adapter to go into sleep mode and fail to wake up properly.

**Solution**: Run the WiFi stability fix script:

```bash
cd ~
./fix-wifi-stability.sh
sudo reboot
```

**What it does**:
1. Disables WiFi power management in NetworkManager
2. Creates a systemd service to run `iwconfig wlan0 power off` on every boot
3. Sets up a network watchdog that pings your gateway every 2 minutes
4. Automatically restarts WiFi interface if connection is lost

**Verify it's working**:
```bash
# Check power management is off
iwconfig wlan0 | grep -i power

# Should show: Power Management:off

# Check watchdog timer status
systemctl status wifi-watchdog.timer

# View watchdog logs
tail -f /var/log/wifi-watchdog.log
```

**Uninstall**:
```bash
cd ~
./uninstall-wifi-stability.sh
```

**Files**:
- `~/fix-wifi-stability.sh` - Installer script
- `~/uninstall-wifi-stability.sh` - Uninstaller script
- `/etc/NetworkManager/conf.d/wifi-powersave.conf` - NetworkManager config
- `/etc/systemd/system/wifi-powersave-off.service` - Power management disable service
- `/usr/local/bin/wifi-watchdog.sh` - Network watchdog script
- `/etc/systemd/system/wifi-watchdog.{service,timer}` - Watchdog timer
- `/var/log/wifi-watchdog.log` - Watchdog logs

## Troubleshooting

**Screen not rotating**:
- Check which HDMI port is in use: `DISPLAY=:0 xrandr`
- Update ~/.xinitrc with the correct output name (HDMI-1 or HDMI-2)
- Verify monitor is physically connected to the matching port

**Monitor power commands not working**:
- Verify I2C is enabled: `ls /dev/i2c*`
- Detect monitor: `sudo ddcutil detect`
- Check supported features: `sudo ddcutil capabilities --bus 20`

**Can't access Pi via SSH**:
- Verify network connection and IP address
- Check SSH is enabled: `sudo raspi-config` → Interface Options → SSH

## HomeKit Integration

The Pi can be controlled as a HomeKit accessory via a lightweight HTTP server that integrates with your existing Homebridge installation.

### HTTP Control Server

A Python Flask server runs on the Pi, exposing REST API endpoints that control the monitor via DDC/CI. Your Homebridge server calls these endpoints to turn the display on/off.

**Installation**:
```bash
cd ~
./install-monitor-http-server.sh
```

**How it works**:
- Runs a Flask HTTP server on port 5000
- Provides a web control interface at http://192.168.20.146:5000/
- Exposes REST API endpoints:
  - `GET /` - Web control interface
  - `GET /on` - Turns monitor on
  - `GET /off` - Turns monitor off
  - `GET /status` - Returns current power state (on/off)
  - `GET /brightness` - Returns current brightness level (0-100)
  - `GET /brightness/<value>` - Sets brightness to specified level (0-100)
  - `GET /watchdog` - Returns network watchdog status and restart count
  - `GET /watchdog/log` - Returns recent watchdog log entries (last 20)
  - `GET /health` - Health check
- Runs as a systemd service that starts automatically on boot

**Web Interface**:

Visit http://192.168.20.146:5000/ in any browser to access the "Posterr Screen" control panel. The interface includes:
- Device information and specifications
- Network Watchdog status showing:
  - Last network check status
  - Total WiFi restart count (green = 0, yellow = 1-4, red = 5+)
  - Recent log entries with color-coded events (green = OK, red = network down, orange = recovery)
- Real-time display status (ON/OFF)
- Brightness control with interactive slider (0-100%)
- Quick brightness presets (25%, 50%, 75%, 100%)
- Buttons to turn the display on/off
- Auto-refresh every 30 seconds
- Manual refresh button

**API Examples**:
```bash
# Turn monitor on
curl http://192.168.20.146:5000/on

# Turn monitor off
curl http://192.168.20.146:5000/off

# Get current status
curl http://192.168.20.146:5000/status

# Get current brightness
curl http://192.168.20.146:5000/brightness

# Set brightness to 75%
curl http://192.168.20.146:5000/brightness/75

# Get watchdog status
curl http://192.168.20.146:5000/watchdog

# Get recent watchdog log entries
curl http://192.168.20.146:5000/watchdog/log

# Health check
curl http://192.168.20.146:5000/health
```

**Service management**:
```bash
# View logs in real-time
sudo journalctl -u monitor-http-server.service -f

# Check service status
sudo systemctl status monitor-http-server.service

# Restart service
sudo systemctl restart monitor-http-server.service
```

**Uninstallation**:
```bash
cd ~
./uninstall-monitor-http-server.sh
```

### Homebridge Configuration

On your Homebridge server (192.168.20.10), install the HTTP lightbulb plugin:

```bash
npm install -g homebridge-http-lightbulb
```

Add this accessory to your `config.json`:

```json
{
  "accessory": "HTTP-LIGHTBULB",
  "name": "Posterr Display",
  "onUrl": "http://192.168.20.146:5000/on",
  "offUrl": "http://192.168.20.146:5000/off",
  "statusUrl": "http://192.168.20.146:5000/status",
  "statusPattern": "\"state\":\\s*\"on\"",
  "pullInterval": 10000,
  "brightness": {
    "statusUrl": "http://192.168.20.146:5000/brightness",
    "statusPattern": "\"brightness\":\\s*(\\d+)",
    "setUrl": "http://192.168.20.146:5000/brightness/%s",
    "pullInterval": 10000
  },
  "http_method": "GET"
}
```

**Configuration notes**:
- `pullInterval: 10000` - Polls power status every 10 seconds (10000ms) to sync changes made via web interface
- Brightness control is fully functional in HomeKit with a dimming slider
- **Limitation**: Brightness status polling is not supported by the plugin. Brightness changes made via the web interface won't automatically sync to HomeKit, but changes from HomeKit work perfectly
- Future enhancement: MQTT notifications can be added to push brightness updates to HomeKit in real-time

Restart Homebridge and the display will appear in HomeKit as a dimmable lightbulb.

**Files**:
- `~/monitor-http-server.py` - Flask HTTP server (Python 3)
- `~/monitor-http-server.service` - Systemd service definition
- `~/install-monitor-http-server.sh` - Installer
- `~/uninstall-monitor-http-server.sh` - Uninstaller
- `/etc/systemd/system/monitor-http-server.service` - Installed service

## Hardware Notes

The monitor's button controller board has exposed I2C pins (SDA/SCL at 3.3V), but DDC/CI over HDMI is the preferred control method as it requires no additional wiring.
