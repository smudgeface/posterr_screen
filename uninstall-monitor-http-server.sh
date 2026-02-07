#!/bin/bash

# Uninstallation script for Monitor HTTP Control Server

set -e

echo "=========================================="
echo "Monitor HTTP Server Uninstallation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please run this script as a normal user, not with sudo"
    exit 1
fi

# Stop and disable service
echo "Stopping and disabling service..."
sudo systemctl stop monitor-http-server.service 2>/dev/null || true
sudo systemctl disable monitor-http-server.service 2>/dev/null || true

# Remove systemd service file
echo "Removing systemd service..."
sudo rm -f /etc/systemd/system/monitor-http-server.service

# Reload systemd
sudo systemctl daemon-reload

# Remove script
echo "Removing server script..."
sudo rm -f /home/pi/monitor-http-server.py

echo ""
echo "=========================================="
echo "Uninstallation complete!"
echo "=========================================="
echo ""
echo "Note: Python3 and Flask were left installed."
echo "The manual monitor control scripts (monitor-on.sh, monitor-off.sh) were not removed."
echo ""
echo "Don't forget to remove the accessory from your Homebridge config.json"
echo ""
