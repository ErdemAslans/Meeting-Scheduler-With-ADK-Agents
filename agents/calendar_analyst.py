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
        return {
            'available_slots': [],
            'participants': participants,
            'date': date,
            'duration': duration_minutes,
            'message': '❌ OAuth bağlantısı yok - Lütfen önce authentication yapın',
            'real_data': False
        }
    
    try:
        # Tarih aralığını hesapla
        start_date = datetime.strptime(date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0)
        end_date = start_date + timedelta(days=1)
        
        # FreeBusy sorgusu - Türkiye saati
        import pytz
        turkey_tz = pytz.timezone('Europe/Istanbul')
        start_date_tz = turkey_tz.localize(start_date)
        end_date_tz = turkey_tz.localize(end_date)
        
        freebusy_query = {
            'timeMin': start_date_tz.isoformat(),
            'timeMax': end_date_tz.isoformat(),
            'timeZone': 'Europe/Istanbul',
            'items': [{'id': email} for email in participants]
        }
        
        print(f"🔍 OAuth 2.0: {len(participants)} katılımcı için takvim kontrolü...")
        freebusy_result = oauth_service.service.freebusy().query(body=freebusy_query).execute()
        busy_times = freebusy_result.get('calendars', {})
        
        # Özel takvim kontrolü - erişilemeyen takvimleri tespit et
        inaccessible_calendars = []
        accessible_calendars = []
        
        for participant_email in participants:
            calendar_data = busy_times.get(participant_email, {})
            
            # Hata kontrolü - API erişim hatası
            if 'errors' in calendar_data:
                error_reasons = [error.get('reason', 'unknown') for error in calendar_data['errors']]
                if 'notFound' in error_reasons or 'internalError' in error_reasons:
                    print(f"🚫 {participant_email}: FreeBusy API erişim reddedildi (private calendar)")
                    inaccessible_calendars.append(participant_email)
                else:
                    print(f"❌ {participant_email}: API hatası - {error_reasons}")
                    inaccessible_calendars.append(participant_email)
            elif 'busy' in calendar_data:
                accessible_calendars.append(participant_email)
                if len(calendar_data['busy']) == 0:
                    print(f"✅ {participant_email}: FreeBusy erişimi başarılı (boş takvim veya müsait)")
                else:
                    print(f"✅ {participant_email}: FreeBusy erişimi başarılı ({len(calendar_data['busy'])} meşgul slot)")
            else:
                print(f"⚠️ {participant_email}: FreeBusy yanıtı alınamadı")
                inaccessible_calendars.append(participant_email)
        
        # Müsait saatleri hesapla
        available_slots = _calculate_free_slots(busy_times, start_date, duration_minutes)
        
        # Boş takvim kontrolü ve alternatif önerileri
        no_slots_available = len(available_slots) == 0
        
        # Uyarı ve öneri mesajları oluştur
        access_warning = len(inaccessible_calendars) > 0
        warning_message = ""
        if access_warning:
            warning_message = f" ⚠️ UYARI: {len(inaccessible_calendars)} katılımcının takvimine erişim yok: {', '.join(inaccessible_calendars)}"
        
        # Boş takvim mesajı
        availability_message = ""
        if no_slots_available:
            availability_message = f"❌ {date} tarihinde {duration_minutes} dakikalık toplantı için boş slot bulunamadı!"
        else:
            availability_message = f"✅ {len(available_slots)} müsait zaman bulundu"
        
        # Alternatif tarih önerileri oluştur (eğer slot yoksa)
        alternative_dates = []
        if no_slots_available:
            base_date = datetime.strptime(date, '%Y-%m-%d')
            for i in range(1, 8):  # Sonraki 7 gün
                next_date = base_date + timedelta(days=i)
                # Hafta sonu atla
                if next_date.weekday() < 5:  # 0-4 hafta içi
                    alternative_dates.append(next_date.strftime('%Y-%m-%d'))
                if len(alternative_dates) >= 3:  # Maksimum 3 alternatif
                    break
        
        return {
            'available_slots': available_slots,
            'participants': participants,
            'accessible_participants': accessible_calendars,
            'inaccessible_participants': inaccessible_calendars,
            'calendar_access_warning': access_warning,
            'no_slots_available': no_slots_available,
            'alternative_dates': alternative_dates,
            'date': date,
            'duration': duration_minutes,
            'message': f'OAuth 2.0 API: {len(accessible_calendars)} katılımcının takvimi kontrol edildi. {availability_message}{warning_message}',
            'real_data': True,
            'oauth_user': oauth_service.user_email
        }
        
    except HttpError as e:
        print(f"❌ OAuth Calendar API hatası: {e}")
        return {
            'available_slots': [],
            'participants': participants,
            'date': date,
            'duration': duration_minutes,
            'message': f'❌ Calendar API hatası: {str(e)}',
            'real_data': False
        }
    except Exception as e:
        print(f"❌ OAuth Calendar hatası: {e}")
        return {
            'available_slots': [],
            'participants': participants,
            'date': date,
            'duration': duration_minutes,
            'message': f'❌ Calendar hatası: {str(e)}',
            'real_data': False
        }

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
        
        # Tarih ve saat hesapla - Timezone düzeltmesi
        import pytz
        turkey_tz = pytz.timezone('Europe/Istanbul')
        
        if 'start_datetime' in meeting_details and 'end_datetime' in meeting_details:
            # ISO format datetime string'leri
            meeting_datetime = datetime.fromisoformat(meeting_details['start_datetime'])
            end_datetime = datetime.fromisoformat(meeting_details['end_datetime'])
            
            # Eğer timezone bilgisi yoksa Türkiye saatini ekle
            if meeting_datetime.tzinfo is None:
                meeting_datetime = turkey_tz.localize(meeting_datetime)
            if end_datetime.tzinfo is None:
                end_datetime = turkey_tz.localize(end_datetime)
        else:
            # Eski format desteği
            date = meeting_details.get('date')
            start_time = meeting_details.get('start_time')
            duration = meeting_details.get('duration')
            
            # ZORUNLU ALAN KONTROLÜ
            if not start_time:
                raise ValueError("⚠️ start_time zorunlu! Meeting details'da start_time eksik.")
            if not duration:
                raise ValueError("⚠️ duration zorunlu! Meeting details'da duration eksik.")
            
            # DEBUG: Duration kontrolü
            print(f"🔍 create_calendar_event DEBUG:")
            print(f"   - meeting_details keys: {list(meeting_details.keys())}")
            print(f"   - duration value: {duration}")
            print(f"   - start_time: {start_time}")
            print(f"   - date: {date}")
            
            if not date:
                raise ValueError("Meeting date is required")
            
            # Naive datetime oluştur ve Türkiye saatiyle localize et
            naive_datetime = datetime.strptime(f"{date} {start_time}", '%Y-%m-%d %H:%M')
            meeting_datetime = turkey_tz.localize(naive_datetime)
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
    """Müsait zaman dilimlerini hesapla - Timezone düzeltmesi"""
    import pytz
    turkey_tz = pytz.timezone('Europe/Istanbul')
    
    # Türkiye saatiyle çalışma saatleri
    work_start = start_date.replace(hour=9, minute=0, second=0, microsecond=0)
    work_end = start_date.replace(hour=18, minute=0, second=0, microsecond=0)
    
    # Eğer timezone bilgisi yoksa Türkiye saatiyle localize et
    if work_start.tzinfo is None:
        work_start = turkey_tz.localize(work_start)
        work_end = turkey_tz.localize(work_end)
    
    available_slots = []
    current_time = work_start
    
    while current_time + timedelta(minutes=duration_minutes) <= work_end:
        slot_end = current_time + timedelta(minutes=duration_minutes)
        is_available = True
        
        for participant_email, calendar_data in busy_times.items():
            if 'busy' in calendar_data:
                for busy_period in calendar_data['busy']:
                    # Google Calendar'dan gelen UTC zamanları Türkiye saatine çevir
                    busy_start = datetime.fromisoformat(busy_period['start'].replace('Z', '+00:00'))
                    busy_end = datetime.fromisoformat(busy_period['end'].replace('Z', '+00:00'))
                    
                    # UTC'den Türkiye saatine çevir
                    busy_start = busy_start.astimezone(turkey_tz)
                    busy_end = busy_end.astimezone(turkey_tz)
                    
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