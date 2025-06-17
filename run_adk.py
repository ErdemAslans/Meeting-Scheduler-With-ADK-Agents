#!/usr/bin/env python3
"""
Google ADK Multi-Agent Meeting Scheduler
Gerçek multi-agent toplantı planlama sistemi
"""

import os
import asyncio
import vertexai
from agents.orchestrator import MeetingOrchestrator
from vertexai.preview.reasoning_engines import AdkApp
from config.settings import GOOGLE_ADK_CONFIG

def setup_environment():
    """Çevre değişkenlerini ve Vertex AI'yi ayarla"""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT çevre değişkeni eksik!")
        print("export GOOGLE_CLOUD_PROJECT='your-project-id'")
        return False
    
    try:
        vertexai.init(
            project=project_id, 
            location=GOOGLE_ADK_CONFIG['location']
        )
        print(f"✅ Vertex AI başlatıldı - Project: {project_id}")
        return True
    except Exception as e:
        print(f"❌ Vertex AI başlatma hatası: {e}")
        return False

def create_adk_app():
    """ADK uygulamasını oluştur"""
    try:
        orchestrator = MeetingOrchestrator()
        app = AdkApp(agent=orchestrator.orchestrator_agent)
        print("✅ ADK App oluşturuldu")
        return app
    except Exception as e:
        print(f"❌ ADK App oluşturma hatası: {e}")
        return None

async def run_interactive():
    """İnteraktif mod"""
    print("🤖 Google ADK Interactive Mode")
    orchestrator = MeetingOrchestrator()
    await orchestrator.run_interactive_mode()

def run_web_server(port=8080):
    """Web sunucusu modunda çalıştır"""
    app = create_adk_app()
    if app:
        print(f"🌐 Web sunucusu {port} portunda başlatılıyor...")
        try:
            app.run(port=port)
        except Exception as e:
            print(f"❌ Web sunucusu hatası: {e}")

def main():
    """Ana fonksiyon"""
    print("🚀 Google ADK Multi-Agent Meeting Scheduler")
    print("=" * 50)
    
    # Çevre kontrolü
    if not setup_environment():
        return
    
    # Gerekli değişkenleri kontrol et
    required_vars = ['SENDER_EMAIL', 'SENDER_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("⚠️  Gerekli çevre değişkenleri eksik:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nÖrnek kullanım:")
        print("export SENDER_EMAIL='your-email@gmail.com'")
        print("export SENDER_PASSWORD='your-app-password'")
        print("export SENDER_NAME='Your Name'")
        return
    
    # Mod seçimi
    print("\nÇalışma modunu seçin:")
    print("1. İnteraktif Mod (komut satırı)")
    print("2. Web Sunucusu (ADK App)")
    print("3. Test Modu")
    
    while True:
        try:
            choice = input("\n🔸 Seçiminiz (1/2/3): ").strip()
            
            if choice == '1':
                print("\n📱 İnteraktif mod başlatılıyor...")
                asyncio.run(run_interactive())
                break
                
            elif choice == '2':
                port = input("Port (varsayılan 8080): ").strip()
                port = int(port) if port.isdigit() else 8080
                run_web_server(port)
                break
                
            elif choice == '3':
                print("\n🧪 Test modu çalıştırılıyor...")
                asyncio.run(test_system())
                break
                
            else:
                print("❌ Geçersiz seçim. 1, 2 veya 3 girin.")
                
        except KeyboardInterrupt:
            print("\n👋 Çıkış yapılıyor...")
            break
        except Exception as e:
            print(f"❌ Hata: {e}")

async def test_system():
    """Sistem testi"""
    print("🧪 ADK Multi-Agent System Test")
    print("-" * 40)
    
    orchestrator = MeetingOrchestrator()
    
    # Test komutları
    test_requests = [
        "Ali (ali@example.com) ve Ayşe (ayse@example.com) ile yarın 1 saatlik toplantı ayarla",
        "john@example.com ile pazartesi 30 dakikalık demo planla",
        "Plan a 2 hour meeting with team@example.com for next friday"
    ]
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n📋 Test {i}: {request}")
        print("-" * 30)
        
        try:
            result = await orchestrator.schedule_meeting_with_agent(request)
            
            if result['success']:
                print("✅ Test Başarılı")
                print(f"📄 Agent Yanıtı: {result['agent_response'][:200]}...")
            else:
                print(f"❌ Test Başarısız: {result['error']}")
                
        except Exception as e:
            print(f"❌ Test Hatası: {e}")
        
        print("-" * 40)
    
    print("\n🏁 Test tamamlandı!")

if __name__ == "__main__":
    main()