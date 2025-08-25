#!/usr/bin/env python3
"""
Raspberry Pi voltage monitoring script.

This script checks for under-voltage warnings in dmesg and creates/removes
a simple flag file that the Discord bot can check.

Run this script every 5 minutes via cron:
*/5 * * * * /usr/bin/python3 /path/to/run/voltage_monitor.py

The script manages the file ./database/undervoltage
which appears as /db/undervoltage inside the container.
"""
import subprocess
import sys
from pathlib import Path


def check_voltage_warnings():
    """Check dmesg for under-voltage warnings."""
    try:
        # Run dmesg and look for under-voltage messages
        result = subprocess.run(
            ['dmesg', '--time-format=iso'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            print(f"Error running dmesg: {result.stderr}", file=sys.stderr)
            return None
            
        # Look for under-voltage messages in the output
        lines = result.stdout.strip().split('\n')
        
        for line in lines:
            if 'under-voltage' in line.lower():
                # Look for the specific under-voltage pattern
                if 'under-voltage detected' in line.lower() or 'throttled due to under-voltage' in line.lower():
                    return True
        
        return False
        
    except subprocess.TimeoutExpired:
        print("dmesg command timed out", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error checking voltage warnings: {e}", file=sys.stderr)
        return None


def main():
    """Main function to check voltage and update flag file."""
    # Path to the flag file (in the local database directory)
    # This gets mounted as /db/undervoltage inside the container
    flag_file = Path("./database/undervoltage")
    
    # Check for voltage warnings
    has_warning = check_voltage_warnings()
    
    if has_warning is None:
        print("Failed to check voltage warnings", file=sys.stderr)
        return 1
    
    # Ensure database directory exists
    flag_file.parent.mkdir(parents=True, exist_ok=True)
    
    if has_warning:
        # Create the flag file
        flag_file.touch()
        print("Undervoltage detected - flag file created")
    else:
        # Remove the flag file if it exists
        if flag_file.exists():
            flag_file.unlink()
            print("No undervoltage - flag file removed")
        else:
            print("No undervoltage - no flag file")
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 