import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import msal
import requests
import json
from google.adk.agents import Agent
import vertexai
from config.settings import GOOGLE_CALENDAR_CONFIG, MICROSOFT_GRAPH_CONFIG, WORKING_HOURS

async def check_calendar_availability(
    participants: List[str], 
    date: str, 
    duration_minutes: int
) -> Dict:
    """Takvim müsaitliğini kontrol eder - Google ADK Tool Function"""
    analyst = CalendarAnalyst()
    result = await analyst.check_availability(participants, date, duration_minutes)
    return {
        'available_slots': result,
        'participants': participants,
        'date': date,
        'duration': duration_minutes
    }

class CalendarAnalyst:
    def __init__(self):
        self.google_service = None
        self.microsoft_token = None
        
    async def authenticate_google(self) -> bool:
        """Google Calendar API kimlik doğrulama"""
        creds = None
        if os.path.exists(GOOGLE_CALENDAR_CONFIG['token_file']):
            creds = Credentials.from_authorized_user_file(
                GOOGLE_CALENDAR_CONFIG['token_file'], 
                GOOGLE_CALENDAR_CONFIG['scopes']
            )
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_CALENDAR_CONFIG['credentials_file'], 
                    GOOGLE_CALENDAR_CONFIG['scopes']
                )
                creds = flow.run_local_server(port=0)
            
            with open(GOOGLE_CALENDAR_CONFIG['token_file'], 'w') as token:
                token.write(creds.to_json())
        
        self.google_service = build('calendar', 'v3', credentials=creds)
        return True
    
    async def authenticate_microsoft(self) -> bool:
        """Microsoft Graph API kimlik doğrulama"""
        app = msal.ConfidentialClientApplication(
            MICROSOFT_GRAPH_CONFIG['client_id'],
            authority=f"https://login.microsoftonline.com/{MICROSOFT_GRAPH_CONFIG['tenant_id']}",
            client_credential=MICROSOFT_GRAPH_CONFIG['client_secret']
        )
        
        result = app.acquire_token_for_client(scopes=MICROSOFT_GRAPH_CONFIG['scope'])
        
        if "access_token" in result:
            self.microsoft_token = result['access_token']
            return True
        return False
    
    async def get_google_freebusy(self, email: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Google Calendar'dan FreeBusy bilgilerini al"""
        if not self.google_service:
            await self.authenticate_google()
        
        body = {
            "timeMin": start_time.isoformat() + 'Z',
            "timeMax": end_time.isoformat() + 'Z',
            "items": [{"id": email}]
        }
        
        try:
            response = self.google_service.freebusy().query(body=body).execute()
            busy_times = response.get('calendars', {}).get(email, {}).get('busy', [])
            return busy_times
        except Exception as e:
            print(f"Google Calendar hatası: {e}")
            return []
    
    async def get_microsoft_freebusy(self, email: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Microsoft Graph'tan FreeBusy bilgilerini al"""
        if not self.microsoft_token:
            await self.authenticate_microsoft()
        
        headers = {
            'Authorization': f'Bearer {self.microsoft_token}',
            'Content-Type': 'application/json'
        }
        
        body = {
            "schedules": [email],
            "startTime": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC"
            },
            "endTime": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC"
            }
        }
        
        try:
            response = requests.post(
                'https://graph.microsoft.com/v1.0/me/calendar/getSchedule',
                headers=headers,
                json=body
            )
            
            if response.status_code == 200:
                data = response.json()
                busy_times = []
                for schedule in data.get('value', []):
                    for event in schedule.get('busyViewEntries', []):
                        if event.get('status') == 'busy':
                            busy_times.append({
                                'start': event.get('start'),
                                'end': event.get('end')
                            })
                return busy_times
            return []
        except Exception as e:
            print(f"Microsoft Graph hatası: {e}")
            return []
    
    def parse_working_hours(self, date: datetime) -> Tuple[datetime, datetime]:
        """Çalışma saatlerini hesapla"""
        start_hour, start_minute = map(int, WORKING_HOURS['start'].split(':'))
        end_hour, end_minute = map(int, WORKING_HOURS['end'].split(':'))
        
        work_start = date.replace(hour=start_hour, minute=start_minute, second=0)
        work_end = date.replace(hour=end_hour, minute=end_minute, second=0)
        
        return work_start, work_end
    
    def get_lunch_break(self, date: datetime) -> Tuple[datetime, datetime]:
        """Öğle arası saatlerini hesapla"""
        lunch_start_hour, lunch_start_minute = map(int, WORKING_HOURS['lunch_start'].split(':'))
        lunch_end_hour, lunch_end_minute = map(int, WORKING_HOURS['lunch_end'].split(':'))
        
        lunch_start = date.replace(hour=lunch_start_hour, minute=lunch_start_minute, second=0)
        lunch_end = date.replace(hour=lunch_end_hour, minute=lunch_end_minute, second=0)
        
        return lunch_start, lunch_end
    
    def find_available_slots(self, busy_times: List[Dict], date: datetime, duration_minutes: int) -> List[Dict]:
        """Müsait zaman dilimlerini bul"""
        work_start, work_end = self.parse_working_hours(date)
        lunch_start, lunch_end = self.get_lunch_break(date)
        
        # Meşgul zamanları datetime'a çevir
        busy_periods = []
        for busy in busy_times:
            start = datetime.fromisoformat(busy['start'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(busy['end'].replace('Z', '+00:00'))
            busy_periods.append((start, end))
        
        # Öğle arasını da meşgul zaman olarak ekle
        busy_periods.append((lunch_start, lunch_end))
        
        # Meşgul zamanları sırala
        busy_periods.sort(key=lambda x: x[0])
        
        available_slots = []
        current_time = work_start
        
        for busy_start, busy_end in busy_periods:
            # Mevcut zaman ile meşgul başlangıç arasında yer var mı?
            if current_time < busy_start:
                slot_duration = (busy_start - current_time).total_seconds() / 60
                if slot_duration >= duration_minutes:
                    available_slots.append({
                        'start': current_time,
                        'end': current_time + timedelta(minutes=duration_minutes),
                        'duration': duration_minutes
                    })
            
            # Meşgul zamanın sonundan devam et
            current_time = max(current_time, busy_end)
        
        # Son meşgul zamandan iş bitişine kadar yer var mı?
        if current_time < work_end:
            slot_duration = (work_end - current_time).total_seconds() / 60
            if slot_duration >= duration_minutes:
                available_slots.append({
                    'start': current_time,
                    'end': current_time + timedelta(minutes=duration_minutes),
                    'duration': duration_minutes
                })
        
        return available_slots
    
    def calculate_availability_score(self, slot: Dict, all_participants_availability: List[List[Dict]]) -> float:
        """Zaman diliminin uygunluk puanını hesapla"""
        slot_start = slot['start']
        slot_end = slot['end']
        
        # Saat dilimi tercihi (10-11 arası ve 14-16 arası en iyi)
        hour = slot_start.hour
        time_score = 1.0
        if 10 <= hour <= 11 or 14 <= hour <= 16:
            time_score = 1.0
        elif 9 <= hour <= 10 or 11 <= hour <= 12 or 16 <= hour <= 17:
            time_score = 0.8
        else:
            time_score = 0.6
        
        # Tüm katılımcılar için uygunluk kontrolü
        participant_score = 1.0
        for participant_slots in all_participants_availability:
            participant_available = any(
                ps['start'] <= slot_start and ps['end'] >= slot_end 
                for ps in participant_slots
            )
            if not participant_available:
                participant_score = 0.0
                break
        
        return time_score * participant_score
    
    async def check_availability(self, participants: List[str], date: str, duration_minutes: int) -> List[Dict]:
        """Ana fonksiyon: Katılımcıların müsaitlik durumunu kontrol et"""
        try:
            meeting_date = datetime.fromisoformat(date)
            start_time = meeting_date.replace(hour=0, minute=0, second=0)
            end_time = meeting_date.replace(hour=23, minute=59, second=59)
            
            all_busy_times = []
            all_available_slots = []
            
            # Her katılımcı için müsaitlik durumunu kontrol et
            for email in participants:
                busy_times = []
                
                # Email adresine göre provider'ı belirle
                if 'gmail.com' in email or 'googlemail.com' in email:
                    busy_times = await self.get_google_freebusy(email, start_time, end_time)
                elif 'outlook.com' in email or 'hotmail.com' in email or 'live.com' in email:
                    busy_times = await self.get_microsoft_freebusy(email, start_time, end_time)
                
                # Müsait slotları bul
                available_slots = self.find_available_slots(busy_times, meeting_date, duration_minutes)
                all_available_slots.append(available_slots)
                all_busy_times.extend(busy_times)
            
            # Ortak müsait zamanları bul
            if not all_available_slots:
                return []
            
            common_slots = all_available_slots[0]
            for participant_slots in all_available_slots[1:]:
                common_slots = [
                    slot for slot in common_slots
                    if any(
                        ps['start'] <= slot['start'] and ps['end'] >= slot['end']
                        for ps in participant_slots
                    )
                ]
            
            # Puanlama ve sıralama
            scored_slots = []
            for slot in common_slots:
                score = self.calculate_availability_score(slot, all_available_slots)
                scored_slots.append({
                    'start': slot['start'].strftime('%H:%M'),
                    'end': slot['end'].strftime('%H:%M'),
                    'date': meeting_date.strftime('%Y-%m-%d'),
                    'duration': duration_minutes,
                    'score': score
                })
            
            # En yüksek puanlı 3 seçeneği döndür
            scored_slots.sort(key=lambda x: x['score'], reverse=True)
            return scored_slots[:3]
            
        except Exception as e:
            print(f"Müsaitlik kontrolü hatası: {e}")
            return []