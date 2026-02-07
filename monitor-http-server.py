#!/usr/bin/env python3

"""
Lightweight HTTP server for controlling Samsung monitor via DDC/CI
Exposes REST API endpoints for HomeKit integration via Homebridge
"""

from flask import Flask, jsonify, render_template_string
import subprocess
import re
import os
import time
from datetime import datetime

app = Flask(__name__)

# Configuration
DDC_BUS = "20"
DDC_FEATURE_POWER = "d6"
DDC_FEATURE_BRIGHTNESS = "10"
MONITOR_ON_SCRIPT = "/home/pi/monitor-on.sh"
MONITOR_OFF_SCRIPT = "/home/pi/monitor-off.sh"
WATCHDOG_LOG = "/var/log/wifi-watchdog.log"

# HTML template for web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Posterr Screen Control</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 100%;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1em;
        }

        .device-info {
            background: #f5f5f5;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }

        .device-info h2 {
            color: #555;
            font-size: 1.2em;
            margin-bottom: 10px;
        }

        .device-info p {
            color: #777;
            line-height: 1.6;
        }

        .status-section {
            margin-bottom: 30px;
        }

        .status-label {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .status-display {
            font-size: 2em;
            font-weight: bold;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            transition: all 0.3s ease;
        }

        .status-display.on {
            background: #4caf50;
            color: white;
        }

        .status-display.off {
            background: #666;
            color: white;
        }

        .status-display.loading {
            background: #ff9800;
            color: white;
        }

        .status-display.error {
            background: #f44336;
            color: white;
        }

        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }

        button {
            padding: 15px 30px;
            font-size: 1.1em;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }

        button:active {
            transform: translateY(0);
        }

        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-on {
            background: #4caf50;
            color: white;
        }

        .btn-on:hover {
            background: #45a049;
        }

        .btn-off {
            background: #666;
            color: white;
        }

        .btn-off:hover {
            background: #555;
        }

        .btn-refresh {
            background: #2196f3;
            color: white;
            grid-column: 1 / -1;
        }

        .btn-refresh:hover {
            background: #1976d2;
        }

        .last-updated {
            text-align: center;
            color: #999;
            font-size: 0.85em;
            margin-top: 20px;
        }

        .spec-list {
            list-style: none;
            margin-top: 10px;
        }

        .spec-list li {
            padding: 5px 0;
            color: #777;
            font-size: 0.95em;
        }

        .spec-list li strong {
            color: #555;
        }

        .api-reference {
            background: #f5f5f5;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }

        .api-reference h2 {
            color: #555;
            font-size: 1.2em;
            margin-bottom: 15px;
        }

        .api-endpoint {
            background: white;
            border-left: 3px solid #667eea;
            padding: 10px 15px;
            margin-bottom: 10px;
            border-radius: 5px;
        }

        .api-endpoint:last-child {
            margin-bottom: 0;
        }

        .api-method {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.75em;
            font-weight: bold;
            margin-right: 8px;
        }

        .api-path {
            font-family: 'Courier New', monospace;
            color: #333;
            font-weight: 600;
        }

        .api-description {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }

        .api-toggle {
            background: #e0e0e0;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9em;
            color: #555;
            margin-bottom: 15px;
            transition: background 0.2s;
        }

        .api-toggle:hover {
            background: #d0d0d0;
        }

        .api-content {
            display: none;
        }

        .api-content.show {
            display: block;
        }

        .brightness-section {
            margin-bottom: 30px;
        }

        .brightness-value {
            font-size: 2em;
            font-weight: bold;
            text-align: center;
            margin-bottom: 15px;
            color: #667eea;
        }

        .slider-container {
            position: relative;
            margin-bottom: 10px;
        }

        .brightness-slider {
            width: 100%;
            height: 8px;
            border-radius: 5px;
            background: #e0e0e0;
            outline: none;
            -webkit-appearance: none;
            appearance: none;
        }

        .brightness-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .brightness-slider::-webkit-slider-thumb:hover {
            background: #5568d3;
            transform: scale(1.1);
        }

        .brightness-slider::-moz-range-thumb {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: #667eea;
            cursor: pointer;
            border: none;
            transition: all 0.2s ease;
        }

        .brightness-slider::-moz-range-thumb:hover {
            background: #5568d3;
            transform: scale(1.1);
        }

        .brightness-slider:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .brightness-labels {
            display: flex;
            justify-content: space-between;
            font-size: 0.85em;
            color: #999;
            margin-top: 5px;
        }

        .preset-buttons {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 15px;
        }

        .btn-preset {
            background: #f5f5f5;
            color: #555;
            padding: 10px;
            font-size: 0.9em;
            border: 2px solid transparent;
            transition: all 0.2s ease;
        }

        .btn-preset:hover {
            background: #e0e0e0;
            border-color: #667eea;
        }

        .watchdog-section {
            background: #f5f5f5;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
        }

        .watchdog-section h2 {
            color: #555;
            font-size: 1.2em;
            margin-bottom: 15px;
        }

        .watchdog-status {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 15px;
            background: white;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .watchdog-status.healthy {
            border-left: 4px solid #4caf50;
        }

        .watchdog-status.issues {
            border-left: 4px solid #ff9800;
        }

        .watchdog-status.error {
            border-left: 4px solid #f44336;
        }

        .watchdog-label {
            font-weight: 600;
            color: #555;
        }

        .watchdog-value {
            color: #777;
            font-size: 0.95em;
        }

        .watchdog-log {
            background: white;
            border-radius: 8px;
            padding: 15px;
            max-height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.85em;
        }

        .log-entry {
            padding: 5px 0;
            border-bottom: 1px solid #f0f0f0;
        }

        .log-entry:last-child {
            border-bottom: none;
        }

        .log-entry.ok {
            color: #4caf50;
        }

        .log-entry.down {
            color: #f44336;
            font-weight: bold;
        }

        .log-entry.recovery {
            color: #ff9800;
        }

        .log-timestamp {
            color: #999;
            margin-right: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Posterr Screen</h1>
        <p class="subtitle">DDC/CI Monitor Control</p>

        <div class="device-info">
            <h2>Device Information</h2>
            <p>Samsung S24B300 display in custom frame, running Posterr kiosk interface. Monitor power control via DDC/CI over HDMI.</p>
            <ul class="spec-list">
                <li><strong>Display:</strong> Samsung S24B300 (2013)</li>
                <li><strong>Orientation:</strong> Portrait (90° rotation)</li>
                <li><strong>Control:</strong> DDC/CI Bus 20, Feature D6</li>
                <li><strong>Backend:</strong> http://192.168.20.10:9876</li>
            </ul>
        </div>

        <div class="api-reference">
            <h2>API Reference</h2>
            <button class="api-toggle" onclick="toggleAPI()">Show API Endpoints</button>
            <div class="api-content" id="api-content">
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/on</span>
                    </div>
                    <div class="api-description">Turn the monitor on</div>
                </div>
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/off</span>
                    </div>
                    <div class="api-description">Turn the monitor off</div>
                </div>
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/status</span>
                    </div>
                    <div class="api-description">Get current power state (returns JSON)</div>
                </div>
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/health</span>
                    </div>
                    <div class="api-description">Health check endpoint</div>
                </div>
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/brightness</span>
                    </div>
                    <div class="api-description">Get current brightness level (0-100)</div>
                </div>
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/brightness/&lt;value&gt;</span>
                    </div>
                    <div class="api-description">Set brightness to specific level (0-100)</div>
                </div>
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/watchdog</span>
                    </div>
                    <div class="api-description">Get network watchdog status and restart count</div>
                </div>
                <div class="api-endpoint">
                    <div>
                        <span class="api-method">GET</span>
                        <span class="api-path">/watchdog/log</span>
                    </div>
                    <div class="api-description">Get recent watchdog log entries (last 20)</div>
                </div>
            </div>
        </div>

        <div class="watchdog-section">
            <h2>Network Watchdog</h2>
            <div id="watchdog-status" class="watchdog-status healthy">
                <div>
                    <div class="watchdog-label">Status</div>
                    <div class="watchdog-value" id="watchdog-status-text">Loading...</div>
                </div>
                <div style="text-align: right;">
                    <div class="watchdog-label">Restarts</div>
                    <div class="watchdog-value" id="watchdog-restarts">--</div>
                </div>
            </div>
            <button class="api-toggle" onclick="toggleWatchdogLog()">Show Recent Log</button>
            <div class="watchdog-log" id="watchdog-log" style="display: none; margin-top: 15px;">
                <div id="watchdog-log-content">Loading...</div>
            </div>
        </div>

        <div class="status-section">
            <div class="status-label">Display Status</div>
            <div id="status" class="status-display loading">Loading...</div>
        </div>

        <div class="brightness-section">
            <div class="status-label">Brightness</div>
            <div class="brightness-value" id="brightness-value">--</div>
            <div class="slider-container">
                <input type="range" min="0" max="100" value="50" class="brightness-slider" id="brightness-slider">
            </div>
            <div class="brightness-labels">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
            </div>
            <div class="preset-buttons">
                <button class="btn-preset" onclick="setBrightnessPreset(25)">25%</button>
                <button class="btn-preset" onclick="setBrightnessPreset(50)">50%</button>
                <button class="btn-preset" onclick="setBrightnessPreset(75)">75%</button>
                <button class="btn-preset" onclick="setBrightnessPreset(100)">100%</button>
            </div>
        </div>

        <div class="controls">
            <button id="btn-on" class="btn-on" onclick="turnOn()">Turn On</button>
            <button id="btn-off" class="btn-off" onclick="turnOff()">Turn Off</button>
            <button id="btn-refresh" class="btn-refresh" onclick="refreshStatus()">Refresh Status</button>
        </div>

        <div class="last-updated" id="last-updated">Never updated</div>
    </div>

    <script>
        let isLoading = false;
        let brightnessTimeout = null;
        let watchdogLogVisible = false;

        function toggleAPI() {
            const content = document.getElementById('api-content');
            const button = document.querySelector('.api-toggle');
            content.classList.toggle('show');

            if (content.classList.contains('show')) {
                button.textContent = 'Hide API Endpoints';
            } else {
                button.textContent = 'Show API Endpoints';
            }
        }

        function toggleWatchdogLog() {
            const logDiv = document.getElementById('watchdog-log');
            const button = event.target;

            watchdogLogVisible = !watchdogLogVisible;

            if (watchdogLogVisible) {
                logDiv.style.display = 'block';
                button.textContent = 'Hide Recent Log';
                refreshWatchdogLog();
            } else {
                logDiv.style.display = 'none';
                button.textContent = 'Show Recent Log';
            }
        }

        async function refreshWatchdog() {
            try {
                const response = await fetch('/watchdog');
                const data = await response.json();

                if (data.status === 'success') {
                    const statusDiv = document.getElementById('watchdog-status');
                    const statusText = document.getElementById('watchdog-status-text');
                    const restarts = document.getElementById('watchdog-restarts');

                    // Update status
                    statusText.textContent = data.last_check || 'Never';
                    restarts.textContent = data.restart_count;

                    // Update styling based on restart count
                    statusDiv.className = 'watchdog-status';
                    if (data.restart_count === 0) {
                        statusDiv.classList.add('healthy');
                    } else if (data.restart_count < 5) {
                        statusDiv.classList.add('issues');
                    } else {
                        statusDiv.classList.add('error');
                    }
                }
            } catch (error) {
                console.error('Failed to get watchdog status:', error);
            }
        }

        async function refreshWatchdogLog() {
            try {
                const response = await fetch('/watchdog/log');
                const data = await response.json();

                if (data.status === 'success') {
                    const logContent = document.getElementById('watchdog-log-content');

                    if (data.entries.length === 0) {
                        logContent.innerHTML = '<div class="log-entry">No log entries yet</div>';
                    } else {
                        logContent.innerHTML = data.entries.map(entry => {
                            let className = 'log-entry';
                            if (entry.includes('Network down')) {
                                className += ' down';
                            } else if (entry.includes('Recovery')) {
                                className += ' recovery';
                            } else if (entry.includes('Network OK')) {
                                className += ' ok';
                            }
                            return `<div class="${className}">${entry}</div>`;
                        }).join('');
                    }
                }
            } catch (error) {
                console.error('Failed to get watchdog log:', error);
            }
        }

        function setStatus(state, text) {
            const statusDiv = document.getElementById('status');
            statusDiv.className = 'status-display ' + state;
            statusDiv.textContent = text;
        }

        function setLoading(loading) {
            isLoading = loading;
            const buttons = document.querySelectorAll('button');
            buttons.forEach(btn => btn.disabled = loading);
        }

        function updateLastUpdated() {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            document.getElementById('last-updated').textContent = 'Last updated: ' + timeString;
        }

        async function refreshStatus() {
            if (isLoading) return;

            setLoading(true);
            setStatus('loading', 'Checking...');

            try {
                const response = await fetch('/status');
                const data = await response.json();

                if (data.status === 'success') {
                    const state = data.state;
                    setStatus(state, state === 'on' ? 'ON' : 'OFF');
                    updateLastUpdated();
                } else {
                    setStatus('error', 'Error: ' + data.message);
                }
            } catch (error) {
                setStatus('error', 'Connection Error');
            } finally {
                setLoading(false);
            }

            // Also refresh brightness and watchdog
            await refreshBrightness();
            await refreshWatchdog();
        }

        async function refreshBrightness() {
            try {
                const response = await fetch('/brightness');
                const data = await response.json();

                if (data.status === 'success') {
                    updateBrightnessDisplay(data.brightness);
                }
            } catch (error) {
                console.error('Failed to get brightness:', error);
            }
        }

        function updateBrightnessDisplay(value) {
            document.getElementById('brightness-value').textContent = value + '%';
            document.getElementById('brightness-slider').value = value;
        }

        async function setBrightness(value) {
            try {
                const response = await fetch('/brightness/' + value);
                const data = await response.json();

                if (data.status === 'success') {
                    updateBrightnessDisplay(data.brightness);
                } else {
                    console.error('Failed to set brightness:', data.message);
                }
            } catch (error) {
                console.error('Connection error:', error);
            }
        }

        function setBrightnessPreset(value) {
            if (isLoading) return;
            updateBrightnessDisplay(value);
            setBrightness(value);
        }

        // Add slider event listener
        document.getElementById('brightness-slider').addEventListener('input', function(e) {
            const value = e.target.value;
            document.getElementById('brightness-value').textContent = value + '%';

            // Debounce the actual brightness change
            clearTimeout(brightnessTimeout);
            brightnessTimeout = setTimeout(() => {
                setBrightness(value);
            }, 500);
        });

        async function turnOn() {
            if (isLoading) return;

            setLoading(true);
            setStatus('loading', 'Turning On...');

            try {
                const response = await fetch('/on');
                const data = await response.json();

                if (data.status === 'success') {
                    setStatus('on', 'ON');
                    updateLastUpdated();
                } else {
                    setStatus('error', 'Error: ' + data.message);
                }
            } catch (error) {
                setStatus('error', 'Connection Error');
            } finally {
                setLoading(false);
            }
        }

        async function turnOff() {
            if (isLoading) return;

            setLoading(true);
            setStatus('loading', 'Turning Off...');

            try {
                const response = await fetch('/off');
                const data = await response.json();

                if (data.status === 'success') {
                    setStatus('off', 'OFF');
                    updateLastUpdated();
                } else {
                    setStatus('error', 'Error: ' + data.message);
                }
            } catch (error) {
                setStatus('error', 'Connection Error');
            } finally {
                setLoading(false);
            }
        }

        // Refresh status on page load
        refreshStatus();

        // Auto-refresh every 30 seconds
        setInterval(refreshStatus, 30000);
    </script>
</body>
</html>
"""


def run_command(command):
    """Execute a shell command and return success status"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def get_monitor_status():
    """Query the monitor's current power state via ddcutil"""
    success, stdout, stderr = run_command(
        f"sudo ddcutil getvcp {DDC_FEATURE_POWER} --bus {DDC_BUS}"
    )

    if not success:
        return None, f"Failed to query monitor: {stderr}"

    # Parse output looking for "DPM: On" or "DPM: Off"
    # Example: "VCP code 0xd6 (Power mode): DPM: On,  DPMS: Off (sl=0x01)"
    match = re.search(r'DPM:\s*(On|Off)', stdout)
    if match:
        state = match.group(1)
        return state == "On", None

    return None, "Could not parse monitor status"


def get_brightness():
    """Query the monitor's current brightness level via ddcutil"""
    success, stdout, stderr = run_command(
        f"sudo ddcutil getvcp {DDC_FEATURE_BRIGHTNESS} --bus {DDC_BUS}"
    )

    if not success:
        return None, f"Failed to query brightness: {stderr}"

    # Parse output looking for current value
    # Example: "VCP code 0x10 (Brightness                    ): current value =   100, max value =   100"
    match = re.search(r'current value\s*=\s*(\d+)', stdout)
    if match:
        return int(match.group(1)), None

    return None, "Could not parse brightness value"


def set_brightness(value):
    """Set the monitor's brightness level via ddcutil"""
    # Validate brightness value (0-100)
    try:
        brightness = int(value)
        if brightness < 0 or brightness > 100:
            return False, "Brightness must be between 0 and 100"
    except ValueError:
        return False, "Invalid brightness value"

    success, stdout, stderr = run_command(
        f"sudo ddcutil setvcp {DDC_FEATURE_BRIGHTNESS} {brightness} --bus {DDC_BUS}"
    )

    if success:
        return True, None
    else:
        return False, f"Failed to set brightness: {stderr}"


def get_watchdog_status():
    """Get network watchdog status from log file"""
    if not os.path.exists(WATCHDOG_LOG):
        return {
            "last_check": "Log file not found",
            "restart_count": 0
        }

    try:
        with open(WATCHDOG_LOG, 'r') as f:
            lines = f.readlines()

        if not lines:
            return {
                "last_check": "No entries yet",
                "restart_count": 0
            }

        # Count restart events (lines containing "Network down")
        restart_count = sum(1 for line in lines if "Network down" in line)

        # Get the last line (most recent entry)
        last_line = lines[-1].strip()

        # Extract just the message part (remove timestamp)
        # Format: "Day Month DD HH:MM:SS TZ YYYY: message"
        if ": " in last_line:
            parts = last_line.split(": ", 1)
            if len(parts) == 2:
                last_check = parts[1]
            else:
                last_check = last_line
        else:
            last_check = last_line

        return {
            "last_check": last_check,
            "restart_count": restart_count
        }
    except Exception as e:
        return {
            "last_check": f"Error reading log: {str(e)}",
            "restart_count": 0
        }


def get_watchdog_log(num_lines=20):
    """Get recent watchdog log entries"""
    if not os.path.exists(WATCHDOG_LOG):
        return []

    try:
        with open(WATCHDOG_LOG, 'r') as f:
            lines = f.readlines()

        # Return last N lines, reversed (most recent first)
        recent_lines = lines[-num_lines:] if len(lines) > num_lines else lines
        return [line.strip() for line in reversed(recent_lines)]
    except Exception as e:
        return [f"Error reading log: {str(e)}"]


@app.route('/', methods=['GET'])
def index():
    """Serve the web control interface"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/on', methods=['GET'])
def turn_on():
    """Turn the monitor on"""
    success, stdout, stderr = run_command(MONITOR_ON_SCRIPT)

    if success:
        return jsonify({
            "status": "success",
            "message": "Monitor turned on",
            "state": "on"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": f"Failed to turn on monitor: {stderr}"
        }), 500


@app.route('/off', methods=['GET'])
def turn_off():
    """Turn the monitor off"""
    success, stdout, stderr = run_command(MONITOR_OFF_SCRIPT)

    if success:
        return jsonify({
            "status": "success",
            "message": "Monitor turned off",
            "state": "off"
        }), 200
    else:
        return jsonify({
            "status": "error",
            "message": f"Failed to turn off monitor: {stderr}"
        }), 500


@app.route('/status', methods=['GET'])
def status():
    """Get the current monitor power state"""
    is_on, error = get_monitor_status()

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 500

    return jsonify({
        "status": "success",
        "state": "on" if is_on else "off",
        "is_on": is_on
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "monitor-http-server"
    }), 200


@app.route('/brightness', methods=['GET'])
def get_brightness_endpoint():
    """Get the current monitor brightness level"""
    brightness, error = get_brightness()

    if error:
        return jsonify({
            "status": "error",
            "message": error
        }), 500

    return jsonify({
        "status": "success",
        "brightness": brightness
    }), 200


@app.route('/brightness/<int:value>', methods=['GET'])
def set_brightness_endpoint(value):
    """Set the monitor brightness level (0-100)"""
    # Check if we're waking from sleep (brightness 0 -> non-zero)
    if value > 0:
        current_brightness, _ = get_brightness()

        # If display is off (brightness 0), turn it on first and wait for it to wake
        if current_brightness == 0:
            # Turn on the display first
            run_command(MONITOR_ON_SCRIPT)

            # Wait for display to fully wake up before setting brightness
            # Adjust this delay if needed - testing to find minimum stable delay
            time.sleep(5.0)

    # Now set the desired brightness
    success, error = set_brightness(value)

    if not success:
        return jsonify({
            "status": "error",
            "message": error
        }), 400

    # Get the new brightness value to confirm
    brightness, get_error = get_brightness()

    return jsonify({
        "status": "success",
        "message": f"Brightness set to {value}",
        "brightness": brightness if not get_error else value
    }), 200


@app.route('/watchdog', methods=['GET'])
def watchdog_status():
    """Get network watchdog status"""
    status_data = get_watchdog_status()

    return jsonify({
        "status": "success",
        "last_check": status_data["last_check"],
        "restart_count": status_data["restart_count"]
    }), 200


@app.route('/watchdog/log', methods=['GET'])
def watchdog_log():
    """Get recent watchdog log entries"""
    log_entries = get_watchdog_log(num_lines=20)

    return jsonify({
        "status": "success",
        "entries": log_entries
    }), 200


if __name__ == '__main__':
    # Listen on all interfaces, port 5000
    # debug=False for production use
    app.run(host='0.0.0.0', port=5000, debug=False)
