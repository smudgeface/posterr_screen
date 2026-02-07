#!/bin/bash

# Uninstallation script for Posterr Sleep Monitor with DDC/CI

set -e

echo "=========================================="
echo "Posterr Sleep Monitor Uninstallation"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please run this script as a normal user, not with sudo"
    exit 1
fi

# Stop and disable service
echo "Stopping and disabling service..."
sudo systemctl stop posterr-sleepwatch.service 2>/dev/null || true
sudo systemctl disable posterr-sleepwatch.service 2>/dev/null || true

# Remove systemd service file
echo "Removing systemd service..."
sudo rm -f /etc/systemd/system/posterr-sleepwatch.service

# Reload systemd
sudo systemctl daemon-reload

# Remove script
echo "Removing script..."
sudo rm -f /home/pi/posterr-sleepwatch.sh

# Remove sudo permissions
echo "Removing sudo permissions..."
sudo rm -f /etc/sudoers.d/posterr-ddcutil

echo ""
echo "=========================================="
echo "Uninstallation complete!"
echo "=========================================="
echo ""
echo "Note: ddcutil and I2C settings were left unchanged."
echo "The manual monitor control scripts (monitor-on.sh, monitor-off.sh) were not removed."
echo ""
