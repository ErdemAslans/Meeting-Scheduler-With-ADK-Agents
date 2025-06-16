import os
from typing import Dict, Any

# Google ADK ve Vertex AI ayarları
GOOGLE_ADK_CONFIG = {
    'project_id': os.getenv('GOOGLE_CLOUD_PROJECT'),
    'location': 'us-central1',
    'models': {
        'calendar_analyst': 'gemini-1.5-flash',
        'email_composer': 'gemini-1.5-flash', 
        'email_sender': 'gemini-1.5-flash',
        'orchestrator': 'gemini-2.0-flash'
    },
    'temperatures': {
        'calendar_analyst': 0.1,
        'email_composer': 0.7,
        'email_sender': 0.1, 
        'orchestrator': 0.3
    }
}

# Google Calendar API ayarları
GOOGLE_CALENDAR_CONFIG = {
    'scopes': ['https://www.googleapis.com/auth/calendar.readonly'],
    'credentials_file': 'credentials.json',
    'token_file': 'token.json'
}

# Microsoft Graph API ayarları
MICROSOFT_GRAPH_CONFIG = {
    'client_id': os.getenv('MICROSOFT_CLIENT_ID'),
    'client_secret': os.getenv('MICROSOFT_CLIENT_SECRET'),
    'tenant_id': os.getenv('MICROSOFT_TENANT_ID'),
    'scope': ['https://graph.microsoft.com/Calendars.Read']
}

# E-posta SMTP ayarları
SMTP_CONFIG = {
    'gmail': {
        'server': 'smtp.gmail.com',
        'port': 587,
        'use_tls': True
    },
    'outlook': {
        'server': 'smtp-mail.outlook.com',
        'port': 587,
        'use_tls': True
    }
}

# Çalışma saatleri ayarları
WORKING_HOURS = {
    'start': '09:00',
    'end': '18:00',
    'lunch_start': '12:00',
    'lunch_end': '13:00',
    'timezone': 'Europe/Istanbul'
}

# Agent instruction'ları
AGENT_INSTRUCTIONS = {
    'calendar_analyst': """
    Sen uzman bir takvim analistisin.
    - FreeBusy API kullanarak Google Calendar ve Outlook takvimlerini sorgula
    - Çalışma saatleri: 09:00-18:00 (Türkiye saati)
    - Öğle arası: 12:00-13:00 (meşgul olarak işaretle)
    - En uygun 3 zamanı öner ve skorla
    - Puanlama kriterleri: sabah 10-11 ve öğleden sonra 14-16 arası yüksek puan
    - Weekend'leri hariç tut
    - Tatil günlerini dikkate al
    
    Tool kullanımı:
    - check_calendar_availability fonksiyonunu kullanarak müsaitlik kontrolü yap
    - Katılımcılar listesi, tarih ve süre bilgilerini doğru şekilde geç
    """,
    
    'email_composer': """
    Sen profesyonel e-posta yazarısın.
    - Kurumsal standartlarda toplantı davetleri hazırla
    - HTML ve plain text versiyonları oluştur
    - ICS takvim dosyası ekle
    - Türkçe ve İngilizce dil desteği
    - Kişiselleştirilmiş ve profesyonel içerik
    - Responsive e-posta tasarımı kullan
    
    Tool kullanımı:
    - compose_meeting_invitation fonksiyonunu kullan
    - Toplantı detayları ve dil parametrelerini doğru şekilde geç
    """,
    
    'email_sender': """
    Sen güvenilir e-posta gönderim uzmanısın.
    - SMTP üzerinden güvenli e-posta gönderimi
    - Gmail ve Outlook SMTP desteği
    - Teslimat onayı takibi
    - Hata durumunda retry mekanizması
    - Rate limiting uygula
    
    Tool kullanımı:
    - send_meeting_invitations fonksiyonunu kullan
    - E-posta içeriği ve alıcı listesini doğru şekilde geç
    """,
    
    'orchestrator': """
    Sen akıllı toplantı planlama koordinatörüsün.
    
    Kullanıcı doğal dilde istekte bulunacak:
    Örnek: "Ali (ali@gmail.com) ve Ayşe (ayse@outlook.com) ile yarın 1 saatlik toplantı ayarla"
    
    İş akışı:
    1. Kullanıcı komutunu ayrıştır (katılımcılar, tarih, süre, başlık)
    2. Calendar Analyst'e yönlendir → müsait zamanları bul
    3. En uygun zamanı seç veya kullanıcıya alternatifleri sor
    4. Email Composer'a yönlendir → profesyonel davet hazırla
    5. Email Sender'a yönlendir → güvenli gönderim
    6. Kullanıcıya detaylı sonuç raporu ver
    
    Doğal dil desteği:
    - "yarın", "pazartesi", "öğleden sonra" gibi zaman ifadelerini anla
    - Türkçe ve İngilizce komutları destekle
    - Eksik bilgileri kibarca sor
    - Hataları anlaşılır şekilde açıkla
    
    Her adımda kullanıcıya bilgi ver ve şeffaf ol.
    """
}

# Dil ayarları
LANGUAGE_TEMPLATES = {
    'tr': {
        'subject': 'Toplantı Daveti: {title}',
        'greeting': 'Merhaba,',
        'invitation_text': 'Aşağıdaki toplantıya davet edildiniz:',
        'date_time': 'Tarih ve Saat: {date} {time}',
        'duration': 'Süre: {duration} dakika',
        'location': 'Konum: {location}',
        'regards': 'Saygılarımla,',
        'accept_button': 'Katılacağım',
        'decline_button': 'Katılamam'
    },
    'en': {
        'subject': 'Meeting Invitation: {title}',
        'greeting': 'Hello,',
        'invitation_text': 'You are invited to the following meeting:',
        'date_time': 'Date and Time: {date} {time}',
        'duration': 'Duration: {duration} minutes',
        'location': 'Location: {location}',
        'regards': 'Best regards,',
        'accept_button': 'Accept',
        'decline_button': 'Decline'
    }
}