#!/bin/bash

# Installation script for Monitor HTTP Control Server

set -e

echo "=========================================="
echo "Monitor HTTP Server Installation"
echo "HomeKit Integration via Homebridge"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Error: Please run this script as a normal user, not with sudo"
    exit 1
fi

# Install Python3 and Flask
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-flask

# Copy server script to home directory
echo "Installing monitor-http-server.py to /home/pi/..."
sudo cp monitor-http-server.py /home/pi/monitor-http-server.py
sudo chmod +x /home/pi/monitor-http-server.py
sudo chown pi:pi /home/pi/monitor-http-server.py

# Install systemd service
echo "Installing systemd service..."
sudo cp monitor-http-server.service /etc/systemd/system/monitor-http-server.service

# Reload systemd and enable service
echo "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable monitor-http-server.service
sudo systemctl start monitor-http-server.service

# Wait a moment for service to start
sleep 2

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Service status:"
sudo systemctl status monitor-http-server.service --no-pager
echo ""
echo "Testing HTTP endpoints..."
echo ""

# Test the health endpoint
echo "Health check:"
curl -s http://localhost:5000/health | python3 -m json.tool || echo "Failed to connect"
echo ""

echo "Current monitor status:"
curl -s http://localhost:5000/status | python3 -m json.tool || echo "Failed to get status"
echo ""

echo "=========================================="
echo "Setup Information for Homebridge"
echo "=========================================="
echo ""
echo "Add this to your Homebridge config.json accessories array:"
echo ""
cat <<'EOF'
{
  "accessory": "HTTP-SWITCH",
  "name": "Pi Display",
  "switchType": "stateful",
  "onUrl": "http://192.168.20.146:5000/on",
  "offUrl": "http://192.168.20.146:5000/off",
  "statusUrl": "http://192.168.20.146:5000/status",
  "statusPattern": "\"state\":\\s*\"on\""
}
EOF
echo ""
echo "Then install homebridge-http-switch on your Homebridge server:"
echo "  npm install -g homebridge-http-switch"
echo ""
echo "Useful commands:"
echo "  View logs: sudo journalctl -u monitor-http-server.service -f"
echo "  Stop service: sudo systemctl stop monitor-http-server.service"
echo "  Start service: sudo systemctl start monitor-http-server.service"
echo "  Restart service: sudo systemctl restart monitor-http-server.service"
echo ""
echo "Test endpoints:"
echo "  curl http://192.168.20.146:5000/status"
echo "  curl http://192.168.20.146:5000/on"
echo "  curl http://192.168.20.146:5000/off"
echo ""
