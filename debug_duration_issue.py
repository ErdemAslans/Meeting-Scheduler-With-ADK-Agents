#!/usr/bin/env python3
"""
Debug script to identify the duration parsing issue
"""

import re
import os
from datetime import datetime, timedelta

def debug_duration_parsing():
    """Debug the exact issue with duration parsing"""
    
    # Test the problematic case
    problematic_request = "30 dakika toplantı"
    
    print(f"Debugging request: '{problematic_request}'")
    print("=" * 60)
    
    # Memory suggestions simulation (default duration)
    suggestions = {'preferred_duration': 60}  # Default from memory
    
    # Start with memory default
    duration = suggestions.get('preferred_duration', 60)
    print(f"1. Initial duration from memory: {duration} minutes")
    
    # Time patterns from orchestrator.py
    time_patterns = [
        (r'(\d+)\s*saat', 'hour'),
        (r'(\d+)\s*hour', 'hour'),
        (r'(\d+)\s*dakika', 'minute'),
        (r'(\d+)\s*minute', 'minute'),
        (r'(\d+)\s*dk', 'minute'),
        (r'(\d+)\s*min', 'minute')
    ]
    
    print(f"2. Analyzing request: '{problematic_request.lower()}'")
    
    # Check each pattern
    for i, (pattern, unit) in enumerate(time_patterns):
        matches = re.findall(pattern, problematic_request.lower())
        print(f"   Pattern {i+1}: {pattern} -> Matches: {matches}")
        
        if matches:
            time_value = int(matches[0])
            print(f"   Found time value: {time_value}")
            
            if unit == 'hour':
                duration = time_value * 60
                print(f"   Unit is 'hour' -> {time_value} * 60 = {duration} minutes")
            else:
                duration = time_value
                print(f"   Unit is 'minute' -> {duration} minutes")
            
            print(f"   Breaking from loop with duration: {duration}")
            break
    
    print(f"3. Final parsed duration: {duration} minutes")
    
    # Check if there are any other issues
    print("\n" + "=" * 60)
    print("ADDITIONAL CHECKS:")
    
    # Check for potential regex issues
    test_cases = [
        "30 dakika",
        "30dakika", 
        "30 dakika toplantı",
        "toplantı 30 dakika",
        "30 dakikalık toplantı",
        "30 dakika süreli toplantı"
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: '{test_case}'")
        duration = 60  # Reset to default
        
        for pattern, unit in time_patterns:
            matches = re.findall(pattern, test_case.lower())
            if matches:
                time_value = int(matches[0])
                if unit == 'hour':
                    duration = time_value * 60
                else:
                    duration = time_value
                print(f"  Pattern '{pattern}' matched -> {duration} minutes")
                break
        else:
            print(f"  No pattern matched -> default {duration} minutes")

if __name__ == "__main__":
    debug_duration_parsing()