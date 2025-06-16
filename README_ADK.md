# Google ADK Multi-Agent Meeting Scheduler

Google ADK ve Vertex AI kullanarak geliştirilen gerçek multi-agent toplantı planlama sistemi.

## 🏗️ Sistem Mimarisi

### Multi-Agent Yapısı

1. **Calendar Analyst Agent** (gemini-1.5-flash, temp: 0.1)
   - Google Calendar ve Outlook FreeBusy API entegrasyonu
   - Çalışma saatleri analizi (09:00-18:00)
   - Akıllı zaman dilimi puanlama sistemi
   - Öğle arası ve tatil günü kontrolü

2. **Email Composer Agent** (gemini-1.5-flash, temp: 0.7)
   - Profesyonel HTML e-posta şablonları
   - ICS takvim dosyası oluşturma
   - Çok dilli destek (TR/EN)
   - Responsive e-posta tasarımı

3. **Email Sender Agent** (gemini-1.5-flash, temp: 0.1)
   - SMTP güvenli gönderim
   - Gmail/Outlook SMTP desteği
   - Teslimat takibi ve raporlama
   - Rate limiting ve retry mekanizması

4. **Orchestrator Agent** (gemini-2.0-flash, temp: 0.3)
   - Doğal dil anlama ve ayrıştırma
   - Agent koordinasyonu
   - İş akışı yönetimi
   - Kullanıcı etkileşimi

## 📦 Kurulum

### 1. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 2. Google Cloud Ayarları

```bash
# Google Cloud CLI'yi yükle ve giriş yap
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Vertex AI API'yi aktifleştir
gcloud services enable aiplatform.googleapis.com

# ADK API'yi aktifleştir (Preview)
gcloud services enable adk.googleapis.com
```

### 3. Çevre Değişkenleri

```bash
# Gerekli değişkenler
export GOOGLE_CLOUD_PROJECT="your-project-id"
export SENDER_EMAIL="your-email@gmail.com"
export SENDER_PASSWORD="your-app-password"  # Gmail App Password
export SENDER_NAME="Your Name"

# Opsiyonel Microsoft Graph
export MICROSOFT_CLIENT_ID="your-client-id"
export MICROSOFT_CLIENT_SECRET="your-client-secret"
export MICROSOFT_TENANT_ID="your-tenant-id"
```

### 4. Google Calendar Credentials

```bash
# credentials.json dosyasını indirip proje köküne koy
# Google Cloud Console > APIs & Services > Credentials
```

## 🚀 Çalıştırma

### 1. ADK Multi-Agent Sistemi

```bash
python run_adk.py
```

Seçenekler:
- **İnteraktif Mod**: Komut satırında doğal dil komutları
- **Web Sunucusu**: HTTP API endpoint'i
- **Test Modu**: Sistem testleri

### 2. Klasik Sistem (Fallback)

```bash
python main.py
```

## 📝 Kullanım Örnekleri

### Türkçe Komutlar

```
Ali (ali@gmail.com) ve Ayşe (ayse@outlook.com) ile yarın 1 saatlik toplantı ayarla

Ekiple pazartesi 2 saatlik sprint planlama toplantısı düzenle

john@example.com ile perşembe öğleden sonra 30 dakikalık demo planla
```

### English Commands

```
Schedule a 1-hour meeting with john@example.com tomorrow

Plan a 2-hour retrospective with team@company.com on Friday

Set up a 30-minute demo with client@example.com next week
```

## 🔧 ADK Agent Yapılandırması

### Agent Definitions

```python
# Calendar Analyst
calendar_analyst = Agent(
    name="calendar_analyst",
    model="gemini-1.5-flash",
    temperature=0.1,
    instruction="Uzman takvim analisti...",
    tools=[check_calendar_availability]
)

# Email Composer
email_composer = Agent(
    name="email_composer",
    model="gemini-1.5-flash",
    temperature=0.7,
    instruction="Profesyonel e-posta yazarı...",
    tools=[compose_meeting_invitation]
)

# Email Sender
email_sender = Agent(
    name="email_sender",
    model="gemini-1.5-flash",
    temperature=0.1,
    instruction="Güvenilir e-posta gönderici...",
    tools=[send_meeting_invitations]
)

# Orchestrator
orchestrator = Agent(
    name="meeting_orchestrator",
    model="gemini-2.0-flash",
    temperature=0.3,
    instruction="Akıllı koordinatör...",
    transfer_agents=[calendar_analyst, email_composer, email_sender]
)
```

