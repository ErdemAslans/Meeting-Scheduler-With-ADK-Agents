import asyncio
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from agents import CalendarAnalyst, EmailComposer, EmailSender
from agents.orchestrator import MeetingOrchestrator
from google.adk.agents import Agent
from vertexai.preview.reasoning_engines import AdkApp
import vertexai
import os

class MeetingScheduler:
    """Klasik toplantı planlama sistemi (Google ADK olmadan)"""
    def __init__(self):
        self.calendar_analyst = CalendarAnalyst()
        self.email_composer = EmailComposer()
        self.email_sender = EmailSender()
        
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
    
    async def schedule_meeting(self, request: str, language: str = 'tr') -> Dict:
        """Ana toplantı planlama fonksiyonu"""
        try:
            print("🔍 Toplantı isteği ayrıştırılıyor...")
            
            # İsteği ayrıştır
            meeting_info = self.parse_meeting_request(request)
            
            if not meeting_info['participants']:
                return {
                    'success': False,
                    'error': 'Katılımcı e-posta adresi bulunamadı'
                }
            
            print(f"📅 {len(meeting_info['participants'])} katılımcının takvimi kontrol ediliyor...")
            
            # Müsaitlik kontrolü
            available_slots = await self.calendar_analyst.check_availability(
                meeting_info['participants'],
                meeting_info['date'],
                meeting_info['duration']
            )
            
            if not available_slots:
                return {
                    'success': False,
                    'error': 'Tüm katılımcılar için müsait zaman bulunamadı'
                }
            
            # En uygun zamanı seç (en yüksek puanlı)
            best_slot = available_slots[0]
            
            print(f"⏰ En uygun saat bulundu: {best_slot['start']}-{best_slot['end']}")
            
            # Toplantı detaylarını güncelle
            meeting_details = {
                **meeting_info,
                'start_time': best_slot['start'],
                'end_time': best_slot['end'],
                'date': best_slot['date']
            }
            
            print("📧 Davet e-postaları hazırlanıyor...")
            
            # E-posta davetini oluştur
            email_content = self.email_composer.compose_invitation(meeting_details, language)
            
            if not email_content['success']:
                return {
                    'success': False,
                    'error': email_content['error']
                }
            
            print("📨 E-postalar gönderiliyor...")
            
            # E-postaları gönder
            send_result = self.email_sender.send_email(email_content)
            
            if send_result['success']:
                print("✅ Toplantı başarıyla planlandı!")
                
                return {
                    'success': True,
                    'meeting_details': meeting_details,
                    'available_slots': available_slots,
                    'selected_slot': best_slot,
                    'email_result': send_result,
                    'message': f"Toplantı {best_slot['date']} {best_slot['start']}-{best_slot['end']} saatleri arasında planlandı. Davetler {send_result['sent_count']} katılımcıya gönderildi."
                }
            else:
                return {
                    'success': False,
                    'error': f"E-posta gönderimi başarısız: {send_result.get('error', 'Bilinmeyen hata')}",
                    'meeting_details': meeting_details
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Toplantı planlama hatası: {str(e)}"
            }
    
    def get_meeting_alternatives(self, request: str) -> Dict:
        """Alternatif toplantı zamanları öner"""
        try:
            meeting_info = self.parse_meeting_request(request)
            
            if not meeting_info['participants']:
                return {
                    'success': False,
                    'error': 'Katılımcı e-posta adresi bulunamadı'
                }
            
            # 3 gün için alternatif zamanlar bul
            alternatives = []
            base_date = datetime.fromisoformat(meeting_info['date'])
            
            for day_offset in range(3):
                check_date = (base_date + timedelta(days=day_offset)).strftime('%Y-%m-%d')
                
                # Bu fonksiyon async olmaması için sync wrapper kullanabiliriz
                # veya asyncio.run() ile çalıştırabiliriz
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    slots = loop.run_until_complete(
                        self.calendar_analyst.check_availability(
                            meeting_info['participants'],
                            check_date,
                            meeting_info['duration']
                        )
                    )
                    
                    if slots:
                        alternatives.extend(slots[:2])  # Her gün için en iyi 2 seçenek
                finally:
                    loop.close()
            
            return {
                'success': True,
                'alternatives': alternatives[:6],  # Toplam 6 alternatif
                'meeting_info': meeting_info
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Alternatif arama hatası: {str(e)}"
            }

