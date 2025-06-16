from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import icalendar
from google.adk.agents import Agent
import vertexai
from config.settings import LANGUAGE_TEMPLATES

def compose_meeting_invitation(
    meeting_details: Dict,
    language: str = "tr"
) -> Dict:
    """Toplantı daveti oluşturur - Google ADK Tool Function"""
    composer = EmailComposer()
    return composer.compose_invitation(meeting_details, language)

class EmailComposer:
    def __init__(self):
        self.templates = LANGUAGE_TEMPLATES
    
    def create_ics_file(self, meeting_details: Dict) -> bytes:
        """ICS takvim dosyası oluştur"""
        cal = icalendar.Calendar()
        cal.add('prodid', '-//Meeting Scheduler//Meeting Scheduler//EN')
        cal.add('version', '2.0')
        cal.add('calscale', 'GREGORIAN')
        cal.add('method', 'REQUEST')
        
        event = icalendar.Event()
        
        # Temel bilgiler
        event.add('uid', str(uuid.uuid4()))
        event.add('summary', meeting_details['title'])
        event.add('description', meeting_details.get('description', ''))
        
        # Tarih ve saat
        start_datetime = datetime.fromisoformat(f"{meeting_details['date']} {meeting_details['start_time']}")
        end_datetime = start_datetime + timedelta(minutes=meeting_details['duration'])
        
        event.add('dtstart', start_datetime)
        event.add('dtend', end_datetime)
        event.add('dtstamp', datetime.now())
        
        # Organizatör
        event.add('organizer', f"MAILTO:{meeting_details['organizer']}")
        
        # Katılımcılar
        for participant in meeting_details['participants']:
            event.add('attendee', f"MAILTO:{participant}")
        
        # Konum
        if meeting_details.get('location'):
            event.add('location', meeting_details['location'])
        
        # Hatırlatma
        alarm = icalendar.Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', 'Toplantı Hatırlatması')
        alarm.add('trigger', timedelta(minutes=-15))
        event.add_component(alarm)
        
        cal.add_component(event)
        return cal.to_ical()
    
    def generate_html_template(self, meeting_details: Dict, language: str = 'tr') -> str:
        """HTML e-posta şablonu oluştur"""
        template = self.templates[language]
        
        # Tarih formatı
        meeting_date = datetime.fromisoformat(f"{meeting_details['date']} {meeting_details['start_time']}")
        formatted_date = meeting_date.strftime('%d.%m.%Y') if language == 'tr' else meeting_date.strftime('%m/%d/%Y')
        formatted_time = meeting_details['start_time']
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="{language}">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{template['subject'].format(title=meeting_details['title'])}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .container {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                .meeting-details {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #667eea;
                    margin: 20px 0;
                }}
                .detail-row {{
                    display: flex;
                    justify-content: space-between;
                    margin: 10px 0;
                    padding: 5px 0;
                    border-bottom: 1px solid #eee;
                }}
                .detail-label {{
                    font-weight: bold;
                    color: #555;
                }}
                .detail-value {{
                    color: #333;
                }}
                .buttons {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .btn {{
                    padding: 12px 24px;
                    margin: 5px;
                    border: none;
                    border-radius: 5px;
                    text-decoration: none;
                    font-weight: bold;
                    display: inline-block;
                    transition: all 0.3s ease;
                }}
                .btn-accept {{
                    background-color: #28a745;
                    color: white;
                }}
                .btn-accept:hover {{
                    background-color: #218838;
                }}
                .btn-decline {{
                    background-color: #dc3545;
                    color: white;
                }}
                .btn-decline:hover {{
                    background-color: #c82333;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #eee;
                    color: #666;
                }}
                .calendar-info {{
                    background-color: #e7f3ff;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 20px 0;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 {meeting_details['title']}</h1>
                </div>
                
                <p><strong>{template['greeting']}</strong></p>
                <p>{template['invitation_text']}</p>
                
                <div class="meeting-details">
                    <div class="detail-row">
                        <span class="detail-label">📋 {('Başlık' if language == 'tr' else 'Title')}:</span>
                        <span class="detail-value">{meeting_details['title']}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">📅 {template['date_time'].split(':')[0]}:</span>
                        <span class="detail-value">{formatted_date} - {formatted_time}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">⏰ {template['duration'].split(':')[0]}:</span>
                        <span class="detail-value">{meeting_details['duration']} {'dakika' if language == 'tr' else 'minutes'}</span>
                    </div>
        """
        
        if meeting_details.get('location'):
            html_content += f"""
                    <div class="detail-row">
                        <span class="detail-label">📍 {template['location'].split(':')[0]}:</span>
                        <span class="detail-value">{meeting_details['location']}</span>
                    </div>
            """
        
        if meeting_details.get('description'):
            html_content += f"""
                    <div class="detail-row">
                        <span class="detail-label">📝 {'Açıklama' if language == 'tr' else 'Description'}:</span>
                        <span class="detail-value">{meeting_details['description']}</span>
                    </div>
            """
        
        # Katılımcı listesi
        participants_list = ', '.join(meeting_details['participants'])
        html_content += f"""
                    <div class="detail-row">
                        <span class="detail-label">👥 {'Katılımcılar' if language == 'tr' else 'Participants'}:</span>
                        <span class="detail-value">{participants_list}</span>
                    </div>
                </div>
                
                <div class="calendar-info">
                    <p><strong>📨 {'Takvim dosyası (ICS) ekte bulunmaktadır.' if language == 'tr' else 'Calendar file (ICS) is attached.'}</strong></p>
                    <p>{'Takviminize eklemek için dosyayı açınız.' if language == 'tr' else 'Open the file to add to your calendar.'}</p>
                </div>
                
                <div class="buttons">
                    <a href="mailto:{meeting_details['organizer']}?subject=RE: {meeting_details['title']} - {'Katılacağım' if language == 'tr' else 'Accept'}" class="btn btn-accept">
                        ✅ {template['accept_button']}
                    </a>
                    <a href="mailto:{meeting_details['organizer']}?subject=RE: {meeting_details['title']} - {'Katılamam' if language == 'tr' else 'Decline'}" class="btn btn-decline">
                        ❌ {template['decline_button']}
                    </a>
                </div>
                
                <div class="footer">
                    <p>{template['regards']}</p>
                    <p><strong>{meeting_details.get('organizer_name', meeting_details['organizer'])}</strong></p>
                    <hr>
                    <p><small>🤖 {'Bu e-posta otomatik toplantı planlama sistemi tarafından gönderilmiştir.' if language == 'tr' else 'This email was sent by an automated meeting scheduling system.'}</small></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_plain_text(self, meeting_details: Dict, language: str = 'tr') -> str:
        """Düz metin e-posta oluştur"""
        template = self.templates[language]
        
        meeting_date = datetime.fromisoformat(f"{meeting_details['date']} {meeting_details['start_time']}")
        formatted_date = meeting_date.strftime('%d.%m.%Y') if language == 'tr' else meeting_date.strftime('%m/%d/%Y')
        
        text_content = f"""
{template['greeting']}

{template['invitation_text']}

=== {'TOPLANTI BİLGİLERİ' if language == 'tr' else 'MEETING DETAILS'} ===

{'Başlık' if language == 'tr' else 'Title'}: {meeting_details['title']}
{template['date_time'].format(date=formatted_date, time=meeting_details['start_time'])}
{template['duration'].format(duration=meeting_details['duration'])}
"""
        
        if meeting_details.get('location'):
            text_content += f"{template['location'].format(location=meeting_details['location'])}\n"
        
        if meeting_details.get('description'):
            text_content += f"\n{'Açıklama' if language == 'tr' else 'Description'}:\n{meeting_details['description']}\n"
        
        participants_list = ', '.join(meeting_details['participants'])
        text_content += f"\n{'Katılımcılar' if language == 'tr' else 'Participants'}: {participants_list}\n"
        
        text_content += f"""
==================================================

{'Katılım durumunuzu bildirmek için bu e-postayı yanıtlayın:' if language == 'tr' else 'Reply to this email to confirm your attendance:'}
- {template['accept_button']}: {meeting_details['title']} - {'Katılacağım' if language == 'tr' else 'Accept'}
- {template['decline_button']}: {meeting_details['title']} - {'Katılamam' if language == 'tr' else 'Decline'}

{template['regards']}
{meeting_details.get('organizer_name', meeting_details['organizer'])}

---
{'Bu e-posta otomatik toplantı planlama sistemi tarafından gönderilmiştir.' if language == 'tr' else 'This email was sent by an automated meeting scheduling system.'}
        """
        
        return text_content.strip()
    
    def compose_invitation(self, meeting_details: Dict, language: str = 'tr') -> Dict:
        """Ana fonksiyon: Toplantı davetini oluştur"""
        try:
            template = self.templates[language]
            
            # E-posta konusu
            subject = template['subject'].format(title=meeting_details['title'])
            
            # HTML içerik
            html_body = self.generate_html_template(meeting_details, language)
            
            # Düz metin içerik
            plain_body = self.generate_plain_text(meeting_details, language)
            
            # ICS dosyası
            ics_content = self.create_ics_file(meeting_details)
            
            # MIME mesajını oluştur
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = meeting_details['organizer']
            msg['To'] = ', '.join(meeting_details['participants'])
            
            # Düz metin ve HTML kısımları ekle
            part1 = MIMEText(plain_body, 'plain', 'utf-8')
            part2 = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # ICS dosyasını ekle
            ics_part = MIMEBase('text', 'calendar')
            ics_part.set_payload(ics_content)
            encoders.encode_base64(ics_part)
            ics_part.add_header(
                'Content-Disposition',
                f'attachment; filename="{meeting_details["title"].replace(" ", "_")}.ics"'
            )
            ics_part.add_header('Content-Type', 'text/calendar; method=REQUEST')
            msg.attach(ics_part)
            
            return {
                'success': True,
                'subject': subject,
                'message': msg,
                'html_body': html_body,
                'plain_body': plain_body,
                'ics_content': ics_content,
                'recipients': meeting_details['participants']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"E-posta oluşturma hatası: {str(e)}"
            }
    
    def preview_invitation(self, meeting_details: Dict, language: str = 'tr') -> Dict:
        """Davet önizlemesi oluştur"""
        try:
            template = self.templates[language]
            subject = template['subject'].format(title=meeting_details['title'])
            html_body = self.generate_html_template(meeting_details, language)
            plain_body = self.generate_plain_text(meeting_details, language)
            
            return {
                'success': True,
                'subject': subject,
                'html_preview': html_body,
                'text_preview': plain_body,
                'recipients': meeting_details['participants']
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Önizleme oluşturma hatası: {str(e)}"
            }