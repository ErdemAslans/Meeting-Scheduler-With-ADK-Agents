#!/usr/bin/env python3
"""
Google ADK Multi-Agent Meeting Scheduler - UI Mode
"""

import os
import asyncio
import vertexai
from agents.orchestrator import MeetingOrchestrator
from vertexai.preview.reasoning_engines import AdkApp
from config.settings import GOOGLE_ADK_CONFIG

def setup_environment():
    """Çevre değişkenlerini ve Vertex AI'yi ayarla"""
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'agentproject-462613')
    
    if not project_id:
        print("❌ GOOGLE_CLOUD_PROJECT çevre değişkeni eksik!")
        return False
    
    try:
        vertexai.init(project=project_id, location='us-central1')
        print(f"✅ Vertex AI başlatıldı - Project: {project_id}")
        return True
    except Exception as e:
        print(f"❌ Vertex AI başlatma hatası: {e}")
        return False

def create_adk_app_with_ui():
    """ADK uygulamasını UI modunda oluştur"""
    try:
        orchestrator = MeetingOrchestrator()
        
        # ADK App oluştur - UI parametreleri ile
        app = AdkApp(
            agent=orchestrator.orchestrator_agent,
            # UI konfigürasyonu
            description="🤖 AI-powered meeting scheduler - Doğal dilde toplantı planlama asistanı",
            examples=[
                "Ali (ali@example.com) ile yarın 1 saatlik toplantı ayarla",
                "john@company.com ile pazartesi 30 dakikalık demo planla", 
                "Plan a 2 hour meeting with team@startup.com for Friday"
            ]
        )
        
        print("✅ ADK App oluşturuldu")
        return app
    except Exception as e:
        print(f"❌ ADK App oluşturma hatası: {e}")
        return None

def run_ui_mode():
    """UI modunda çalıştır"""
    print("🚀 Google ADK Multi-Agent Meeting Scheduler - UI Mode")
    print("=" * 55)
    
    if not setup_environment():
        return
    
    app = create_adk_app_with_ui()
    if not app:
        return
    
    try:
        print("\n🌐 ADK UI başlatılıyor...")
        print("📱 Browser'ınızda şu adrese gidin:")
        print("   → http://localhost:8080")
        print("\n💡 UI özellikleri:")
        print("   • Chat interface ile doğal dil girişi")
        print("   • Örnek: 'Ali ile yarın toplantı ayarla'")
        print("   • Real-time AI agent responses")
        print("\n🛑 Durdurmak için Ctrl+C")
        
        # UI mode ile başlat
        app.run(
            port=8080,
            host="0.0.0.0",  # Tüm network interface'lerden erişim
            debug=True       # Debug mode - daha detaylı log
        )
        
    except KeyboardInterrupt:
        print("\n👋 UI kapatılıyor...")
    except Exception as e:
        print(f"❌ UI başlatma hatası: {e}")
        print("💡 API mode kullanmayı deneyin: python run_adk.py")

def run_api_mode():
    """API modunda çalıştır (mevcut)"""
    print("🚀 Google ADK Multi-Agent Meeting Scheduler - API Mode")
    print("=" * 55)
    
    if not setup_environment():
        return
    
    app = create_adk_app_with_ui()
    if not app:
        return
    
    try:
        print("\n📡 API Mode başlatılıyor...")
        print("🌐 API endpoint hazır:")
        print("   POST http://localhost:8080/query")
        print("   Content-Type: application/json")
        print('   Body: {"user_id": "user1", "message": "toplantı talebi"}')
        
        # Test request
        print("\n🧪 Test request:")
        print('curl -X POST http://localhost:8080/query \\')
        print('  -H "Content-Type: application/json" \\')
        print('  -d \'{"user_id": "user1", "message": "Ali ile toplantı"}\'')
        
        app.run(port=8080, host="0.0.0.0")
        
    except KeyboardInterrupt:
        print("\n👋 API kapatılıyor...")

def main():
    """Ana fonksiyon - Mode seçimi"""
    print("🤖 Google ADK Meeting Scheduler")
    print("=" * 35)
    print("Hangi modda çalıştırmak istiyorsunuz?")
    print("1. 🌐 UI Mode (Browser interface)")
    print("2. 📡 API Mode (REST endpoint)")
    print("3. 🧪 Auto Mode (Otomatik UI deneme)")
    
    while True:
        try:
            choice = input("\n🔸 Seçiminiz (1/2/3): ").strip()
            
            if choice == '1':
                run_ui_mode()
                break
            elif choice == '2':
                run_api_mode()
                break
            elif choice == '3':
                print("\n🧪 UI mode deneniyor...")
                try:
                    run_ui_mode()
                except Exception as e:
                    print(f"❌ UI mode başarısız: {e}")
                    print("📡 API mode'a geçiliyor...")
                    run_api_mode()
                break
            else:
                print("❌ Geçersiz seçim. 1, 2 veya 3 girin.")
                
        except KeyboardInterrupt:
            print("\n👋 Çıkış yapılıyor...")
            break

if __name__ == "__main__":
    main()