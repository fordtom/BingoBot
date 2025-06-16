#!/bin/bash
"""
Setup script for Raspberry Pi voltage monitoring.

This script:
1. Copies the voltage monitoring script to the Pi
2. Makes it executable
3. Sets up the cron job to run every 5 minutes
4. Creates the database directory if needed
"""

# Configuration
SCRIPT_DIR="/home/pi/bingobot-monitoring"
SCRIPT_NAME="voltage_monitor.py"

echo "Setting up Raspberry Pi voltage monitoring..."

# Create script directory
echo "Creating script directory: $SCRIPT_DIR"
mkdir -p "$SCRIPT_DIR"

# Copy the monitoring script
echo "Copying voltage monitoring script..."
cp "$(dirname "$0")/voltage_monitor.py" "$SCRIPT_DIR/$SCRIPT_NAME"
chmod +x "$SCRIPT_DIR/$SCRIPT_NAME"

# Create database directory (local to bot project)
echo "Creating local database directory..."
mkdir -p "./database"

# Test the script
echo "Testing voltage monitoring script..."
cd "$SCRIPT_DIR"
python3 "$SCRIPT_NAME"

if [ $? -eq 0 ]; then
    echo "✅ Script test successful"
else
    echo "❌ Script test failed"
    exit 1
fi

# Set up cron job
echo "Setting up cron job..."
CRON_ENTRY="*/5 * * * * cd $SCRIPT_DIR && /usr/bin/python3 $SCRIPT_NAME >> /var/log/voltage_monitor.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_DIR/$SCRIPT_NAME"; then
    echo "Cron job already exists"
else
    # Add the cron job
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    echo "✅ Cron job added: runs every 5 minutes"
fi

echo "Setup complete!"
echo ""
echo "The monitoring script will:"
echo "- Run every 5 minutes via cron"
echo "- Check for voltage warnings in dmesg"
echo "- Create/remove flag file: ./database/undervoltage"
echo "- Log output to: /var/log/voltage_monitor.log"
echo "- Send simple Discord message 'i am undervolting :(' when flag exists"
echo ""
echo "You can manually run the script with:"
echo "  cd $SCRIPT_DIR && python3 $SCRIPT_NAME"
echo ""
echo "View the cron job with:"
echo "  crontab -l"
echo ""
echo "Check logs with:"
echo "  tail -f /var/log/voltage_monitor.log" 