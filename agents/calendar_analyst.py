#!/usr/bin/env python3
"""
Google ADK Calendar Analyst Agent
"""

from typing import List
from google.adk.agents import Agent

def check_calendar_availability(participants: List[str], date: str, duration_minutes: int) -> dict:
    """Takvim müsaitliği kontrol et - ADK Tool Function"""
    # Mock data - gerçek uygulamada Google Calendar API kullanılacak
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
        },
        {
            'start': '15:30',
            'end': f'{15 + duration_minutes//60}:{30 + duration_minutes%60:02d}',
            'date': date,
            'score': 0.7,
            'duration': duration_minutes
        }
    ]
    
    return {
        'available_slots': available_slots,
        'participants': participants,
        'date': date,
        'duration': duration_minutes,
        'message': f'{len(participants)} katılımcı için {len(available_slots)} müsait zaman bulundu'
    }

def create_calendar_agent():
    """Calendar Analyst Agent'ı oluşturur"""
    
    calendar_agent = Agent(
        name="calendar_analyst",
        model="gemini-1.5-flash",
        description="📅 Calendar availability checker - Takvim müsaitlik kontrolcüsü",
        instruction="""Sen uzman bir takvim analistisin!

GÖREVIN: Katılımcıların takvim müsaitliğini kontrol et ve en uygun zaman dilimlerini öner.

İŞ AKIŞIN:
1. 📝 Parametreleri al:
   - Katılımcı listesi (e-posta adresleri)
   - Tarih (YYYY-MM-DD formatında)
   - Süre (dakika cinsinden)

2. 📅 Müsaitlik kontrolü:
   - Her katılımcının takvimini kontrol et
   - Çalışma saatleri: 09:00-18:00 (Türkiye saati)
   - Öğle arası: 12:00-13:00 (meşgul)
   - Weekend'leri hariç tut

3. ⭐ Zaman dilimlerini skorla:
   - Sabah 10-11: Yüksek puan (0.9)
   - Öğleden sonra 14-16: Orta puan (0.8)
   - Diğer saatler: Düşük puan (0.7)

4. 📊 En uygun 3 zamanı döndür:
   - Skorlamaya göre sırala
   - Her zaman dilimi için detaylı bilgi ver

ÖNEMLI:
- check_calendar_availability tool'unu doğru parametrelerle kullan
- Sonuçları net ve anlaşılır şekilde sun
- Katılımcı sayısına göre zorluk seviyesini belirt
""",
        tools=[check_calendar_availability]
    )
    
    return calendar_agent

class CalendarAnalyst:
    """Takvim analisti sınıfı"""
    
    def __init__(self):
        self.agent = create_calendar_agent()
    
    async def check_availability(self, participants: List[str], date: str, duration: int) -> List[dict]:
        """Müsaitlik kontrolü"""
        result = check_calendar_availability(participants, date, duration)
        return result.get('available_slots', [])