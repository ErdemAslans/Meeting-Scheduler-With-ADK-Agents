#!/usr/bin/env python3
"""
Google ADK Meeting Scheduler Orchestrator
"""

import os
import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Any
from google.adk.agents import Agent
import vertexai

# Import tool functions from other agents
from .calendar_analyst import check_calendar_availability
from .email_composer import compose_meeting_invitation
from .email_sender import send_meeting_invitations

def create_orchestrator_agent():
    """Ana koordinatör agent'ı oluşturur"""
    
    # Ana orchestrator agent
    orchestrator = Agent(
        name="meeting_orchestrator",
        model="gemini-2.0-flash",
        description="🤖 AI-powered meeting scheduler - Akıllı toplantı planlama asistanı",
        instruction="""Sen gelişmiş bir toplantı planlama asistanısın!

GÖREVIN: Kullanıcı doğal dilde toplantı talep ettiğinde, end-to-end toplantı planlama sürecini yönet.

ÖRNEKLER:
- "Ali (ali@gmail.com) ile yarın 1 saatlik toplantı ayarla"
- "john@company.com ile pazartesi 30 dakikalık demo planla"
- "team@startup.com ile cuma 2 saatlik planlama toplantısı"

İŞ AKIŞIN:
1. 📝 Kullanıcı talebini ayrıştır:
   - Katılımcı e-postaları çıkar
   - Tarih belirle (yarın, pazartesi, vs.)
   - Süre hesapla (1 saat = 60 dakika)
   - Toplantı başlığını oluştur

2. 📅 check_calendar_availability tool'unu kullan:
   - Katılımcılar listesi, tarih, süre parametreleri
   - Müsait zamanları al ve skorla

3. ⏰ En uygun zamanı seç:
   - En yüksek skorlu zamanı tercih et
   - Alternatifleri de kullanıcıya sun

4. 📧 compose_meeting_invitation tool'unu kullan:
   - Toplantı detaylarını ve dili geç
   - Profesyonel davet hazırla

5. 📨 send_meeting_invitations tool'unu kullan:
   - E-posta içeriği ve alıcıları geç
   - Gönderim sonucunu raporla

6. ✅ Kullanıcıya özet rapor ver:
   - Seçilen tarih/saat
   - Gönderilen davetiye sayısı
   - Başarı durumu

ÖNEMLI:
- Her adımı sırasıyla takip et
- Tool'ları doğru parametrelerle çağır  
- Kullanıcıya her adımda bilgi ver
- Hatalar durumunda alternatifleri öner
- Türkçe ve İngilizce destekle

Örnek kullanıcı mesajı aldığında:
"Ali (ali@gmail.com) ve Ayşe (ayse@outlook.com) ile yarın 1 saatlik toplantı ayarla"

1. Katılımcıları tespit et: ["ali@gmail.com", "ayse@outlook.com"]
2. Tarihi hesapla: yarın = tomorrow
3. Süreyi belirle: 1 saat = 60 dakika
4. check_calendar_availability(participants=["ali@gmail.com", "ayse@outlook.com"], date="2025-06-17", duration_minutes=60)
5. En uygun zamanı seç ve compose_meeting_invitation çağır
6. send_meeting_invitations ile gönder
7. Kullanıcıya sonucu rapor et""",
        tools=[check_calendar_availability, compose_meeting_invitation, send_meeting_invitations]
    )
    
    return orchestrator

class MeetingOrchestrator:
    """Toplantı planlama orkestratörü"""
    
    def __init__(self):
        self.orchestrator_agent = create_orchestrator_agent()
        
    def parse_meeting_request(self, request: str) -> dict:
        """Doğal dil toplantı isteğini ayrıştır"""
        
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
        
        # Tarih ayrıştırma
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
        else:
            # Varsayılan: yarın
            meeting_date = (date_today + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Süre ayrıştırma
        duration = 60  # Varsayılan 1 saat
        
        # Saat/dakika ifadelerini yakala
        time_patterns = [
            r'(\d+)\s*saat',
            r'(\d+)\s*hour',
            r'(\d+)\s*dakika',
            r'(\d+)\s*minute',
            r'(\d+)\s*dk'
        ]
        
        for pattern in time_patterns:
            matches = re.findall(pattern, request.lower())
            if matches:
                time_value = int(matches[0])
                if 'saat' in pattern or 'hour' in pattern:
                    duration = time_value * 60
                else:
                    duration = time_value
                break
        
        return {
            'participants': participants,
            'participant_names': names,
            'date': meeting_date,
            'duration': duration,
            'title': "Toplantı",
            'location': "Online",
            'organizer': os.getenv('SENDER_EMAIL', 'organizer@example.com'),
            'organizer_name': os.getenv('SENDER_NAME', 'Toplantı Organizatörü')
        }
    
    async def schedule_meeting_with_agent(self, request: str, language: str = 'tr') -> dict:
        """Google ADK Agent kullanarak toplantı planla"""
        try:
            print("🤖 Orchestrator Agent çalışıyor...")
            
            # Toplantı isteğini ayrıştır
            meeting_info = self.parse_meeting_request(request)
            
            if not meeting_info['participants']:
                return {
                    'success': False,
                    'error': 'Katılımcı e-posta adresi bulunamadı'
                }
            
            # Agent'a gönderilecek mesaj
            agent_message = f"""
            Toplantı planlama isteği: {request}
            
            Ayrıştırılan bilgiler:
            - Katılımcılar: {', '.join(meeting_info['participants'])}
            - Tarih: {meeting_info['date']}
            - Süre: {meeting_info['duration']} dakika
            - Başlık: {meeting_info['title']}
            - Konum: {meeting_info['location']}
            - Dil: {language}
            
            Lütfen şu adımları takip et:
            1. Calendar Analyst ile müsait zamanları kontrol et
            2. En uygun zamanı belirle
            3. Email Composer ile davet hazırla
            4. Email Sender ile gönder
            5. Sonucu raporla
            """
            
            # Orchestrator agent'ını çalıştır
            response = await self.orchestrator_agent.run(agent_message)
            
            return {
                'success': True,
                'agent_response': response,
                'meeting_info': meeting_info,
                'message': 'Toplantı ADK Agent ile başarıyla işlendi'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"ADK Agent hatası: {str(e)}"
            }
    
    async def run_interactive_mode(self):
        """İnteraktif mod - Kullanıcı komutlarını dinle"""
        print("🤖 Google ADK Multi-Agent Toplantı Planlama Sistemi")
        print("=" * 60)
        print("Örnek: 'Ali (ali@gmail.com) ve Ayşe (ayse@outlook.com) ile yarın 1 saatlik toplantı ayarla'")
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
                print("🔄 Agent'lar çalışıyor...")
                
                result = await self.schedule_meeting_with_agent(request)
                
                if result['success']:
                    print(f"✅ {result['message']}")
                    print(f"🤖 Agent Yanıtı: {result['agent_response']}")
                else:
                    print(f"❌ Hata: {result['error']}")
                
                print("\n" + "="*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n👋 Görüşmek üzere!")
                break
            except Exception as e:
                print(f"❌ Beklenmeyen hata: {str(e)}")

# ADK Web için root agent - bu önemli!
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
    print("🚀 Meeting Scheduler Agent hazır!")
    print("📱 ADK Web başlatmak için: adk web")
    print("🌐 Browser'da: http://localhost:8000")