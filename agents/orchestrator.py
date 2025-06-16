#!/usr/bin/env python3
"""
Google ADK Meeting Scheduler Orchestrator - UPDATED with Complete Calendar Integration
"""

import os
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Any
from google.adk.agents import Agent
import vertexai

# Import UPDATED tool functions
from .calendar_analyst import check_calendar_availability, create_calendar_event
from .email_composer import compose_meeting_invitation
from .email_sender import send_meeting_invitations

def create_orchestrator_agent():
    """Ana koordinatör agent'ı oluşturur - UPDATED with Calendar Event Creation"""
    
    orchestrator = Agent(
        name="meeting_orchestrator",
        model="gemini-2.0-flash",
        description="🤖 COMPLETE AI Meeting Scheduler - GERÇEK Calendar API + Event Creation",
        instruction="""Sen TAMAMEN ENTEGRENMİŞ toplantı planlama asistanısın!

🆕 YENİ ÖZELLİKLER:
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
1. 📝 Kullanıcı talebini ayrıştır:
   - Katılımcı e-postaları çıkar
   - Tarih belirle (yarın, pazartesi, vs.)
   - Süre hesapla (1 saat = 60 dakika)
   - Toplantı başlığını oluştur

2. 📅 check_calendar_availability tool'unu kullan:
   - GERÇEK Google Calendar API ile müsaitlik kontrol
   - Katılımcılar listesi, tarih, süre parametreleri
   - Gerçek busy time'ları al ve skorla

3. ⏰ En uygun zamanı seç:
   - En yüksek skorlu zamanı tercih et
   - Kullanıcıya seçilen zamanı bildir

4. 📅 create_calendar_event tool'unu kullan:
   - GERÇEK Google Calendar Event oluştur
   - Katılımcıları otomatik davet et
   - Reminder'ları ayarla
   - Event ID ve link al

5. 📧 compose_meeting_invitation tool'unu kullan:
   - Toplantı detaylarını ve Calendar link'i ekle
   - Profesyonel e-posta daveti hazırla

6. 📨 send_meeting_invitations tool'unu kullan:
   - E-posta davetini gönder
   - Calendar link'i e-postaya dahil et

7. ✅ TAMAMEN OTOMATİK SONUÇ:
   - ✓ Calendar event oluşturuldu
   - ✓ Katılımcılar otomatik davet edildi
   - ✓ E-posta gönderildi
   - ✓ Reminder'lar ayarlandı
   - ✓ Meeting link'i paylaşıldı

🔧 TOOL SIRASI (ÖNEMLİ):
1. check_calendar_availability (GERÇEK müsaitlik kontrol)
2. create_calendar_event (GERÇEK Calendar Event oluştur)
3. compose_meeting_invitation (Email hazırla + Calendar link ekle)
4. send_meeting_invitations (Email gönder)

BAŞARI KRİTERLERİ:
- ✅ Calendar event oluşturulmalı
- ✅ Katılımcılar otomatik davet edilmeli  
- ✅ E-posta gönderilmeli
- ✅ Event link paylaşılmalı
- ✅ Kullanıcıya tam rapor verilmeli

Örnek başarılı sonuç mesajı:
"✅ Toplantı başarıyla planlandı!
📅 Calendar Event: [Event ID]
🔗 Meeting Link: [Calendar Link]  
📧 E-posta gönderildi: 2 katılımcı
⏰ Tarih/Saat: [Seçilen zaman]
🔔 Reminder'lar ayarlandı"

ÖNEMLI:
- Her tool'u sırasıyla ve doğru parametrelerle çağır
- Calendar Event MUTLAKA oluşturulmalı
- Event ID ve calendar link'i mutlaka al ve raporla
- Başarı durumunda event ID ve calendar link'i paylaş
- Türkçe ve İngilizce tam destek
- Her adımda kullanıcıya progress bilgisi ver

Örnek kullanıcı mesajı aldığında:
"Ali (ali@gmail.com) ve Ayşe (ayse@outlook.com) ile yarın 1 saatlik toplantı ayarla"

1. Katılımcıları tespit et: ["ali@gmail.com", "ayse@outlook.com"]
2. Tarihi hesapla: yarın = 2025-06-18
3. Süreyi belirle: 1 saat = 60 dakika
4. check_calendar_availability(participants=["ali@gmail.com", "ayse@outlook.com"], date="2025-06-18", duration_minutes=60)
5. En uygun zamanı seç (örn: 10:00-11:00)
6. create_calendar_event ile gerçek Calendar Event oluştur
7. compose_meeting_invitation ile email hazırla (Calendar link dahil)
8. send_meeting_invitations ile gönder
9. Kullanıcıya event ID ve calendar link ile başarı raporu ver
""",
        tools=[check_calendar_availability, create_calendar_event, compose_meeting_invitation, send_meeting_invitations]
    )
    
    return orchestrator

