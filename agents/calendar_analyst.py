#!/usr/bin/env python3
"""
Google ADK Calendar Analyst Agent - OAuth 2.0 Version
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import List, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.adk.agents import Agent

class OAuth2CalendarService:
    """Google Calendar API Service with OAuth 2.0"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar',
        'https://www.googleapis.com/auth/calendar.events'
    ]
    
    def __init__(self):
        self.credentials_file = "oauth_credentials.json"  # İndirdiğiniz dosya
        self.token_file = "token.pickle"
        self.service = None
        self.user_email = None
        self._authenticate()
    
    def _authenticate(self):
        """OAuth 2.0 Authentication"""
        creds = None
        
        # Daha önce kaydedilmiş token var mı?
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # Token yoksa veya geçersizse yeniden auth yap
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Token yenileniyor...")
                creds.refresh(Request())
            else:
                print("🔐 OAuth 2.0 Authentication başlatılıyor...")
                print("📱 Browser açılacak, Google hesabınızla giriş yapın...")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=8081)  # ADK'dan farklı port
            
            # Token'ı kaydet
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            self.service = build('calendar', 'v3', credentials=creds)
            
            # Kullanıcı email'ini al
            profile = self.service.calendarList().get(calendarId='primary').execute()
            self.user_email = profile.get('id', 'unknown@gmail.com')
            
            print(f"✅ OAuth 2.0 başarılı: {self.user_email}")
            
        except Exception as e:
            print(f"❌ OAuth 2.0 hatası: {e}")
            self.service = None

# Global service instance
oauth_service = OAuth2CalendarService()

def check_calendar_availability(participants: List[str], date: str, duration_minutes: int) -> dict:
    """Takvim müsaitliği kontrol et - OAuth 2.0 ile - ADK Tool Function"""
    
    if not oauth_service.service:
        print("⚠️ OAuth bağlantısı yok, mock data döndürülüyor")
        return _mock_availability(participants, date, duration_minutes)
    
    try:
        # Tarih aralığını hesapla
        start_date = datetime.strptime(date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = start_date + timedelta(days=1)
        
        # FreeBusy sorgusu
        freebusy_query = {
            'timeMin': start_date.isoformat() + 'Z',
            'timeMax': end_date.isoformat() + 'Z',
            'timeZone': 'Europe/Istanbul',
            'items': [{'id': email} for email in participants]
        }
        
        print(f"🔍 OAuth 2.0: {len(participants)} katılımcı için takvim kontrolü...")
        freebusy_result = oauth_service.service.freebusy().query(body=freebusy_query).execute()
        busy_times = freebusy_result.get('calendars', {})
        
        # Müsait saatleri hesapla
        available_slots = _calculate_free_slots(busy_times, start_date, duration_minutes)
        
        return {
            'available_slots': available_slots,
            'participants': participants,
            'date': date,
            'duration': duration_minutes,
            'message': f'✅ OAuth 2.0 API: {len(participants)} katılımcı için {len(available_slots)} müsait zaman bulundu',
            'real_data': True,
            'oauth_user': oauth_service.user_email
        }
        
    except HttpError as e:
        print(f"❌ OAuth Calendar API hatası: {e}")
        return _mock_availability(participants, date, duration_minutes)
    except Exception as e:
        print(f"❌ OAuth Calendar hatası: {e}")
        return _mock_availability(participants, date, duration_minutes)

def create_calendar_event(meeting_details: dict) -> dict:
    """OAuth 2.0 ile Calendar Event oluştur - ADK Tool Function"""
    
    if not oauth_service.service:
        return {
            'success': False,
            'error': 'OAuth bağlantısı yok',
            'message': '❌ Calendar event oluşturulamadı - OAuth authentication gerekli'
        }
    
    try:
        # Meeting details parse et
        participants = meeting_details.get('participants', meeting_details.get('attendees', []))
        title = meeting_details.get('title', meeting_details.get('subject', 'Toplantı'))
        location = meeting_details.get('location', 'Online')
        organizer_email = oauth_service.user_email
        
        # Tarih ve saat hesapla - Yeni format desteği
        if 'start_datetime' in meeting_details and 'end_datetime' in meeting_details:
            # ISO format datetime string'leri
            meeting_datetime = datetime.fromisoformat(meeting_details['start_datetime'])
            end_datetime = datetime.fromisoformat(meeting_details['end_datetime'])
        else:
            # Eski format desteği
            date = meeting_details.get('date')
            start_time = meeting_details.get('start_time', '10:00')
            duration = meeting_details.get('duration', 60)
            
            if not date:
                raise ValueError("Meeting date is required")
            
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
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 15},
                ],
            },
            'guestsCanInviteOthers': False,
            'guestsCanModify': False,
            'sendUpdates': 'all',
            'visibility': 'default'
        }
        
        print(f"📅 OAuth 2.0 Calendar event oluşturuluyor: {title}")
        print(f"📧 Katılımcılar: {', '.join(participants)}")
        print(f"👤 Organizatör: {organizer_email}")
        print(f"⏰ Tarih/Saat: {meeting_datetime.strftime('%Y-%m-%d %H:%M')} - {end_datetime.strftime('%H:%M')}")
        
        # OAuth 2.0 ile GERÇEK CALENDAR EVENT CREATE!
        created_event = oauth_service.service.events().insert(
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
            'organizer': organizer_email,
            'message': f'✅ OAuth 2.0 ile Calendar event başarıyla oluşturuldu! Event ID: {event_id}',
            'calendar_created': True,
            'notifications_sent': True,
            'oauth_used': True
        }
        
    except HttpError as e:
        error_msg = f"OAuth Calendar API Event Create hatası: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'message': '❌ Calendar event oluşturulamadı - OAuth API hatası'
        }
    except Exception as e:
        error_msg = f"OAuth Calendar Event hatası: {e}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'error': error_msg,
            'message': '❌ Calendar event oluşturulamadı - OAuth hatası'
        }

