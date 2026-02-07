#!/bin/bash
# Uninstall WiFi Stability Fix

echo "=== Uninstalling WiFi Stability Fix ==="
echo ""

# Stop and disable services
echo "[1/4] Stopping and disabling services..."
sudo systemctl stop wifi-watchdog.timer 2>/dev/null
sudo systemctl disable wifi-watchdog.timer 2>/dev/null
sudo systemctl stop wifi-powersave-off.service 2>/dev/null
sudo systemctl disable wifi-powersave-off.service 2>/dev/null

# Remove systemd files
echo "[2/4] Removing systemd service files..."
sudo rm -f /etc/systemd/system/wifi-watchdog.service
sudo rm -f /etc/systemd/system/wifi-watchdog.timer
sudo rm -f /etc/systemd/system/wifi-powersave-off.service
sudo systemctl daemon-reload

# Remove watchdog script
echo "[3/4] Removing watchdog script..."
sudo rm -f /usr/local/bin/wifi-watchdog.sh

# Remove NetworkManager config
echo "[4/4] Removing NetworkManager power save config..."
sudo rm -f /etc/NetworkManager/conf.d/wifi-powersave.conf

echo ""
echo "=== Uninstallation Complete ==="
echo ""
echo "Note: WiFi power management will revert to default (on) after reboot."
echo "To re-enable power management immediately, run:"
echo "  sudo iwconfig wlan0 power on"
echo ""
echo "Watchdog log file remains at: /var/log/wifi-watchdog.log"
echo "To remove it: sudo rm /var/log/wifi-watchdog.log"
