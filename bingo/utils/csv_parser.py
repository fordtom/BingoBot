"""Utility for parsing CSV files for bingo games."""
import csv
import io
from typing import List, Dict, Any


async def parse_events_csv(file_content: str) -> List[Dict[str, Any]]:
    """
    Parse a CSV file containing event descriptions.
    
    Args:
        file_content: String content of the CSV file
        
    Returns:
        List of event dictionaries with 'description' keys
        
    Expected CSV format:
    ```
    description
    Event 1 description
    Event 2 description
    ...
    ```
    """
    events = []
    
    # Read the CSV content
    f = io.StringIO(file_content)
    reader = csv.DictReader(f)
    
    # If no header is provided, assume it's just descriptions
    if reader.fieldnames is None or 'description' not in reader.fieldnames:
        f.seek(0)
        reader = csv.reader(f)
        for row in reader:
            if row and row[0].strip():  # Skip empty lines
                events.append({'description': row[0].strip()})
    else:
        for row in reader:
            if 'description' in row and row['description'].strip():
                events.append({'description': row['description'].strip()})
    
    return events