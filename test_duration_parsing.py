#!/usr/bin/env python3
"""
Test script to check duration parsing logic
"""

import re

def test_duration_parsing():
    """Test the duration parsing logic from orchestrator.py"""
    
    # Test cases
    test_requests = [
        "30 dakika toplantı",
        "30 dakikalık toplantı",
        "1 saat toplantı",
        "1 saatlik toplantı",
        "15 dakika demo",
        "2 saat planlama",
        "45 dakika",
        "30 minute meeting",
        "1 hour meeting",
        "60 dk toplantı",
        "90 min toplantı"
    ]
    
    # Same patterns as in orchestrator.py
    time_patterns = [
        (r'(\d+)\s*saat', 'hour'),
        (r'(\d+)\s*hour', 'hour'),
        (r'(\d+)\s*dakika', 'minute'),
        (r'(\d+)\s*minute', 'minute'),
        (r'(\d+)\s*dk', 'minute'),
        (r'(\d+)\s*min', 'minute')
    ]
    
    print("Duration Parsing Test Results:")
    print("=" * 50)
    
    for request in test_requests:
        # Default duration (same as in orchestrator.py)
        duration = 60  # Default from memory suggestions
        
        # Parse duration
        for pattern, unit in time_patterns:
            matches = re.findall(pattern, request.lower())
            if matches:
                time_value = int(matches[0])
                if unit == 'hour':
                    duration = time_value * 60
                else:
                    duration = time_value
                break
        
        print(f"Request: '{request}' -> Duration: {duration} minutes")
        
        # Check if this would be correct
        if "30 dakika" in request.lower() and duration != 30:
            print(f"  ❌ ISSUE: Expected 30 minutes, got {duration}")
        elif "30 dakika" in request.lower() and duration == 30:
            print(f"  ✅ CORRECT: 30 minutes")
        elif "1 saat" in request.lower() and duration != 60:
            print(f"  ❌ ISSUE: Expected 60 minutes, got {duration}")
        elif "1 saat" in request.lower() and duration == 60:
            print(f"  ✅ CORRECT: 60 minutes")

if __name__ == "__main__":
    test_duration_parsing()