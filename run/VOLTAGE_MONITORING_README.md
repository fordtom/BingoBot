# Raspberry Pi Voltage Monitoring Setup

This system monitors your Raspberry Pi for under-voltage warnings and automatically sends a simple message to Discord when detected.

## How It Works

1. **Host-side script** (`run/voltage_monitor.py`) runs on your Pi every 5 minutes via cron
2. **Checks dmesg** for voltage warnings 
3. **Creates/removes flag file** `./database/undervoltage` based on detection
4. **Discord bot** checks for this file every 5 minutes
5. **Sends message** "i am undervolting :(" to #general when file exists

Super simple - just file existence, no JSON, no database tracking!

## Setup Instructions

### 1. Deploy to Raspberry Pi

Copy the monitoring files to your Pi and run from the bot project directory:
```bash
# Copy files to your Pi
scp run/voltage_monitor.py pi@your-pi-ip:/tmp/
scp run/setup_voltage_monitoring.sh pi@your-pi-ip:/tmp/

# SSH to your Pi and go to bot project directory
ssh pi@your-pi-ip
cd /path/to/your/BingoBot/project

# Run the setup script
chmod +x /tmp/setup_voltage_monitoring.sh
/tmp/setup_voltage_monitoring.sh
```

### 2. Verify Setup

Check that everything is working:
```bash
# Test the monitoring script manually
cd /home/pi/bingobot-monitoring
python3 voltage_monitor.py

# Check if the flag file was created (if undervoltage detected)
ls -la ./database/undervoltage

# View the cron job
crontab -l

# Check logs
tail -f /var/log/voltage_monitor.log
```

### 3. Automatic Notifications

The bot will automatically post "i am undervolting :(" to #general when undervoltage is detected. That's it!

## File Structure

```
Host Pi:
/home/pi/bingobot-monitoring/voltage_monitor.py  # Monitoring script
./database/undervoltage  # Flag file (empty file, just existence matters)
/var/log/voltage_monitor.log  # Log file

Docker Container:
/db/undervoltage  # Same flag file, mounted via ./database:/db volume
```

## Flag File Logic

- **Undervoltage detected**: Empty file `./database/undervoltage` is created
- **No undervoltage**: File is removed
- **Bot checks**: Every 5 minutes, if file exists → send message to #general

## Notifications

- **Simple message**: "i am undervolting :(" sent to #general
- **May repeat**: Message sent every 5 minutes while condition persists
- **No embeds**: Just plain text message
- **No state tracking**: Pure file existence check

## Troubleshooting

### No flag file created
- Check script can run: `cd /home/pi/bingobot-monitoring && python3 voltage_monitor.py`
- Verify ./database directory exists and is writable

### No Discord notifications
- Check bot logs: `docker logs bingobot`
- Verify bot has monitoring cog loaded
- Check if flag file exists: `ls -la ./database/undervoltage`

### Script errors
- Check monitoring logs: `tail -f /var/log/voltage_monitor.log`
- Test script manually: `cd /home/pi/bingobot-monitoring && python3 voltage_monitor.py`
- Verify dmesg access: `dmesg | tail`

### Cron not running
- Check cron service: `sudo systemctl status cron`
- Check cron logs: `grep CRON /var/log/syslog`
- List cron jobs: `crontab -l` 