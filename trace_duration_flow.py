#!/usr/bin/env python3
"""
Trace the complete duration flow to identify where the issue occurs
"""

import re
from datetime import datetime, timedelta

def trace_duration_flow():
    """Trace the complete duration parsing and usage flow"""
    
    print("TRACING DURATION FLOW FOR: '30 dakika toplantı'")
    print("=" * 70)
    
    request = "30 dakika toplantı"
    user_email = "test@example.com"
    
    # Step 1: Memory Manager - get_context_suggestions
    print("STEP 1: Memory Manager - get_context_suggestions")
    print("-" * 50)
    
    # Simulate no existing user profile
    user_profiles = {}  # Empty - new user
    
    suggestions = {
        'similar_meetings': [],
        'frequent_participants': [],
        'preferred_time': None,
        'preferred_duration': 60  # Default hardcoded
    }
    
    profile = user_profiles.get(user_email)  # None for new user
    if profile:
        suggestions['preferred_duration'] = profile.preferred_meeting_duration
        print(f"  Using profile preferred duration: {profile.preferred_meeting_duration}")
    else:
        print(f"  No user profile found, using default: {suggestions['preferred_duration']}")
    
    print(f"  Memory suggestions: {suggestions}")
    
    # Step 2: Orchestrator - parse_meeting_request
    print("\nSTEP 2: Orchestrator - parse_meeting_request")
    print("-" * 50)
    
    # Start with memory default
    duration = suggestions.get('preferred_duration', 60)
    print(f"  Initial duration from memory: {duration} minutes")
    
    # Parse user request
    time_patterns = [
        (r'(\d+)\s*saat', 'hour'),
        (r'(\d+)\s*hour', 'hour'),
        (r'(\d+)\s*dakika', 'minute'),
        (r'(\d+)\s*minute', 'minute'),
        (r'(\d+)\s*dk', 'minute'),
        (r'(\d+)\s*min', 'minute')
    ]
    
    print(f"  Parsing request: '{request.lower()}'")
    
    for pattern, unit in time_patterns:
        matches = re.findall(pattern, request.lower())
        if matches:
            time_value = int(matches[0])
            print(f"  ✅ Pattern '{pattern}' matched: {matches}")
            
            if unit == 'hour':
                duration = time_value * 60
                print(f"  Converting hours to minutes: {time_value} * 60 = {duration}")
            else:
                duration = time_value
                print(f"  Using minutes directly: {duration}")
            break
    else:
        print(f"  ❌ No pattern matched, keeping default: {duration}")
    
    print(f"  Final parsed duration: {duration} minutes")
    
    # Create meeting_info dict (same as orchestrator)
    meeting_info = {
        'participants': ['test@participant.com'],
        'date': '2025-06-20',
        'duration': duration,
        'title': 'Test Toplantı',
        'location': 'Online',
        'organizer': user_email
    }
    
    print(f"  Meeting info created with duration: {meeting_info['duration']}")
    
    # Step 3: Calendar Analyst - create_calendar_event
    print("\nSTEP 3: Calendar Analyst - create_calendar_event")
    print("-" * 50)
    
    meeting_details = meeting_info.copy()
    
    # This is the critical part in calendar_analyst.py
    date = meeting_details.get('date')
    start_time = meeting_details.get('start_time', '10:00')
    duration_from_details = meeting_details.get('duration', 60)  # ⚠️ Default fallback!
    
    print(f"  Meeting details duration: {meeting_details.get('duration', 'NOT FOUND')}")
    print(f"  Duration from get() with fallback: {duration_from_details}")
    
    if meeting_details.get('duration') is None:
        print("  ❌ ISSUE: Duration is None, using fallback of 60 minutes!")
    else:
        print(f"  ✅ Duration properly passed: {duration_from_details} minutes")
    
    # Calculate end time
    meeting_datetime = datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
    end_datetime = meeting_datetime + timedelta(minutes=duration_from_details)
    
    print(f"  Start time: {meeting_datetime}")
    print(f"  End time: {end_datetime}")
    print(f"  Calculated duration: {duration_from_details} minutes")
    
    # Step 4: Check for data loss points
    print("\nSTEP 4: POTENTIAL DATA LOSS POINTS")
    print("-" * 50)
    
    # Check if orchestrator properly passes duration
    print("Checking orchestrator return:")
    orchestrator_return = {
        'participants': ['test@participant.com'],
        'date': '2025-06-20',
        'duration': duration,  # This should be 30
        'title': 'Test Toplantı'
    }
    print(f"  Orchestrator returns duration: {orchestrator_return['duration']}")
    
    # Check agent instruction handling
    print("\nChecking agent message format:")
    agent_message = f"""
    Toplantı Planlama İsteği: {request}
    
    Ayrıştırılan bilgiler:
    - Katılımcılar: test@participant.com
    - Tarih: 2025-06-20
    - Süre: {duration} dakika
    - Başlık: Test Toplantı
    """
    print(f"  Agent message includes duration: {duration} dakika")
    
    print(f"\nFINAL SUMMARY:")
    print(f"  User requested: 30 dakika")
    print(f"  Orchestrator parsed: {duration} minutes")
    print(f"  Calendar would create: {duration_from_details} minutes")
    
    if duration == 30 and duration_from_details == 30:
        print("  ✅ FLOW IS CORRECT")
    else:
        print("  ❌ ISSUE DETECTED")

if __name__ == "__main__":
    trace_duration_flow()