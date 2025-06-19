#!/usr/bin/env python3
"""
Google ADK Meeting Scheduler Orchestrator - UPDATED with Complete Calendar Integration
"""

import os
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Any, Optional
from google.adk.agents import Agent
import vertexai

# Import tool functions
from .calendar_analyst import check_calendar_availability, create_calendar_event
from .memory_manager import MemoryManager

# Global memory manager
global_memory = MemoryManager()

# Memory tool functions
def save_conversation_to_memory(user_input: str, agent_response: str, meeting_details: dict, success: bool, meeting_id: Optional[str] = None, calendar_event_id: Optional[str] = None) -> dict:
    """Konuşmayı memory'e kaydet - ADK Tool Function"""
    try:
        import os
        user_email = os.getenv('SENDER_EMAIL', 'organizer@example.com')
        
        # Meeting details'e calendar_event_id ekle
        if calendar_event_id:
            meeting_details['calendar_event_id'] = calendar_event_id
            meeting_details['organizer'] = user_email
        
        # Konuşmayı kaydet
        global_memory.add_conversation_turn(
            user_input=user_input,
            agent_response=agent_response,
            parsed_data=meeting_details,
            success=success,
            meeting_id=meeting_id
        )
        
        # Eğer toplantı başarılı ise meeting history'e de ekle
        if success and meeting_details.get('participants'):
            meeting_id = global_memory.add_meeting_to_history(meeting_details)
            
            # Frequent participants güncelle
            for participant in meeting_details.get('participants', []):
                global_memory.add_frequent_participant(user_email, participant)
        
        return {
            'success': True,
            'meeting_id': meeting_id,
            'message': '💾 Konuşma ve toplantı memory\'e kaydedildi'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def get_user_memory_insights() -> dict:
    """Kullanıcı memory insights getir - ADK Tool Function"""
    try:
        # SENDER_EMAIL'den organizatör email'ini al
        import os
        user_email = os.getenv('SENDER_EMAIL', 'organizer@example.com')
        
        profile = global_memory.get_or_create_user_profile(user_email)
        patterns = global_memory.analyze_user_patterns(user_email)
        
        return {
            'success': True,
            'user_email': user_email,
            'profile': {
                'email': profile.email,
                'total_meetings': profile.total_meetings_scheduled,
                'frequent_participants': profile.frequent_participants[:5],
                'preferred_duration': profile.preferred_meeting_duration,
                'preferred_times': profile.preferred_meeting_times
            },
            'patterns': patterns,
            'message': f'🧠 {user_email} için memory insights alındı'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def create_orchestrator_agent():
    """Ana koordinatör agent'ı oluşturur - UPDATED with Calendar Event Creation"""
    
    orchestrator = Agent(
        name="meeting_orchestrator",
        model="gemini-2.0-flash",
        description="🤖 MEMORY-ENHANCED AI Meeting Scheduler - GERÇEK Calendar API + Memory System",
        instruction="""Sen HAFIZA ve CONTEXT YÖNETİMİ olan akıllı toplantı planlama asistanısın!

🧠 HAFIZA ÖZELLİKLERİ:
- ✅ Kullanıcı tercihlerini hatırlar ve öğrenir
- ✅ Sık kullanılan katılımcıları bilir
- ✅ Geçmiş toplantı desenlerini analiz eder
- ✅ Konuşma geçmişini kaydeder

📅 CALENDAR ÖZELLİKLER:
- ✅ GERÇEK Google Calendar API ile müsaitlik kontrolü
- ✅ GERÇEK Calendar Event oluşturma
- ✅ Otomatik katılımcı davetleri
- ✅ Email + Calendar çifte entegrasyon

GÖREVIN: End-to-end TAMAMEN OTOMATİK toplantı planlama.

ÖRNEKLER:
- "Ali (ali@gmail.com) ile yarın 1 saatlik toplantı ayarla"
- "john@company.com ile pazartesi 30 dakikalık demo planla"
- "team@startup.com ile cuma 2 saatlik planlama toplantısı"

🔄 TAM İŞ AKIŞIN:
1. 🧠 Memory insights al:
   - get_user_memory_insights() tool'unu kullan (parametre yok)
   - Kullanıcının geçmiş tercihlerini öğren
   - Sık kullanılan katılımcıları tespit et
   - Memory'den öneriler al

2. 📝 ÖNEMLİ: Sana verilen ayrıştırılmış bilgileri AYNEN kullan:
   - Süre: Sana verilen dakika değerini DEĞİŞTİRME (30 dakika = 30, 15 dakika = 15)
   - Katılımcılar: Sana verilen email listesini kullan
   - Tarih: Sana verilen tarihi kullan
   - Başlık: Sana verilen başlığı kullan
   ⚠️ KULLANICIDAn TEKRAr PARSE ETME - Verilen bilgileri kullan!

3. 📅 check_calendar_availability tool'unu kullan:
   - GERÇEK Google Calendar API ile müsaitlik kontrol
   - Katılımcılar listesi, tarih, süre parametreleri
   - Gerçek busy time'ları al ve skorla
   ⚠️ ÖNEMLİ: Eğer 'calendar_access_warning' true ise, kullanıcıya şu uyarıyı ver:
   "UYARI: Bazı katılımcıların takvimleri özel olduğu için kontrol edilemedi. 
   Bu saatlerde çakışma olabilir. Lütfen katılımcılarla manuel onay alın."

4. ⏰ En uygun zamanı seç:
   - En yüksek skorlu zamanı tercih et
   - Kullanıcıya seçilen zamanı bildir
   - Eğer erişilemeyen takvimler varsa, uyarıyı tekrarla
   ⚠️ ÖNEMLİ: Eğer 'no_slots_available' true ise:
   "❌ Bu tarihte boş slot yok! Alternatif tarihler: [alternative_dates listesi]
   Başka bir tarih seçelim mi?" diye sor ve TOPLANTI OLUŞTURMA!

5. 📅 create_calendar_event tool'unu kullan:
   - GERÇEK Google Calendar Event oluştur
   - Katılımcıları otomatik davet et (Google Calendar daveti)
   - Reminder'ları ayarla
   - Event ID ve link al
   
   ⚠️ ÖNEMLİ: Calendar event oluştururken 'sendUpdates': 'all' ayarı
   katılımcılara otomatik Google Calendar daveti gönderir.
   Ayrı email daveti GEREKMEZ ve GÖNDERMEMEN gerekir!

6. 💾 save_conversation_to_memory tool'unu kullan:
   - user_input: Kullanıcının original isteği
   - agent_response: Senin yanıtın
   - meeting_details: Tüm toplantı bilgileri
   - success: true (eğer başarılı ise)
   - calendar_event_id: create_calendar_event'den aldığın event_id

7. ✅ TAMAMEN OTOMATİK SONUÇ:
   - ✓ Calendar event oluşturuldu
   - ✓ Katılımcılar otomatik Google Calendar daveti aldı
   - ✓ Reminder'lar ayarlandı
   - ✓ Meeting link'i paylaşıldı
   - ✓ Memory'e kaydedildi

🔧 TOOL SIRASI (ÖNEMLİ):
1. 🧠 get_user_memory_insights tool'unu MUTLAKA kullan:
   - İlk adım olarak memory'den benzer toplantıları kontrol et
   - Aynı katılımcılarla yakın tarihte toplantı var mı?
   - Kullanıcının tercih ettiği saat/süre nedir?
   - Sık kullandığı katılımcılar kimler?
   - Memory'den gelen önerileri kullanıcıya sun
   
2. check_calendar_availability (GERÇEK müsaitlik kontrol)
3. create_calendar_event (GERÇEK Calendar Event oluştur - otomatik davet gönderir)
4. save_conversation_to_memory (Memory'e kaydet)

⚠️ ARTIK KULLANMA:
- compose_meeting_invitation (Gereksiz - calendar zaten davet gönderiyor)
- send_meeting_invitations (Gereksiz - ikili email gönderir)

BAŞARI KRİTERLERİ:
- ✅ Calendar event oluşturulmalı
- ✅ Katılımcılar otomatik Google Calendar daveti almalı
- ✅ Event link paylaşılmalı
- ✅ Kullanıcıya tam rapor verilmeli
- ❌ Ayrı email daveti gönderilmemeli (ikili gönderim engellenir)

Örnek başarılı sonuç mesajı:
"✅ Toplantı başarıyla planlandı!
📅 Calendar Event: [Event ID]
🔗 Meeting Link: [Calendar Link]  
📧 Google Calendar daveti gönderildi: 2 katılımcı
⏰ Tarih/Saat: [Seçilen zaman]
🔔 Reminder'lar ayarlandı"

ÖNEMLI:
- Sadece gerekli tool'ları kullan (compose_meeting_invitation ve send_meeting_invitations KULLANMA)
- Calendar Event MUTLAKA oluşturulmalı
- Event ID ve calendar link'i mutlaka al ve raporla
- Google Calendar otomatik davet gönderir, ayrı email gönderme
- Türkçe ve İngilizce tam destek
- Her adımda kullanıcıya progress bilgisi ver

Örnek kullanıcı mesajı aldığında:
"Ali (ali@gmail.com) ve Ayşe (ayse@outlook.com) ile yarın 1 saatlik toplantı ayarla"

1. Katılımcıları tespit et: ["ali@gmail.com", "ayse@outlook.com"]
2. Tarihi hesapla: yarın = 2025-06-18
3. Süreyi belirle: 1 saat = 60 dakika
4. check_calendar_availability(participants=["ali@gmail.com", "ayse@outlook.com"], date="2025-06-18", duration_minutes=60)
5. En uygun zamanı seç (örn: 10:00-11:00)
6. create_calendar_event ile gerçek Calendar Event oluştur (otomatik Google Calendar daveti gönderir)
7. save_conversation_to_memory ile memory'e kaydet
8. Kullanıcıya event ID ve calendar link ile başarı raporu ver
""",
        tools=[
            check_calendar_availability, 
            create_calendar_event, 
            save_conversation_to_memory,
            get_user_memory_insights
        ]
    )
    
    return orchestrator

class MeetingOrchestrator:
    """Toplantı planlama orkestratörü - UPDATED with Memory & Context Management"""
    
    def __init__(self):
        self.orchestrator_agent = create_orchestrator_agent()
        self.memory_manager = MemoryManager()
        print("🧠 Memory Manager başlatıldı")
        
    def parse_meeting_request(self, request: str, user_email: str = None) -> dict:
        """Doğal dil toplantı isteğini ayrıştır - UPDATED with Memory Integration"""
        
        # Memory'den context önerileri al
        organizer_email = user_email or os.getenv('SENDER_EMAIL', 'organizer@example.com')
        suggestions = self.memory_manager.get_context_suggestions(request, organizer_email)
        
        # E-posta adreslerini bul
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, request)
        
        # İsim ve e-posta eşleştirmesi
        participants = []
        names = []
        
        # "Ali (ali@gmail.com)" formatını yakala
        name_email_pattern = r'(\w+)\s*\(([^)]+@[^)]+)\)'
        name_email_matches = re.findall(name_email_pattern, request, re.IGNORECASE)
        
        for name, email in name_email_matches:
            participants.append(email)
            names.append(name)
        
        # Diğer e-postaları da ekle
        for email in emails:
            if email not in participants:
                participants.append(email)
                names.append(email.split('@')[0])
        
        # Eğer katılımcı yok ama "Ali ile" gibi ifade varsa, memory'den öner
        if not participants:
            # "Ali ile", "John ile" gibi ifadeleri yakala
            name_pattern = r'(\w+)\s*ile|with\s+(\w+)'
            name_matches = re.findall(name_pattern, request, re.IGNORECASE)
            if name_matches:
                mentioned_name = name_matches[0][0] or name_matches[0][1]
                # Frequent participants'tan bu isimle eşleşen email bul
                for freq_email in suggestions.get('frequent_participants', []):
                    if mentioned_name.lower() in freq_email.lower():
                        participants.append(freq_email)
                        names.append(mentioned_name)
                        print(f"🧠 Memory'den önerildi: {mentioned_name} -> {freq_email}")
                        break
        
        # Tarih ayrıştırma - UPDATED
        date_today = datetime.now()
        meeting_date = None
        
        # Türkçe tarih ifadeleri
        if any(word in request.lower() for word in ['bugün', 'today']):
            meeting_date = date_today.strftime('%Y-%m-%d')
        elif any(word in request.lower() for word in ['yarın', 'tomorrow']):
            meeting_date = (date_today + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'pazartesi' in request.lower() or 'monday' in request.lower():
            days_ahead = 0 - date_today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            meeting_date = (date_today + timedelta(days_ahead)).strftime('%Y-%m-%d')
        elif 'salı' in request.lower() or 'tuesday' in request.lower():
            days_ahead = 1 - date_today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            meeting_date = (date_today + timedelta(days_ahead)).strftime('%Y-%m-%d')
        elif 'çarşamba' in request.lower() or 'wednesday' in request.lower():
            days_ahead = 2 - date_today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            meeting_date = (date_today + timedelta(days_ahead)).strftime('%Y-%m-%d')
        elif 'perşembe' in request.lower() or 'thursday' in request.lower():
            days_ahead = 3 - date_today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            meeting_date = (date_today + timedelta(days_ahead)).strftime('%Y-%m-%d')
        elif 'cuma' in request.lower() or 'friday' in request.lower():
            days_ahead = 4 - date_today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            meeting_date = (date_today + timedelta(days_ahead)).strftime('%Y-%m-%d')
        else:
            # Varsayılan: yarın
            meeting_date = (date_today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Süre ayrıştırma - UPDATED with Memory
        duration = suggestions.get('preferred_duration', 60)  # Memory'den varsayılan süre
        
        # Saat/dakika ifadelerini yakala - GELİŞTİRİLMİŞ
        time_patterns = [
            (r'(\d+)\s*saat', 'hour'),
            (r'(\d+)\s*hour', 'hour'),
            (r'(\d+)\s*saatlik', 'hour'),
            (r'(\d+)\s*h', 'hour'),
            (r'(\d+)\s*dakika', 'minute'),
            (r'(\d+)\s*dakikalık', 'minute'),
            (r'(\d+)\s*minute', 'minute'),
            (r'(\d+)\s*dk', 'minute'),
            (r'(\d+)\s*min', 'minute'),
            (r'(\d+)\s*m', 'minute'),
            # Özel durumlar
            (r'yarım\s*saat', 'half_hour'),
            (r'çeyrek\s*saat', 'quarter_hour'),
            (r'bir\s*saat', 'one_hour'),
            (r'iki\s*saat', 'two_hour')
        ]
        
        for pattern, unit in time_patterns:
            matches = re.findall(pattern, request.lower())
            if matches or unit in ['half_hour', 'quarter_hour', 'one_hour', 'two_hour']:
                if unit == 'hour':
                    duration = int(matches[0]) * 60
                elif unit == 'minute':
                    duration = int(matches[0])
                elif unit == 'half_hour':
                    duration = 30
                elif unit == 'quarter_hour':
                    duration = 15
                elif unit == 'one_hour':
                    duration = 60
                elif unit == 'two_hour':
                    duration = 120
                print(f"🔍 Süre tespit edildi: {duration} dakika ('{pattern}' pattern'i ile)")
                break
        
        # Saat ayrıştırma - UPDATED
        start_time = "10:00"  # Varsayılan
        
        # Saat formatlarını yakala
        time_patterns = [
            r'(\d{1,2}):(\d{2})',          # 14:30, 9:15
            r'(\d{1,2})\.(\d{2})',         # 14.30, 9.15
            r'saat\s+(\d{1,2}):(\d{2})',   # saat 14:30
            r'(\d{1,2})\s*:\s*(\d{2})',    # 14 : 30
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, request.lower())
            if matches:
                hour, minute = matches[0]
                start_time = f"{int(hour):02d}:{int(minute):02d}"
                print(f"🕒 Saat tespit edildi: {start_time}")
                break
        
        # Toplantı başlığı oluştur
        if len(names) > 0:
            if len(names) == 1:
                title = f"{names[0]} ile Toplantı"
            elif len(names) == 2:
                title = f"{names[0]} ve {names[1]} ile Toplantı"
            else:
                title = f"{names[0]} ve {len(names)-1} kişi ile Toplantı"
        else:
            title = "Toplantı"
        
        # Memory context güncelle
        self.memory_manager.update_context('last_parsed_request', request)
        self.memory_manager.update_context('suggested_participants', suggestions.get('frequent_participants', []))
        
        return {
            'participants': participants,
            'participant_names': names,
            'date': meeting_date,
            'start_time': start_time,
            'duration': duration,
            'title': title,
            'location': "Online",
            'organizer': organizer_email,
            'organizer_name': os.getenv('SENDER_NAME', 'Toplantı Organizatörü'),
            'subject': title,
            'memory_suggestions': suggestions,
            'user_email': organizer_email
        }
    
    async def schedule_meeting_with_agent(self, request: str, language: str = 'tr', user_email: str = None) -> dict:
        """Google Direct Calendar API ile COMPLETE toplantı planla - Spesifik zaman kontrolü ile"""
        try:
            # Başlangıç logları ve memory insights
            print("🤖 DIRECT CALENDAR Orchestrator çalışıyor.")
            organizer_email = user_email or os.getenv('SENDER_EMAIL', 'organizer@example.com')
            user_profile = self.memory_manager.get_or_create_user_profile(organizer_email)
            if user_profile.frequent_participants:
                print(f"🧠 Sık katılımcılar: {', '.join(user_profile.frequent_participants[:3])}")

            # İstek ayrıştırma
            meeting_info = self.parse_meeting_request(request, organizer_email)
            if not meeting_info.get('participants'):
                return {'success': False, 'error': 'Katılımcı e-posta adresi bulunamadı.'}

            # 1. Kullanıcının istediği spesifik zaman aralığını kontrol et
            import datetime, pytz
            from .calendar_analyst import oauth_service
            turkey_tz = pytz.timezone('Europe/Istanbul')
            start_str = f"{meeting_info['date']} {meeting_info.get('start_time', '10:00')}"
            requested_start = turkey_tz.localize(
                datetime.datetime.strptime(start_str, '%Y-%m-%d %H:%M')
            )
            requested_end = requested_start + datetime.timedelta(minutes=meeting_info['duration'])

            print(f"🕒 İstenen zaman: {requested_start.strftime('%Y-%m-%d %H:%M')} - {requested_end.strftime('%H:%M')} ({meeting_info['duration']} dakika)")

            fb_query = {
                'timeMin': requested_start.isoformat(),
                'timeMax': requested_end.isoformat(),
                'timeZone': 'Europe/Istanbul',
                'items': [{'id': email} for email in meeting_info['participants']]
            }
            fb_result = oauth_service.service.freebusy().query(body=fb_query).execute()
            busy_times = any(
                len(calendars.get('busy', [])) > 0 for calendars in fb_result.get('calendars', {}).values()
            )
            
            if busy_times:
                # Takvim doluysa, kullanıcıdan yeni tarih/saat iste
                return {
                    'success': False,
                    'error': (
                        f"⚠️ Seçtiğin {requested_start.strftime('%Y-%m-%d %H:%M')} — "
                        f"{requested_end.strftime('%H:%M')} arası dolu. Lütfen başka bir tarih veya saat belirt.")
                }

            # 2. Önce kullanıcıya detayları göster - ONAY İSTE
            meeting_summary = f"""
📅 **TOPLANTI DETAYLARI - ONAY GEREKLİ**

📋 **Başlık**: {meeting_info['title']}
👥 **Katılımcılar**: {', '.join(meeting_info['participants'])}
📅 **Tarih**: {requested_start.strftime('%d %B %Y')} ({requested_start.strftime('%A')})
🕒 **Saat**: {requested_start.strftime('%H:%M')} - {requested_end.strftime('%H:%M')}
⏱️ **Süre**: {meeting_info['duration']} dakika
🌍 **Zaman Dilimi**: Europe/Istanbul
📍 **Konum**: {meeting_info.get('location', 'Online')}

✅ **Bu bilgiler doğru mu? Toplantıyı oluşturayım mı?**

💡 Değişiklik yapmak istersen: "Hayır, saat 14:00'da olsun" veya "Süreyi 30 dakika yap" diyebilirsin.
✅ Onaylamak için: "Evet", "Tamam", "Oluştur" diyebilirsin.
"""

            return {
                'success': True,
                'needs_confirmation': True,
                'meeting_details': meeting_info,
                'requested_start': requested_start.isoformat(),
                'requested_end': requested_end.isoformat(),
                'message': meeting_summary,
                'confirmation_data': {
                    'organizer': organizer_email,
                    'start_datetime': requested_start.isoformat(),
                    'end_datetime': requested_end.isoformat(),
                    'participants': meeting_info['participants'],
                    'title': meeting_info['title'],
                    'duration': meeting_info['duration'],
                    'location': meeting_info.get('location', 'Online')
                }
            }
            
        except Exception as e:
            # Hata durumunda da memory'e kaydet
            self.memory_manager.add_conversation_turn(
                user_input=request,
                agent_response=f"Hata: {str(e)}",
                parsed_data={},
                success=False
            )
            
            return {
                'success': False,
                'error': f"MEMORY-ENHANCED ADK Agent hatası: {str(e)}"
            }
    
    async def confirm_and_create_meeting(self, confirmation_data: dict, user_email: str = None) -> dict:
        """Onaylanan toplantıyı oluştur"""
        try:
            print("✅ Toplantı onaylandı - Oluşturuluyor...")
            
            from .calendar_analyst import create_calendar_event
            
            # Event oluştur
            event_resp = create_calendar_event(confirmation_data)
            
            if event_resp.get('success'):
                # Memory'e kaydet
                meeting_id = self.memory_manager.add_meeting_to_history(confirmation_data)
                self.memory_manager.add_conversation_turn(
                    user_input=f"Toplantı onaylandı: {confirmation_data['title']}",
                    agent_response=f"✅ Toplantı başarıyla oluşturuldu!",
                    parsed_data=confirmation_data,
                    success=True,
                    meeting_id=meeting_id
                )
                
                return {
                    'success': True,
                    'meeting_id': meeting_id,
                    'event_id': event_resp.get('event_id'),
                    'event_link': event_resp.get('event_link'),
                    'message': (
                        f"✅ Toplantı başarıyla oluşturuldu!\n"
                        f"📅 Event ID: {event_resp.get('event_id')}\n"
                        f"🔗 Meeting Link: {event_resp.get('event_link')}\n"
                        f"📧 Google Calendar daveti gönderildi: {len(confirmation_data['participants'])} katılımcı\n"
                        f"⏰ Tarih/Saat: {confirmation_data['start_datetime'][:16]} - {confirmation_data['end_datetime'][11:16]}\n"
                        f"🔔 Reminder'lar ayarlandı"
                    ),
                    'agent_response': event_resp.get('message', 'Toplantı başarıyla oluşturuldu.')
                }
            else:
                return {
                    'success': False,
                    'error': event_resp.get('error', 'Takvim etkinliği oluşturulurken bir hata oluştu.')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Toplantı oluşturma hatası: {str(e)}"
            }
    
    async def run_interactive_mode(self):
        """İnteraktif mod - UPDATED with Memory & Context Management"""
        print("🤖 MEMORY-ENHANCED Google ADK Multi-Agent Meeting Scheduler")
        print("🧠 YENİ: Memory & Context Management!")
        print("📅 YENİ: GERÇEK Calendar Event Oluşturma!")
        print("=" * 75)
        print("Artık sizi hatırlıyor ve öğreniyor! 🎉")
        print()
        
        # Memory istatistikleri göster
        organizer_email = os.getenv('SENDER_EMAIL', 'user@example.com')
        user_stats = self.memory_manager.get_user_stats(organizer_email)
        if user_stats.get('total_meetings', 0) > 0:
            print(f"📊 Profiliniz: {user_stats['total_meetings']} toplantı, {user_stats['recent_meetings_count']} son 30 gün")
            if user_stats.get('frequent_participants'):
                print(f"👥 Sık çalıştığınız kişiler: {', '.join(user_stats['frequent_participants'][:3])}")
            print()
        
        print("💡 Özellikler:")
        print("   • 🧠 Sık kullandığınız katılımcıları hatırlar")
        print("   • ⏰ Tercih ettiğiniz toplantı saatlerini öğrenir")
        print("   • 📝 Geçmiş konuşmaları kaydeder")
        print("   • 💾 Tüm toplantı geçmişinizi tutar")
        print()
        print("Örnek: 'Ali ile yarın toplantı ayarla' (email hatırlanır)")
        print("Sonuç: ✅ Memory + ✅ Calendar Event + ✅ Email Davet")
        print("Çıkmak için 'exit', geçmişi görmek için 'history' yazın.")
        print()
        
        while True:
            try:
                request = input("📝 Toplantı isteğinizi yazın: ").strip()
                
                if request.lower() in ['exit', 'quit', 'çıkış']:
                    print("👋 Görüşmek üzere!")
                    print("💾 Tüm hafıza kaydedildi.")
                    break
                
                # Özel komutlar
                if request.lower() == 'history':
                    print("\n📜 Konuşma Geçmişi:")
                    print(self.memory_manager.get_conversation_summary(10))
                    print()
                    continue
                    
                if request.lower() == 'stats':
                    user_stats = self.memory_manager.get_user_stats(organizer_email)
                    print(f"\n📊 İstatistikleriniz:")
                    print(f"   Toplam toplantı: {user_stats.get('total_meetings', 0)}")
                    print(f"   Son 30 gün: {user_stats.get('recent_meetings_count', 0)}")
                    print(f"   Sık katılımcılar: {', '.join(user_stats.get('frequent_participants', [])[:5])}")
                    print()
                    continue
                
                if not request:
                    continue
                
                print()
                print("🔄 MEMORY-ENHANCED Agent'lar çalışıyor...")
                print("🧠 Memory & Context aktif...")
                print("📅 Calendar API + Event Creation...")
                
                result = await self.schedule_meeting_with_agent(request, user_email=organizer_email)
                
                if result['success']:
                    print(f"✅ {result['message']}")
                    print("🧠 Memory özellikler:")
                    for feature in result.get('features', []):
                        print(f"   {feature}")
                    
                    if result.get('meeting_id'):
                        print(f"💾 Meeting ID: {result['meeting_id']}")
                    
                    print(f"\n🤖 Agent Yanıtı:\n{result['agent_response']}")
                else:
                    print(f"❌ Hata: {result['error']}")
                
                print("\n" + "="*75 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Görüşmek üzere!")
                break
            except Exception as e:
                print(f"❌ Beklenmeyen hata: {str(e)}")

# ADK Web için root agent - UPDATED
root_agent = create_orchestrator_agent()

# Vertex AI başlatma
def setup_vertexai():
    """Vertex AI'yi başlat"""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'meeting-agent-463411')
    try:
        vertexai.init(project=project_id, location='us-central1')
        print(f"✅ Vertex AI başlatıldı - Project: {project_id}")
        return True
    except Exception as e:
        print(f"❌ Vertex AI başlatma hatası: {e}")
        return False

# ADK Web için otomatik setup
if __name__ == "__main__":
    setup_vertexai()
    print("🚀 COMPLETE Meeting Scheduler Agent hazır!")
    print("📱 ADK Web başlatmak için: adk web")
    print("🌐 Browser'da: http://localhost:8000")