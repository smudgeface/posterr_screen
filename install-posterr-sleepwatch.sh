#!/bin/bash

# Installation script for Posterr Sleep Monitor with DDC/CI
# This replaces the CEC-based version with ddcutil for monitors that don't support CEC

set -e

echo "=========================================="
echo "Posterr Sleep Monitor Installation"
echo "DDC/CI version for non-CEC monitors"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please run this script as a normal user, not with sudo"
    exit 1
fi

# Verify ddcutil is installed
echo "Checking for ddcutil..."
if ! command -v ddcutil &> /dev/null; then
    echo "ddcutil not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y ddcutil
else
    echo "ddcutil is already installed"
fi

# Verify I2C is enabled
echo "Checking I2C devices..."
if ! ls /dev/i2c* &> /dev/null; then
    echo "Warning: No I2C devices found."
    echo "Please enable I2C with: sudo raspi-config → Interface Options → I2C"
    echo "Then reboot and run this installer again."
    exit 1
fi

# Copy script to home directory
echo "Installing posterr-sleepwatch.sh to /home/pi/..."
sudo cp posterr-sleepwatch.sh /home/pi/posterr-sleepwatch.sh
sudo chmod +x /home/pi/posterr-sleepwatch.sh
sudo chown pi:pi /home/pi/posterr-sleepwatch.sh

# Install systemd service
echo "Installing systemd service..."
sudo cp posterr-sleepwatch.service /etc/systemd/system/posterr-sleepwatch.service

# Configure sudo permissions for ddcutil (to avoid password prompts)
echo "Configuring sudo permissions for ddcutil..."
echo "pi ALL=(ALL) NOPASSWD: /usr/bin/ddcutil" | sudo tee /etc/sudoers.d/posterr-ddcutil > /dev/null
sudo chmod 0440 /etc/sudoers.d/posterr-ddcutil

# Reload systemd and enable service
echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable posterr-sleepwatch.service
sudo systemctl start posterr-sleepwatch.service

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Service status:"
sudo systemctl status posterr-sleepwatch.service --no-pager
echo ""
echo "Useful commands:"
echo "  View logs: sudo journalctl -u posterr-sleepwatch.service -f"
echo "  Stop service: sudo systemctl stop posterr-sleepwatch.service"
echo "  Start service: sudo systemctl start posterr-sleepwatch.service"
echo "  Disable service: sudo systemctl disable posterr-sleepwatch.service"
echo ""