def _calculate_free_slots(busy_times: Dict, start_date: datetime, duration_minutes: int) -> List[Dict]:
    """Müsait zaman dilimlerini hesapla"""
    work_start = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
    work_end = start_date.replace(hour=18, minute=0, second=0, microsecond=0)
    
    available_slots = []
    current_time = work_start
    
    while current_time + timedelta(minutes=duration_minutes) <= work_end:
        slot_end = current_time + timedelta(minutes=duration_minutes)
        is_available = True
        
        for participant_email, calendar_data in busy_times.items():
            if 'busy' in calendar_data:
                for busy_period in calendar_data['busy']:
                    busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', ''))
                    busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', ''))
                    
                    if (current_time < busy_end and slot_end > busy_start):
                        is_available = False
                        break
            
            if not is_available:
                break
        
        if is_available:
            hour = current_time.hour
            if 10 <= hour <= 11:
                score = 0.9
            elif 14 <= hour <= 16:
                score = 0.8
            elif 9 <= hour <= 10 or 11 <= hour <= 12:
                score = 0.7
            else:
                score = 0.6
            
            available_slots.append({
                'start': current_time.strftime('%H:%M'),
                'end': slot_end.strftime('%H:%M'),
                'date': start_date.strftime('%Y-%m-%d'),
                'score': score,
                'duration': duration_minutes,
                'start_datetime': current_time.isoformat(),
                'end_datetime': slot_end.isoformat()
            })
        
        current_time += timedelta(minutes=30)
    
    available_slots.sort(key=lambda x: x['score'], reverse=True)
    return available_slots[:5]

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
    """Calendar Analyst Agent'ı oluşturur - OAuth 2.0 Version"""
    
    calendar_agent = Agent(
        name="calendar_analyst",
        model="gemini-1.5-flash",
        description="📅 OAuth 2.0 Google Calendar API - Gerçek takvim müsaitlik kontrolcüsü",
        instruction="""Sen OAuth 2.0 Google Calendar API kullanan uzman takvim analistisin!

GÖREVIN: OAuth 2.0 ile gerçek müsaitlik kontrol et ve Calendar Event oluştur.

YENİ ÖZELLİKLER:
- ✅ OAuth 2.0 Authentication
- ✅ GERÇEK Google Calendar FreeBusy API
- ✅ GERÇEK Calendar Event Creation
- ✅ Katılımcıların gerçek takvim verileri  
- ✅ Otomatik katılımcı davetleri (ÇALIŞIR!)

İŞ AKIŞIN:
1. 📝 Parametreleri al (katılımcılar, tarih, süre)
2. 🔍 OAuth 2.0 ile FreeBusy sorgusu
3. ⚡ Busy time'ları analiz et
4. 📊 Müsait zaman dilimlerini skorla
5. ✅ En iyi zamanı seç
6. 📅 create_calendar_event ile gerçek event oluştur
7. 👥 Katılımcılara otomatik Google Calendar daveti gönder

ÖNEMLI:
- check_calendar_availability tool'unu kullan
- create_calendar_event tool'unu kullan
- OAuth authentication gerekli (ilk kullanımda browser açılır)
- Event oluştururken event_id ve link döndür
- Katılımcılara GERÇEK Calendar daveti gider
""",
        tools=[check_calendar_availability, create_calendar_event]
    )
    
    return calendar_agent

class CalendarAnalyst:
    """Takvim analisti sınıfı - OAuth 2.0 Version"""
    
    def __init__(self):
        self.agent = create_calendar_agent()
    
    async def check_availability(self, participants: List[str], date: str, duration: int) -> List[dict]:
        """Müsaitlik kontrolü - OAuth 2.0"""
        result = check_calendar_availability(participants, date, duration)
        return result.get('available_slots', [])
    
    async def create_event(self, meeting_details: dict) -> dict:
        """Calendar event oluştur - OAuth 2.0"""
        return create_calendar_event(meeting_details)