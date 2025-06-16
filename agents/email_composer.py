#!/usr/bin/env python3
"""
Google ADK Email Composer Agent - UPDATED with Calendar Link Support
"""

from typing import List
from google.adk.agents import Agent

def compose_meeting_invitation(meeting_details: dict, language: str = "tr") -> dict:
    """Toplantı daveti oluştur - UPDATED with Calendar Link - ADK Tool Function"""
   
    # Toplantı başlığını al
    title = meeting_details.get('subject', meeting_details.get('title', 'Toplantı'))
    subject = f"Toplantı Daveti: {title}"
   
    # Katılımcıları al
    participants = meeting_details.get('attendees', meeting_details.get('participants', []))
    
    # Calendar link al (yeni özellik)
    calendar_link = meeting_details.get('event_link', meeting_details.get('calendar_link', ''))
    event_id = meeting_details.get('event_id', '')
    
    # HTML content - UPDATED with Calendar Link
    calendar_section = ""
    if calendar_link:
        calendar_section = f"""
        <div style="background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0;">
            <h3 style="color: #2e7d32; margin: 0 0 10px 0;">📅 Calendar Event</h3>
            <p style="margin: 5px 0;"><strong>Event ID:</strong> {event_id}</p>
            <p style="margin: 5px 0;">
                <a href="{calendar_link}" 
                   style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                   📅 Takvimde Görüntüle
                </a>
            </p>
            <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">
                Bu etkinlik otomatik olarak takviminize eklenmiştir. Yukarıdaki butona tıklayarak Google Calendar'da görüntüleyebilirsiniz.
            </p>
        </div>
        """
    
    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #2c3e50;">📅 {title}</h2>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
            <p><strong>📅 Tarih:</strong> {meeting_details.get('date')}</p>
            <p><strong>⏰ Saat:</strong> {meeting_details.get('start_time')} - {meeting_details.get('end_time')}</p>
            <p><strong>⏱️ Süre:</strong> {meeting_details.get('duration', 60)} dakika</p>
            <p><strong>📍 Konum:</strong> {meeting_details.get('location', 'Online')}</p>
            <p><strong>👥 Katılımcılar:</strong> {', '.join(participants)}</p>
        </div>
        {calendar_section}
        <p style="margin-top: 20px;">Bu toplantıya davet edildiniz. Katılım durumunuzu bildirmek için organizatöre yanıt verin.</p>
        <p style="color: #666; font-size: 12px;">Bu davet Verlumea AI Meeting Scheduler tarafından gönderilmiştir.</p>
    </div>
    """
   
    return {
        'success': True,
        'subject': subject,
        'html_body': html_body,
        'recipients': participants,
        'message': f"Davet hazırlandı: {subject}" + (f" (Calendar Link: {calendar_link})" if calendar_link else ""),
        'calendar_link': calendar_link,
        'event_id': event_id
    }

def create_email_composer_agent():
    """Email Composer Agent'ı oluşturur - UPDATED"""
   
    email_agent = Agent(
        name="email_composer",
        model="gemini-1.5-flash",
        description="📧 Professional email composer with Calendar Link support - Profesyonel e-posta yazarı",
        instruction="""Sen profesyonel e-posta yazarısın!

🆕 YENİ ÖZELLİK: Calendar Link Desteği

GÖREVIN: Toplantı davetleri ve e-posta içerikleri oluştur.

İŞ AKIŞIN:
1. 📝 Toplantı detaylarını al:
   - Başlık/konu
   - Tarih ve saat
   - Katılımcılar
   - Konum (Online/Ofis)
   - Süre
   - 🆕 Calendar Link (event_link)
   - 🆕 Event ID (event_id)

2. 📧 Profesyonel davet oluştur:
   - HTML formatında güzel tasarım
   - Responsive e-posta şablonu
   - Tüm detayları içeren içerik
   - 🆕 Calendar Link butonu ekle
   - Marka kimliği (Verlumea AI)

3. 🎨 E-posta tasarımı:
   - Modern ve temiz görünüm
   - Kolay okunabilir fontlar
   - Renk uyumu (#2c3e50, #f8f9fa)
   - 🆕 Özel Calendar bölümü (#e8f5e8, #2e7d32)
   - Mobil uyumlu

4. 📋 İçerik standartları:
   - Net ve anlaşılır dil
   - Profesyonel üslup
   - Gerekli tüm bilgiler
   - 🆕 Calendar Link CTA button
   - Call-to-action (yanıt verme)

🆕 CALENDAR LINK ÖZELLİKLERİ:
- Event ID göster
- "Takvimde Görüntüle" butonu
- Otomatik ekleme bildirimi
- Görsel calendar icon

ÖNEMLI:
- compose_meeting_invitation tool'unu kullan
- Her dil için uygun şablon (TR/EN)
- Calendar link varsa mutlaka ekle
- Teknik detayları gizle, sadece önemli bilgiler
- Kullanıcı dostu format
""",
        tools=[compose_meeting_invitation]
    )
   
    return email_agent

class EmailComposer:
    """E-posta oluşturma sınıfı - UPDATED"""
   
    def __init__(self):
        self.agent = create_email_composer_agent()
   
    def compose_invitation(self, meeting_details: dict, language: str = 'tr') -> dict:
        """Toplantı daveti oluştur - UPDATED"""
        return compose_meeting_invitation(meeting_details, language)