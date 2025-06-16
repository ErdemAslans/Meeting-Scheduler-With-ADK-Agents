from google.adk.agents import Agent
import vertexai
from typing import Dict, List, Any
import asyncio
from datetime import datetime, timedelta
import re
import os
from agents.calendar_analyst import check_calendar_availability
from agents.email_composer import compose_meeting_invitation
from agents.email_sender import send_meeting_invitations

# Orchestrator Agent için Google ADK Agent tanımı
def create_orchestrator_agent():
    """Ana koordinatör agent'ı oluşturur"""
    
    calendar_analyst = Agent(
        name="calendar_analyst",
        model="gemini-1.5-flash",
        temperature=0.1,
        instruction="""Sen uzman bir takvim analistisin.
        - FreeBusy API kullanarak takvimleri sorgula
        - Çalışma saatleri: 09:00-18:00
        - Öğle arası: 12:00-13:00 (meşgul)
        - En uygun 3 zamanı öner
        - Puanlama kriterleri: sabah 10-11 ve öğleden sonra 14-16 arası yüksek puan
        
        Sen sadece takvim analizinden sorumlusun. Kullanıcıdan toplantı detayları istediğinde, 
        katılımcılar listesi, tarih ve süre bilgilerini topla.""",
        tools=[check_calendar_availability]
    )

    email_composer = Agent(
        name="email_composer", 
        model="gemini-1.5-flash",
        temperature=0.7,
        instruction="""Sen profesyonel e-posta yazarısın.
        - Kurumsal standartlarda davet hazırla
        - HTML ve plain text versiyonları oluştur
        - ICS takvim dosyası ekle
        - Türkçe ve İngilizce destek
        - Kişiselleştirilmiş içerik
        
        Sen sadece e-posta oluşturmaktan sorumlusun. Toplantı detayları verildikinde
        profesyonel ve açık davetiye metni hazırla.""",
        tools=[compose_meeting_invitation]
    )

    email_sender = Agent(
        name="email_sender",
        model="gemini-1.5-flash", 
        temperature=0.1,
        instruction="""Sen güvenilir e-posta gönderim uzmanısın.
        - SMTP üzerinden güvenli gönderim
        - Gmail ve Outlook desteği
        - Teslimat onayı takibi
        - Hata durumunda retry
        
        Sen sadece e-posta göndermekten sorumlusun. E-posta içeriği hazır olduğunda
        güvenli bir şekilde alıcılara ulaştır.""",
        tools=[send_meeting_invitations]
    )

    orchestrator = Agent(
        name="meeting_orchestrator",
        model="gemini-2.0-flash",
        temperature=0.3,
        instruction="""Sen akıllı toplantı planlama koordinatörüsün.
        
        Kullanıcı şöyle diyecek: "Ali (ali@gmail.com) ve Ayşe (ayse@outlook.com) ile yarın 1 saatlik toplantı ayarla"
        
        Adımlar:
        1. Komutu ayrıştır (katılımcılar, tarih, süre)
        2. Calendar Analyst'e yönlendir → müsait zamanları bul
        3. En uygun zamanı seç veya kullanıcıya sor
        4. Email Composer'a yönlendir → davet hazırla
        5. Email Sender'a yönlendir → gönder
        6. Sonucu bildir
        
        Doğal dil desteği:
        - "yarın", "pazartesi", "öğleden sonra" gibi ifadeleri anla
        - Türkçe ve İngilizce
        - Eksik bilgileri kibarca sor
        
        Önemli: Her adımı sırasıyla takip et ve diğer agent'lara uygun tool'ları kullanarak yönlendir.
        Kullanıcıya süreç boyunca bilgi ver.""",
        transfer_agents=[calendar_analyst, email_composer, email_sender]
    )
    
    return orchestrator

class MeetingOrchestrator:
    """Toplantı planlama orkestratörü"""
    
    def __init__(self):
        self.orchestrator_agent = create_orchestrator_agent()
        
    def parse_meeting_request(self, request: str) -> Dict:
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
        
        # Toplantı başlığını çıkar
        title = "Toplantı"
        
        # Ortak başlık kalıpları
        title_keywords = [
            'toplantı', 'meeting', 'görüşme', 'planlama', 'sprint', 
            'retrospektif', 'demo', 'sunum', 'değerlendirme'
        ]
        
        words = request.lower().split()
        for i, word in enumerate(words):
            if any(keyword in word for keyword in title_keywords):
                # Başlığı oluştur
                title_parts = []
                if i > 0:
                    title_parts.extend(words[max(0, i-2):i])
                title_parts.append(word)
                if i < len(words) - 1:
                    title_parts.extend(words[i+1:min(len(words), i+3)])
                
                title = ' '.join(title_parts).title()
                break
        
        # Konum
        location = "Online"
        if any(word in request.lower() for word in ['ofis', 'office', 'konferans', 'conference']):
            location = "Ofis"
        elif any(word in request.lower() for word in ['zoom', 'teams', 'meet', 'online']):
            location = "Online"
        
        return {
            'participants': participants,
            'participant_names': names,
            'date': meeting_date,
            'duration': duration,
            'title': title,
            'location': location,
            'organizer': os.getenv('SENDER_EMAIL', 'organizer@example.com'),
            'organizer_name': os.getenv('SENDER_NAME', 'Toplantı Organizatörü')
        }
    
    async def schedule_meeting_with_agent(self, request: str, language: str = 'tr') -> Dict:
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

# Standalone çalıştırma için
async def main():
    orchestrator = MeetingOrchestrator()
    await orchestrator.run_interactive_mode()

if __name__ == "__main__":
    # Vertex AI'yi başlat
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if project_id:
        vertexai.init(project=project_id, location="us-central1")
    
    # Gerekli çevre değişkenlerini kontrol et
    required_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD', 'GOOGLE_CLOUD_PROJECT']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Gerekli çevre değişkenleri eksik:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nÖrnek kullanım:")
        print("export SENDER_EMAIL='your-email@gmail.com'")
        print("export SENDER_PASSWORD='your-app-password'")
        print("export SENDER_NAME='Your Name'")
        print("export GOOGLE_CLOUD_PROJECT='your-project-id'")
        exit(1)
    
    asyncio.run(main())