#!/bin/bash
# WiFi Stability Fix for Raspberry Pi
# Disables power management and adds network watchdog

echo "=== Raspberry Pi WiFi Stability Fix ==="
echo ""

# 1. Disable WiFi power management
echo "[1/4] Disabling WiFi power management..."
sudo tee /etc/NetworkManager/conf.d/wifi-powersave.conf > /dev/null <<EOF
[connection]
wifi.powersave = 2
EOF

# 2. Add permanent iwconfig power management disable
echo "[2/4] Creating WiFi power management disable service..."
sudo tee /etc/systemd/system/wifi-powersave-off.service > /dev/null <<EOF
[Unit]
Description=Disable WiFi Power Management
After=network.target

[Service]
Type=oneshot
ExecStart=/sbin/iwconfig wlan0 power off
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable wifi-powersave-off.service
sudo systemctl start wifi-powersave-off.service

# 3. Create network watchdog script (optional fallback)
echo "[3/4] Creating network watchdog..."
sudo tee /usr/local/bin/wifi-watchdog.sh > /dev/null <<'EOF'
#!/bin/bash
# Network watchdog - restarts WiFi if connection is lost

# Dynamically get default gateway
PING_TARGET=$(ip route | grep default | awk '{print $3}' | head -n1)
LOG_FILE="/var/log/wifi-watchdog.log"

# If no gateway found, exit
if [ -z "$PING_TARGET" ]; then
    echo "$(date): No default gateway found, skipping check" >> "$LOG_FILE"
    exit 0
fi

if ! ping -c 3 -W 5 "$PING_TARGET" > /dev/null 2>&1; then
    echo "$(date): Network down (gateway: $PING_TARGET), restarting WiFi interface" >> "$LOG_FILE"

    # Log current WiFi status
    iwconfig wlan0 >> "$LOG_FILE" 2>&1

    # Restart WiFi
    sudo ip link set wlan0 down
    sleep 2
    sudo ip link set wlan0 up
    sleep 5

    # If still down, restart networking service
    if ! ping -c 3 -W 5 "$PING_TARGET" > /dev/null 2>&1; then
        echo "$(date): Interface restart failed, restarting networking" >> "$LOG_FILE"
        sudo systemctl restart NetworkManager
        sleep 10
    fi

    echo "$(date): Recovery attempt complete" >> "$LOG_FILE"
else
    # Log successful check every hour (keep log from growing too large)
    if [ $(date +%M) -eq 0 ]; then
        echo "$(date): Network OK (gateway: $PING_TARGET)" >> "$LOG_FILE"
    fi
fi
EOF

sudo chmod +x /usr/local/bin/wifi-watchdog.sh

# 4. Create systemd timer for watchdog (runs every 2 minutes)
echo "[4/4] Setting up watchdog timer..."
sudo tee /etc/systemd/system/wifi-watchdog.service > /dev/null <<EOF
[Unit]
Description=WiFi Watchdog Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/wifi-watchdog.sh
EOF

sudo tee /etc/systemd/system/wifi-watchdog.timer > /dev/null <<EOF
[Unit]
Description=Run WiFi Watchdog every 2 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=2min

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable wifi-watchdog.timer
sudo systemctl start wifi-watchdog.timer

echo ""
echo "=== Installation Complete ==="
echo ""
echo "What was done:"
echo "1. WiFi power management disabled in NetworkManager"
echo "2. Created systemd service to disable iwconfig power management on boot"
echo "3. Created network watchdog that checks connectivity every 2 minutes"
echo "4. Watchdog will auto-restart WiFi interface if connection is lost"
echo ""
echo "Logs:"
echo "- Watchdog logs: tail -f /var/log/wifi-watchdog.log"
echo "- Timer status: systemctl status wifi-watchdog.timer"
echo ""
echo "Current WiFi status:"
iwconfig wlan0 2>&1 | grep -i power
echo ""
echo "RECOMMENDATION: Reboot the Pi now to ensure all changes take effect"
echo "  sudo reboot"
