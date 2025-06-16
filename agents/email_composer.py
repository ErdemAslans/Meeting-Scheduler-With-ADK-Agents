#!/usr/bin/env python3
"""
Google ADK Email Composer Agent
"""

from typing import List
from google.adk.agents import Agent

def compose_meeting_invitation(meeting_details: dict, language: str = "tr") -> dict:
    """Toplantı daveti oluştur - ADK Tool Function"""
    
    # Toplantı başlığını al
    title = meeting_details.get('subject', meeting_details.get('title', 'Toplantı'))
    subject = f"Toplantı Daveti: {title}"
    
    # Katılımcıları al
    participants = meeting_details.get('attendees', meeting_details.get('participants', []))
    
    # HTML content
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">📅 {title}</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <p><strong>📅 Tarih:</strong> {meeting_details.get('date')}</p>
            <p><strong>⏰ Saat:</strong> {meeting_details.get('start_time')} - {meeting_details.get('end_time')}</p>
            <p><strong>⏱️ Süre:</strong> 60 dakika</p>
            <p><strong>📍 Konum:</strong> {meeting_details.get('location', 'Online')}</p>
            <p><strong>👥 Katılımcılar:</strong> {', '.join(participants)}</p>
        </div>
        <p style="margin-top: 20px;">Bu toplantıya davet edildiniz. Katılım durumunuzu bildirmek için organizatöre yanıt verin.</p>
        <p style="color: #666; font-size: 12px;">Bu davet Verlumea AI Meeting Scheduler tarafından gönderilmiştir.</p>
    </div>
    """
    
    return {
        'success': True,
        'subject': subject,
        'html_body': html_body,
        'recipients': participants,
        'message': f"Davet hazırlandı: {subject}"
    }

def create_email_composer_agent():
    """Email Composer Agent'ı oluşturur"""
    
    email_agent = Agent(
        name="email_composer",
        model="gemini-1.5-flash",
        description="📧 Professional email composer - Profesyonel e-posta yazarı",
        instruction="""Sen profesyonel e-posta yazarısın!

GÖREVIN: Toplantı davetleri ve e-posta içerikleri oluştur.

İŞ AKIŞIN:
1. 📝 Toplantı detaylarını al:
   - Başlık/konu
   - Tarih ve saat
   - Katılımcılar
   - Konum (Online/Ofis)
   - Süre

2. 📧 Profesyonel davet oluştur:
   - HTML formatında güzel tasarım
   - Responsive e-posta şablonu
   - Tüm detayları içeren içerik
   - Marka kimliği (Verlumea AI)

3. 🎨 E-posta tasarımı:
   - Modern ve temiz görünüm
   - Kolay okunabilir fontlar
   - Renk uyumu (#2c3e50, #f8f9fa)
   - Mobil uyumlu

4. 📋 İçerik standartları:
   - Net ve anlaşılır dil
   - Profesyonel üslup
   - Gerekli tüm bilgiler
   - Call-to-action (yanıt verme)

ÖNEMLI:
- compose_meeting_invitation tool'unu kullan
- Her dil için uygun şablon (TR/EN)
- Teknik detayları gizle, sadece önemli bilgiler
- Kullanıcı dostu format
""",
        tools=[compose_meeting_invitation]
    )
    
    return email_agent

class EmailComposer:
    """E-posta oluşturma sınıfı"""
    
    def __init__(self):
        self.agent = create_email_composer_agent()
    
    def compose_invitation(self, meeting_details: dict, language: str = 'tr') -> dict:
        """Toplantı daveti oluştur"""
        return compose_meeting_invitation(meeting_details, language)