# Google ADK App oluşturma
def create_adk_app():
    """Google ADK uygulaması oluştur"""
    orchestrator = MeetingOrchestrator()
    app = AdkApp(agent=orchestrator.orchestrator_agent)
    return app

async def main():
    """Ana uygulama fonksiyonu"""
    print("🚀 Google ADK Multi-Agent Toplantı Planlama Sistemi Başlatılıyor...")
    print("=" * 70)
    
    # Mod seçimi
    print("Çalışma modunu seçin:")
    print("1. Klasik Scheduler (eski sistem)")
    print("2. Google ADK Multi-Agent (yeni sistem)")
    print("3. ADK Web App (deployment)")
    
    while True:
        try:
            choice = input("\n🔸 Seçiminiz (1/2/3): ").strip()
            
            if choice == '1':
                # Klasik sistem
                print("\n📱 Klasik Toplantı Planlama Sistemi")
                scheduler = MeetingScheduler()
                
                print("=" * 50)
                print("Örnek: 'Ali (ali@gmail.com) ile yarın 1 saatlik toplantı ayarla'")
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
                        result = await scheduler.schedule_meeting(request)
                        
                        if result['success']:
                            print(f"✅ {result['message']}")
                            
                            if len(result['available_slots']) > 1:
                                print("\n📋 Diğer müsait zamanlar:")
                                for i, slot in enumerate(result['available_slots'][1:], 1):
                                    print(f"  {i+1}. {slot['date']} {slot['start']}-{slot['end']} (Puan: {slot['score']:.2f})")
                        else:
                            print(f"❌ Hata: {result['error']}")
                            
                            alternatives = scheduler.get_meeting_alternatives(request)
                            if alternatives['success'] and alternatives['alternatives']:
                                print("\n💡 Alternatif zamanlar:")
                                for i, alt in enumerate(alternatives['alternatives'][:3], 1):
                                    print(f"  {i}. {alt['date']} {alt['start']}-{alt['end']}")
                        
                        print("\n" + "="*50 + "\n")
                        
                    except KeyboardInterrupt:
                        print("\n👋 Görüşmek üzere!")
                        break
                    except Exception as e:
                        print(f"❌ Beklenmeyen hata: {str(e)}")
                break
                
            elif choice == '2':
                # Google ADK Multi-Agent sistem
                print("\n🤖 Google ADK Multi-Agent Sistemi")
                orchestrator = MeetingOrchestrator()
                await orchestrator.run_interactive_mode()
                break
                
            elif choice == '3':
                # ADK Web App
                print("\n🌐 ADK Web App başlatılıyor...")
                app = create_adk_app()
                print("✅ ADK App oluşturuldu!")
                print("🚀 Web sunucusu 8080 portunda başlatılıyor...")
                app.run(port=8080)
                break
                
            else:
                print("❌ Geçersiz seçim. Lütfen 1, 2 veya 3 girin.")
                
        except KeyboardInterrupt:
            print("\n👋 Görüşmek üzere!")
            break
        except Exception as e:
            print(f"❌ Beklenmeyen hata: {str(e)}")

if __name__ == "__main__":
    # Vertex AI başlatma
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    if project_id:
        try:
            vertexai.init(project=project_id, location="us-central1")
            print("✅ Vertex AI başlatıldı")
        except Exception as e:
            print(f"⚠️ Vertex AI başlatma hatası: {e}")
    
    # Ortam değişkenlerini kontrol et
    required_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD']
    optional_vars = ['GOOGLE_CLOUD_PROJECT', 'SENDER_NAME']
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    missing_optional = [var for var in optional_vars if not os.getenv(var)]
    
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
    
    if missing_optional:
        print("💡 İsteğe bağlı değişkenler:")
        for var in missing_optional:
            print(f"   - {var} (Google ADK için gerekli)")
        print()
    
    asyncio.run(main())