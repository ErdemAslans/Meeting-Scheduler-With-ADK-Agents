"""
Agent modülleri
"""

# Google ADK için root_agent export
try:
    from .orchestrator import root_agent
except ImportError:
    root_agent = None

# Tool functions import (ADK olmadan da çalışsın)
try:
    from .calendar_analyst import check_calendar_availability
except ImportError:
    check_calendar_availability = None

try:
    from .email_composer import compose_meeting_invitation
except ImportError:
    compose_meeting_invitation = None

try:
    from .email_sender import send_meeting_invitations
except ImportError:
    send_meeting_invitations = None

# Klasik sınıflar
try:
    from .calendar_analyst import CalendarAnalyst
except ImportError:
    CalendarAnalyst = None

try:
    from .email_composer import EmailComposer
except ImportError:
    EmailComposer = None

try:
    from .email_sender import EmailSender
except ImportError:
    EmailSender = None

try:
    from .orchestrator import MeetingOrchestrator
except ImportError:
    MeetingOrchestrator = None

__all__ = [
    'root_agent',  # ADK için gerekli
    'CalendarAnalyst',
    'EmailComposer', 
    'EmailSender',
    'MeetingOrchestrator',
    'check_calendar_availability',
    'compose_meeting_invitation',
    'send_meeting_invitations'
]