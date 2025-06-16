import smtplib
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import ssl
import asyncio
from google.adk.agents import Agent
import vertexai
from config.settings import SMTP_CONFIG
import os

async def send_meeting_invitations(
    email_content: Dict,
    recipients: List[str]
) -> Dict:
    """E-postaları gönderir - Google ADK Tool Function"""
    sender = EmailSender()
    return sender.send_email(email_content)

class EmailSender:
    def __init__(self):
        self.smtp_configs = SMTP_CONFIG
    
    def get_smtp_config(self, email: str) -> Optional[Dict]:
        """E-posta adresine göre SMTP ayarlarını belirle"""
        email_lower = email.lower()
        
        if any(domain in email_lower for domain in ['gmail.com', 'googlemail.com']):
            return self.smtp_configs['gmail']
        elif any(domain in email_lower for domain in ['outlook.com', 'hotmail.com', 'live.com']):
            return self.smtp_configs['outlook']
        else:
            # Varsayılan olarak Gmail ayarlarını kullan
            return self.smtp_configs['gmail']
    
    def authenticate_smtp(self, email: str, password: str) -> tuple:
        """SMTP kimlik doğrulama"""
        config = self.get_smtp_config(email)
        if not config:
            raise ValueError(f"Desteklenmeyen e-posta sağlayıcısı: {email}")
        
        try:
            # SSL bağlamı oluştur
            context = ssl.create_default_context()
            
            # SMTP sunucusuna bağlan
            server = smtplib.SMTP(config['server'], config['port'])
            
            if config['use_tls']:
                server.starttls(context=context)
            
            # Giriş yap
            server.login(email, password)
            
            return server, None
            
        except smtplib.SMTPAuthenticationError as e:
            return None, f"Kimlik doğrulama hatası: {str(e)}"
        except smtplib.SMTPConnectError as e:
            return None, f"Bağlantı hatası: {str(e)}"
        except Exception as e:
            return None, f"SMTP hatası: {str(e)}"
    
    def send_single_email(self, server: smtplib.SMTP, sender_email: str, recipient_email: str, message: MIMEMultipart) -> Dict:
        """Tek bir e-posta gönder"""
        try:
            # E-posta başlıklarını ayarla
            message['From'] = sender_email
            message['To'] = recipient_email
            
            # E-postayı gönder
            text = message.as_string()
            server.sendmail(sender_email, recipient_email, text)
            
            return {
                'success': True,
                'recipient': recipient_email,
                'message': 'E-posta başarıyla gönderildi'
            }
            
        except smtplib.SMTPRecipientsRefused as e:
            return {
                'success': False,
                'recipient': recipient_email,
                'error': f"Alıcı reddedildi: {str(e)}"
            }
        except smtplib.SMTPDataError as e:
            return {
                'success': False,
                'recipient': recipient_email,
                'error': f"Veri hatası: {str(e)}"
            }
        except Exception as e:
            return {
                'success': False,
                'recipient': recipient_email,
                'error': f"Gönderim hatası: {str(e)}"
            }
    
    async def send_email_batch(self, sender_email: str, sender_password: str, recipients: List[str], message: MIMEMultipart) -> Dict:
        """Toplu e-posta gönderimi"""
        # SMTP sunucusuna bağlan
        server, error = self.authenticate_smtp(sender_email, sender_password)
        if error:
            return {
                'success': False,
                'error': error,
                'sent_count': 0,
                'failed_count': len(recipients)
            }
        
        results = []
        sent_count = 0
        failed_count = 0
        
        try:
            for recipient in recipients:
                # Her alıcı için mesajı kopyala
                msg_copy = MIMEMultipart()
                for key, value in message.items():
                    msg_copy[key] = value
                
                # Mesaj içeriğini kopyala
                for part in message.walk():
                    if part.get_content_maintype() != 'multipart':
                        msg_copy.attach(part)
                
                # E-postayı gönder
                result = self.send_single_email(server, sender_email, recipient, msg_copy)
                results.append(result)
                
                if result['success']:
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Kısa bir bekleme (rate limiting için)
                await asyncio.sleep(0.1)
            
        finally:
            # Bağlantıyı kapat
            server.quit()
        
        return {
            'success': sent_count > 0,
            'results': results,
            'sent_count': sent_count,
            'failed_count': failed_count,
            'total_recipients': len(recipients)
        }
    
    def send_email(self, email_content: Dict) -> Dict:
        """Ana fonksiyon: E-posta gönderimi"""
        try:
            if not email_content.get('success', False):
                return {
                    'success': False,
                    'error': 'Geçersiz e-posta içeriği'
                }
            
            # Kimlik bilgilerini çevre değişkenlerinden al
            sender_email = os.getenv('SENDER_EMAIL')
            sender_password = os.getenv('SENDER_PASSWORD')
            
            if not sender_email or not sender_password:
                return {
                    'success': False,
                    'error': 'Gönderici kimlik bilgileri bulunamadı. SENDER_EMAIL ve SENDER_PASSWORD çevre değişkenlerini ayarlayın.'
                }
            
            # Eşzamansız gönderim fonksiyonunu çalıştır
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.send_email_batch(
                        sender_email,
                        sender_password,
                        email_content['recipients'],
                        email_content['message']
                    )
                )
                return result
            finally:
                loop.close()
                
        except Exception as e:
            return {
                'success': False,
                'error': f"E-posta gönderim hatası: {str(e)}"
            }
    
    def test_smtp_connection(self, email: str, password: str) -> Dict:
        """SMTP bağlantısını test et"""
        try:
            server, error = self.authenticate_smtp(email, password)
            if error:
                return {
                    'success': False,
                    'error': error
                }
            
            server.quit()
            return {
                'success': True,
                'message': 'SMTP bağlantısı başarılı'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Bağlantı testi hatası: {str(e)}"
            }
    
    def get_delivery_report(self, results: List[Dict]) -> str:
        """Teslimat raporu oluştur"""
        if not results:
            return "Teslimat raporu bulunamadı."
        
        sent_emails = [r for r in results if r['success']]
        failed_emails = [r for r in results if not r['success']]
        
        report = f"""
=== TESLIMAT RAPORU ===

Toplam Alıcı: {len(results)}
Başarılı Gönderim: {len(sent_emails)}
Başarısız Gönderim: {len(failed_emails)}

"""
        
        if sent_emails:
            report += "✅ BAŞARILI GÖNDERİMLER:\n"
            for email in sent_emails:
                report += f"  - {email['recipient']}\n"
            report += "\n"
        
        if failed_emails:
            report += "❌ BAŞARISIZ GÖNDERİMLER:\n"
            for email in failed_emails:
                report += f"  - {email['recipient']}: {email['error']}\n"
            report += "\n"
        
        success_rate = (len(sent_emails) / len(results)) * 100
        report += f"Başarı Oranı: {success_rate:.1f}%"
        
        return report