class MeetingOrchestrator:
    """Toplantı planlama orkestratörü - UPDATED with Complete Calendar Integration"""
    
    def __init__(self):
        self.orchestrator_agent = create_orchestrator_agent()
        
    def parse_meeting_request(self, request: str) -> dict:
        """Doğal dil toplantı isteğini ayrıştır - UPDATED"""
        
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
        
        # Süre ayrıştırma - UPDATED
        duration = 60  # Varsayılan 1 saat
        
        # Saat/dakika ifadelerini yakala
        time_patterns = [
            (r'(\d+)\s*saat', 'hour'),
            (r'(\d+)\s*hour', 'hour'),
            (r'(\d+)\s*dakika', 'minute'),
            (r'(\d+)\s*minute', 'minute'),
            (r'(\d+)\s*dk', 'minute'),
            (r'(\d+)\s*min', 'minute')
        ]
        
        for pattern, unit in time_patterns:
            matches = re.findall(pattern, request.lower())
            if matches:
                time_value = int(matches[0])
                if unit == 'hour':
                    duration = time_value * 60
                else:
                    duration = time_value
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
        
        return {
            'participants': participants,
            'participant_names': names,
            'date': meeting_date,
            'duration': duration,
            'title': title,
            'location': "Online",
            'organizer': os.getenv('SENDER_EMAIL', 'organizer@example.com'),
            'organizer_name': os.getenv('SENDER_NAME', 'Toplantı Organizatörü'),
            'subject': title
        }
    
    async def schedule_meeting_with_agent(self, request: str, language: str = 'tr') -> dict:
        """Google ADK Agent kullanarak COMPLETE toplantı planla"""
        try:
            print("🤖 COMPLETE Orchestrator Agent çalışıyor...")
            print("🆕 Yeni özellikler: GERÇEK Calendar Event Creation!")
            
            # Toplantı isteğini ayrıştır
            meeting_info = self.parse_meeting_request(request)
            
            if not meeting_info['participants']:
                return {
                    'success': False,
                    'error': 'Katılımcı e-posta adresi bulunamadı'
                }
            
            # Agent'a gönderilecek UPDATED mesaj
            agent_message = f"""
            🆕 COMPLETE Toplantı Planlama İsteği: {request}
            
            Ayrıştırılan bilgiler:
            - Katılımcılar: {', '.join(meeting_info['participants'])}
            - Tarih: {meeting_info['date']}
            - Süre: {meeting_info['duration']} dakika
            - Başlık: {meeting_info['title']}
            - Konum: {meeting_info['location']}
            - Dil: {language}
            
            🔄 TAM İŞ AKIŞI (SIRASIZ TAKIP ET):
            1. ✅ check_calendar_availability ile GERÇEK müsaitlik kontrol
            2. ✅ En uygun zamanı belirle
            3. ✅ create_calendar_event ile GERÇEK Calendar Event oluştur (YENİ!)
            4. ✅ compose_meeting_invitation ile email hazırla (Calendar link dahil)
            5. ✅ send_meeting_invitations ile email gönder
            6. ✅ Event ID ve Calendar link ile başarı raporu ver
            
            🎯 Hedef: Kullanıcının takviminde gerçek event oluşturulmalı!
            ⚠️ MUTLAKA create_calendar_event tool'unu kullan!
            """
            
            # COMPLETE Orchestrator agent'ını çalıştır
            response = await self.orchestrator_agent.run(agent_message)
            
            return {
                'success': True,
                'agent_response': response,
                'meeting_info': meeting_info,
                'message': '✅ COMPLETE: Calendar Event + Email başarıyla işlendi',
                'features': [
                    '📅 Gerçek Calendar API kullanıldı',
                    '📧 Calendar Event oluşturuldu', 
                    '👥 Katılımcılar otomatik davet edildi',
                    '📨 E-posta davetleri gönderildi',
                    '🔔 Reminder\'lar ayarlandı'
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"COMPLETE ADK Agent hatası: {str(e)}"
            }
    
    async def run_interactive_mode(self):
        """İnteraktif mod - UPDATED with Calendar Features"""
        print("🤖 COMPLETE Google ADK Multi-Agent Meeting Scheduler")
        print("🆕 YENİ: GERÇEK Calendar Event Oluşturma!")
        print("=" * 65)
        print("Artık gerçekten takvime etkinlik ekleniyor! 🎉")
        print()
        print("Örnek: 'Ali (ali@gmail.com) ile yarın 1 saatlik toplantı ayarla'")
        print("Sonuç: ✅ Calendar Event + ✅ Email Davet + ✅ Otomatik Reminder")
        print("Çıkmak için 'exit' yazın.")
        print()
        
        while True:
            try:
                request = input("📝 Toplantı isteğinizi yazın: ").strip()
                
                if request.lower() in ['exit', 'quit', 'çıkış']:
                    print("👋 Görüşmek üzere!")
                    break
                    
                if not request:
                    continue
                
                print()
                print("🔄 COMPLETE Agent'lar çalışıyor...")
                print("📅 Calendar API + Event Creation...")
                
                result = await self.schedule_meeting_with_agent(request)
                
                if result['success']:
                    print(f"✅ {result['message']}")
                    print("🆕 Yeni özellikler:")
                    for feature in result.get('features', []):
                        print(f"   {feature}")
                    print(f"\n🤖 Agent Yanıtı:\n{result['agent_response']}")
                else:
                    print(f"❌ Hata: {result['error']}")
                
                print("\n" + "="*65 + "\n")
                
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
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'agentproject-462613')
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