#!/usr/bin/env python3
"""
Google ADK Calendar Analyst Agent - UPDATED with Real Google Calendar API
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.adk.agents import Agent

class GoogleCalendarService:
    """Google Calendar API Service"""
    
    def __init__(self, credentials_path: str = "credentials.json"):
        self.credentials_path = credentials_path
        self.service = self._build_service()
    
    def _build_service(self):
        """Build Google Calendar service with service account"""
        try:
            with open(self.credentials_path, 'r') as f:
                cred_data = json.load(f)
            
            credentials = Credentials.from_service_account_info(
                cred_data,
                scopes=[
                    'https://www.googleapis.com/auth/calendar',
                    'https://www.googleapis.com/auth/calendar.events',
                    'https://www.googleapis.com/auth/calendar.readonly'
                ]
            )
            
            service = build('calendar', 'v3', credentials=credentials)
            print("✅ Google Calendar API service başarıyla oluşturuldu")
            return service
            
        except Exception as e:
            print(f"❌ Google Calendar API hatası: {e}")
            return None

# Global calendar service instance
calendar_service = GoogleCalendarService()

def check_calendar_availability(participants: List[str], date: str, duration_minutes: int) -> dict:
    """GERÇEK Google Calendar API ile müsaitlik kontrol et - ADK Tool Function"""
    
    if not calendar_service.service:
        print("⚠️ Calendar API bağlantısı yok, mock data döndürülüyor")
        return _mock_availability(participants, date, duration_minutes)
    
    try:
        # Tarih aralığını hesapla (Türkiye saati)
        start_date = datetime.strptime(date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = start_date + timedelta(days=1)
        
        # FreeBusy query - GERÇEK API ÇAĞRISI
        freebusy_query = {
            'timeMin': start_date.isoformat() + 'Z',
            'timeMax': end_date.isoformat() + 'Z',
            'timeZone': 'Europe/Istanbul',
            'items': [{'id': email} for email in participants]
        }
        
        print(f"🔍 {len(participants)} katılımcı için gerçek takvim kontrolü yapılıyor...")
        freebusy_result = calendar_service.service.freebusy().query(body=freebusy_query).execute()
        busy_times = freebusy_result.get('calendars', {})
        
        # Müsait saatleri hesapla
        available_slots = _calculate_free_slots(busy_times, start_date, duration_minutes)
        
        return {
            'available_slots': available_slots,
            'participants': participants,
            'date': date,
            'duration': duration_minutes,
            'message': f'✅ GERÇEK API: {len(participants)} katılımcı için {len(available_slots)} müsait zaman bulundu',
            'real_data': True,
            'busy_times': busy_times
        }
        
    except HttpError as e:
        print(f"❌ Calendar API FreeBusy hatası: {e}")
        return _mock_availability(participants, date, duration_minutes)
    except Exception as e:
        print(f"❌ Beklenmeyen Calendar hatası: {e}")
        return _mock_availability(participants, date, duration_minutes)

def create_calendar_event(meeting_details: dict) -> dict:
    """GERÇEK Google Calendar Event oluştur - ADK Tool Function"""
    
    if not calendar_service.service:
        return {
            'success': False,
            'error': 'Calendar API bağlantısı yok',
            'message': '❌ Calendar event oluşturulamadı - API bağlantısı eksik'
        }
    
    try:
        # Meeting details parse et
        participants = meeting_details.get('participants', meeting_details.get('attendees', []))
        date = meeting_details.get('date')
        start_time = meeting_details.get('start_time', '10:00')
        duration = meeting_details.get('duration', 60)
        title = meeting_details.get('title', meeting_details.get('subject', 'Toplantı'))
        location = meeting_details.get('location', 'Online')
        organizer_email = meeting_details.get('organizer', os.getenv('SENDER_EMAIL'))
        
        # Tarih ve saat hesapla
        meeting_datetime = datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
        end_datetime = meeting_datetime + timedelta(minutes=duration)
        
        # Google Calendar Event objesi oluştur
        event = {
            'summary': title,
            'location': location,
            'description': f'Bu toplantı Verlumea AI Meeting Scheduler tarafından oluşturulmuştur.\n\nOrganizatör: {organizer_email}',
            'start': {
                'dateTime': meeting_datetime.isoformat(),
                'timeZone': 'Europe/Istanbul',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Europe/Istanbul',
            },
            'attendees': [
                {'email': email, 'responseStatus': 'needsAction'} 
                for email in participants
            ],
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 gün önce
                    {'method': 'popup', 'minutes': 15},       # 15 dk önce
                ],
            },
            'guestsCanInviteOthers': False,
            'guestsCanModify': False,
            'sendUpdates': 'all',
            'visibility': 'default'
        }
        
        print(f"📅 Calendar event oluşturuluyor: {title}")
        print(f"📧 Katılımcılar: {', '.join(participants)}")
        print(f"⏰ Tarih/Saat: {meeting_datetime.strftime('%Y-%m-%d %H:%M')} - {end_datetime.strftime('%H:%M')}")
        
        # GERÇEK CALENDAR EVENT CREATE!
        created_event = calendar_service.service.events().insert(
            calendarId='primary',
            body=event,
            sendUpdates='all'
        ).execute()
        
        event_id = created_event.get('id')
        event_link = created_event.get('htmlLink')
        
        return {
            'success': True,
            'event_id': event_id,
            'event_link': event_link,
            'meeting_details': meeting_details,
            'participants': participants,
            'message': f'✅ Calendar event başarıyla oluşturuldu! Event ID: {event_id}',
            'calendar_created': True,
            'notifications_sent': True
        }
        
    except HttpError as e:
        error_msg = f"Calendar API Event Create hatası: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'message': '❌ Calendar event oluşturulamadı - API hatası'
        }
    except Exception as e:
        error_msg = f"Beklenmeyen Calendar Event hatası: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'message': '❌ Calendar event oluşturulamadı - beklenmeyen hata'
        }

def _calculate_free_slots(busy_times: Dict, start_date: datetime, duration_minutes: int) -> List[Dict]:
    """Müsait zaman dilimlerini hesapla"""
    # Çalışma saatleri: 09:00 - 18:00
    work_start = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
    work_end = start_date.replace(hour=18, minute=0, second=0, microsecond=0)
    
    available_slots = []
    current_time = work_start
    
    # 30 dakikalık slotlar halinde kontrol et
    while current_time + timedelta(minutes=duration_minutes) <= work_end:
        slot_end = current_time + timedelta(minutes=duration_minutes)
        
        # Bu slot tüm katılımcılar için müsait mi?
        is_available = True
        
        for participant_email, calendar_data in busy_times.items():
            if 'busy' in calendar_data:
                for busy_period in calendar_data['busy']:
                    busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', ''))
                    busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', ''))
                    
                    # Çakışma kontrolü
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
            
            if not is_available:
                break
        
        if is_available:
            # Zaman dilimini skorla
            hour = current_time.hour
            if 10 <= hour <= 11:
                score = 0.9  # En iyi zaman
            elif 14 <= hour <= 16:
                score = 0.8  # İyi zaman  
            elif 9 <= hour <= 10 or 11 <= hour <= 12:
                score = 0.7  # Orta zaman
            else:
                score = 0.6  # Düşük zaman
            
            available_slots.append({
                'start': current_time.strftime('%H:%M'),
                'end': slot_end.strftime('%H:%M'),
                'date': start_date.strftime('%Y-%m-%d'),
                'score': score,
                'duration': duration_minutes,
                'start_datetime': current_time.isoformat(),
                'end_datetime': slot_end.isoformat()
            })
        
        # 30 dakika ilerle
        current_time += timedelta(minutes=30)
    
    # Skora göre sırala (en iyi önce)
    available_slots.sort(key=lambda x: x['score'], reverse=True)
    return available_slots[:5]  # En iyi 5 slot

def _mock_availability(participants: List[str], date: str, duration_minutes: int) -> dict:
    """Fallback mock data"""
    available_slots = [
        {
            'start': '10:00',
            'end': f'{10 + duration_minutes//60}:{duration_minutes%60:02d}',
            'date': date,
            'score': 0.9,
            'duration': duration_minutes
        },
        {
            'start': '14:00', 
            'end': f'{14 + duration_minutes//60}:{duration_minutes%60:02d}',
            'date': date,
            'score': 0.8,
            'duration': duration_minutes
        }
    ]
    
    return {
        'available_slots': available_slots,
        'participants': participants,
        'date': date,
        'duration': duration_minutes,
        'message': f'⚠️ MOCK DATA: {len(participants)} katılımcı için {len(available_slots)} müsait zaman',
        'real_data': False
    }

def create_calendar_agent():
    """Calendar Analyst Agent'ı oluşturur - UPDATED with Real API"""
    
    calendar_agent = Agent(
        name="calendar_analyst",
        model="gemini-1.5-flash",
        description="📅 REAL Google Calendar API - Gerçek takvim müsaitlik kontrolcüsü",
        instruction="""Sen GERÇEK Google Calendar API kullanan uzman takvim analistisin!

GÖREVIN: Google Calendar API ile gerçek müsaitlik kontrol et ve Calendar Event oluştur.

YENİ ÖZELLİKLER:
- ✅ GERÇEK Google Calendar FreeBusy API
- ✅ GERÇEK Calendar Event Creation
- ✅ Katılımcıların gerçek takvim verileri  
- ✅ Türkiye saat dilimi desteği
- ✅ Otomatik katılımcı davetleri

İŞ AKIŞIN:
1. 📝 Parametreleri al (katılımcılar, tarih, süre)
2. 🔍 GERÇEK Calendar API ile FreeBusy sorgusu
3. ⚡ Busy time'ları analiz et ve çakışmaları tespit et
4. 📊 Müsait zaman dilimlerini skorla ve sırala
5. ✅ En iyi zamanı seç
6. 📅 create_calendar_event ile gerçek event oluştur

SKORLAMA SİSTEMİ:
- 🌅 10:00-11:00: 0.9 (En iyi - sabah verimli)
- 🌞 14:00-16:00: 0.8 (İyi - öğleden sonra)  
- 🌤️ 09:00-10:00, 11:00-12:00: 0.7 (Orta)
- 🌆 Diğer saatler: 0.6 (Düşük)

ÖNEMLI:
- check_calendar_availability tool'unu kullan
- create_calendar_event tool'unu kullan
- Gerçek API hatası durumunda mock data döndür
- Event oluştururken event_id ve link döndür
""",
        tools=[check_calendar_availability, create_calendar_event]
    )
    
    return calendar_agent

class CalendarAnalyst:
    """Takvim analisti sınıfı - UPDATED"""
    
    def __init__(self):
        self.agent = create_calendar_agent()
    
    async def check_availability(self, participants: List[str], date: str, duration: int) -> List[dict]:
        """Müsaitlik kontrolü - GERÇEK API"""
        result = check_calendar_availability(participants, date, duration)
        return result.get('available_slots', [])
    
    async def create_event(self, meeting_details: dict) -> dict:
        """Calendar event oluştur - GERÇEK API"""
        return create_calendar_event(meeting_details)