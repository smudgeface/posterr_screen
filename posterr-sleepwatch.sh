#!/bin/bash

# Posterr Sleep Monitor with DDC/CI Display Control
# Modified to use ddcutil instead of CEC for Samsung S24B300 monitor

# Configuration
POSTERR_URL="http://192.168.20.10:9876"
POLL_FREQUENCY=5  # seconds between API checks
DDC_BUS=20        # I2C bus for the monitor
DDC_FEATURE="d6"  # VCP feature code for power mode
DDC_ON="01"       # Value to turn monitor on
DDC_OFF="04"      # Value to turn monitor off (standby)

# Check if ddcutil is installed
if ! command -v ddcutil &> /dev/null; then
    echo "Error: ddcutil is not installed. Please install it with: sudo apt-get install ddcutil"
    exit 1
fi

# Verify I2C devices exist
if [ ! -e "/dev/i2c-${DDC_BUS}" ]; then
    echo "Error: /dev/i2c-${DDC_BUS} not found. Ensure I2C is enabled in raspi-config"
    exit 1
fi

echo "Posterr sleep monitor started"
echo "Monitoring: ${POSTERR_URL}/api/sleep"
echo "Using DDC/CI on bus ${DDC_BUS}"

# Track previous state to avoid redundant commands
previous_state=""

# Main monitoring loop
while true; do
    # Query Posterr API for sleep state
    output=$(curl -s "${POSTERR_URL}/api/sleep" 2>/dev/null)

    # Check if curl succeeded
    if [ $? -ne 0 ]; then
        echo "Warning: Failed to connect to Posterr API at ${POSTERR_URL}"
        sleep ${POLL_FREQUENCY}
        continue
    fi

    # Parse the sleep state (expects "true" or "false")
    if [ "$output" = "true" ]; then
        if [ "$previous_state" != "off" ]; then
            echo "$(date): Sleep mode active - turning monitor OFF"
            sudo ddcutil setvcp ${DDC_FEATURE} ${DDC_OFF} --bus ${DDC_BUS} 2>/dev/null
            previous_state="off"
        fi
    elif [ "$output" = "false" ]; then
        if [ "$previous_state" != "on" ]; then
            echo "$(date): Sleep mode inactive - turning monitor ON"
            sudo ddcutil setvcp ${DDC_FEATURE} ${DDC_ON} --bus ${DDC_BUS} 2>/dev/null
            previous_state="on"
        fi
    else
        echo "Warning: Unexpected API response: $output"
    fi

    # Wait before next poll
    sleep ${POLL_FREQUENCY}
done
