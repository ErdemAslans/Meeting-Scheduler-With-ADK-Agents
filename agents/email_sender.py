#!/usr/bin/env python3
"""
Google ADK Email Sender Agent
"""

import os
import smtplib
import ssl
from typing import List
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.adk.agents import Agent

def send_meeting_invitations(email_content: dict, recipients: List[str]) -> dict:
    """E-posta gönder - ADK Tool Function"""
    
    # Gerçek e-posta gönderimi
    try:
        # Kimlik bilgilerini al
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        if not sender_email or not sender_password:
            return {
                'success': False,
                'error': 'SENDER_EMAIL ve SENDER_PASSWORD çevre değişkenleri eksik',
                'sent_count': 0,
                'failed_count': len(recipients)
            }
        
        # E-posta içeriğini hazırla
        subject = email_content.get('subject', 'Toplantı Daveti')
        html_body = email_content.get('html_body', '')
        
        # SMTP bağlantısı
        context = ssl.create_default_context()
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls(context=context)
        server.login(sender_email, sender_password)
        
        sent_count = 0
        failed_count = 0
        
        for recipient in recipients:
            try:
                # E-posta mesajını oluştur
                message = MIMEMultipart('alternative')
                message['Subject'] = subject
                message['From'] = sender_email
                message['To'] = recipient
                
                # HTML içeriği ekle
                html_part = MIMEText(html_body, 'html')
                message.attach(html_part)
                
                # Gönder
                server.sendmail(sender_email, recipient, message.as_string())
                sent_count += 1
                
            except Exception as e:
                failed_count += 1
                print(f"E-posta gönderim hatası {recipient}: {e}")
        
        server.quit()
        
        return {
            'success': sent_count > 0,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'recipients': recipients,
            'message': f"✅ {sent_count} katılımcıya davet gönderildi, {failed_count} başarısız"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"SMTP bağlantı hatası: {str(e)}",
            'sent_count': 0,
            'failed_count': len(recipients)
        }

def create_email_sender_agent():
    """Email Sender Agent'ı oluşturur"""
    
    sender_agent = Agent(
        name="email_sender",
        model="gemini-1.5-flash",
        description="📨 Secure email delivery - Güvenli e-posta gönderimi",
        instruction="""Sen güvenilir e-posta gönderim uzmanısın!

GÖREVIN: E-postaları güvenli ve hızlı bir şekilde gönder.

İŞ AKIŞIN:
1. 📝 E-posta içeriğini al:
   - Konu (subject)
   - HTML içerik (html_body)
   - Alıcı listesi (recipients)

2. 🔐 Güvenli SMTP bağlantısı:
   - Gmail SMTP (smtp.gmail.com:587)
   - TLS şifreleme
   - App Password kimlik doğrulama
   - Bağlantı güvenliği

3. 📨 Toplu gönderim:
   - Her alıcı için ayrı mesaj
   - Hata toleransı
   - Gönderim raporu
   - Rate limiting (spam önleme)

4. 📊 Sonuç raporu:
   - Başarılı gönderim sayısı
   - Başarısız gönderim sayısı
   - Hata detayları
   - Teslimat durumu

ÖNEMLI:
- send_meeting_invitations tool'unu kullan
- SMTP kimlik bilgilerini güvenli şekilde al
- Her hatayı logla
- Bağlantıyı her zaman temizle
""",
        tools=[send_meeting_invitations]
    )
    
    return sender_agent

class EmailSender:
    """E-posta gönderim sınıfı"""
    
    def __init__(self):
        self.agent = create_email_sender_agent()
    
    def send_email(self, email_content: dict) -> dict:
        """E-posta gönder"""
        recipients = email_content.get('recipients', [])
        return send_meeting_invitations(email_content, recipients)