### ADK App Deployment

```python
from vertexai.preview.reasoning_engines import AdkApp

app = AdkApp(agent=orchestrator)
app.run(port=8080)  # Local development
```

## 🛠️ Tool Functions

### 1. Calendar Availability Check

```python
async def check_calendar_availability(
    participants: List[str], 
    date: str, 
    duration_minutes: int
) -> Dict:
    # FreeBusy API queries
    # Working hours analysis
    # Slot scoring
    return available_slots
```

### 2. Meeting Invitation Composer

```python
def compose_meeting_invitation(
    meeting_details: Dict,
    language: str = "tr"
) -> Dict:
    # HTML email generation
    # ICS file creation
    # Multi-language support
    return email_content
```

### 3. Email Sender

```python
async def send_meeting_invitations(
    email_content: Dict,
    recipients: List[str]
) -> Dict:
    # SMTP secure sending
    # Delivery tracking
    # Error handling
    return send_results
```

## 📊 Özellikler

### ✅ Tamamlanan

- ✅ Google ADK Agent Framework entegrasyonu
- ✅ Vertex AI model yapılandırması
- ✅ Multi-agent koordinasyon sistemi
- ✅ FreeBusy API Google Calendar entegrasyonu
- ✅ Microsoft Graph API Outlook desteği
- ✅ Profesyonel HTML e-posta şablonları
- ✅ ICS takvim dosyası oluşturma
- ✅ SMTP güvenli e-posta gönderimi
- ✅ Doğal dil komut ayrıştırma
- ✅ Çok dilli destek (TR/EN)
- ✅ Çalışma saatleri ve tatil günü kontrolü
- ✅ Akıllı zaman dilimi puanlama
- ✅ Web sunucusu deployment
- ✅ İnteraktif komut satırı arayüzü

### 🚧 Gelecek Geliştirmeler

- 🔄 Microsoft Teams entegrasyonu
- 🔄 Zoom API entegrasyonu
- 🔄 Slack/Discord bot desteği
- 🔄 Tekrarlayan toplantı desteği
- 🔄 Toplantı takip sistemi
- 🔄 Analytics ve raporlama
- 🔄 Mobile app API
- 🔄 Voice command desteği

## 🔐 Güvenlik

- 🔒 SMTP TLS/SSL şifreleme
- 🔒 OAuth2 authentication
- 🔒 App Password kullanımı
- 🔒 Çevre değişkeni güvenliği
- 🔒 Rate limiting
- 🔒 Input validation

## 📈 Performans

- ⚡ Async/await paralel işleme
- ⚡ FreeBusy API batch sorguları
- ⚡ Vertex AI model optimization
- ⚡ SMTP connection pooling
- ⚡ Intelligent caching

## 🐛 Troubleshooting

### Common Issues

1. **Vertex AI hatası**: `GOOGLE_CLOUD_PROJECT` değişkenini kontrol edin
2. **Gmail gönderim hatası**: App Password kullanın
3. **Calendar API hatası**: `credentials.json` dosyasını kontrol edin
4. **ADK import hatası**: `google-adk-agents` versiyonunu güncelleyin

### Debug Mode

```bash
export DEBUG=1
python run_adk.py
```

## 📞 Destek

- 📧 E-posta: support@example.com
- 📖 Dokümantasyon: [Google ADK Docs](https://cloud.google.com/vertex-ai/docs/adk)
- 🐙 GitHub Issues: [Repository](https://github.com/example/meeting-scheduler)

---

**© 2024 - Google ADK Multi-Agent Meeting Scheduler**