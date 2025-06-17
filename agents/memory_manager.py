#!/usr/bin/env python3
"""
Memory & Context Management for Meeting Scheduler Agents
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class ConversationTurn:
    """Tek konuşma turunu temsil eder"""
    timestamp: str
    user_input: str
    agent_response: str
    parsed_data: Dict[str, Any]
    success: bool
    meeting_created: bool = False
    meeting_id: Optional[str] = None


@dataclass
class UserProfile:
    """Kullanıcı profil bilgileri"""
    user_id: str
    email: str
    name: Optional[str] = None
    timezone: str = "Europe/Istanbul"
    preferred_meeting_duration: int = 60
    preferred_meeting_times: List[str] = None
    frequent_participants: List[str] = None
    meeting_preferences: Dict[str, Any] = None
    last_interaction: Optional[str] = None
    total_meetings_scheduled: int = 0
    
    def __post_init__(self):
        if self.preferred_meeting_times is None:
            self.preferred_meeting_times = ["10:00", "14:00", "15:00"]
        if self.frequent_participants is None:
            self.frequent_participants = []
        if self.meeting_preferences is None:
            self.meeting_preferences = {}


@dataclass
class MeetingMemory:
    """Toplantı hafıza kaydı"""
    meeting_id: str
    title: str
    participants: List[str]
    organizer: str
    date: str
    time: str
    duration: int
    status: str  # scheduled, completed, cancelled
    created_at: str
    calendar_event_id: Optional[str] = None
    notes: Optional[str] = None


class MemoryManager:
    """Toplantı planlayıcı için hafıza ve context yönetimi"""
    
    def __init__(self, memory_file: str = "memory_data.json"):
        self.memory_file = memory_file
        self.conversation_history: List[ConversationTurn] = []
        self.user_profiles: Dict[str, UserProfile] = {}
        self.meeting_history: List[MeetingMemory] = []
        self.current_context: Dict[str, Any] = {}
        self.session_data: Dict[str, Any] = {}
        
        # Dosyadan hafıza yükle
        self._load_memory()
    
    def _load_memory(self):
        """Hafızayı dosyadan yükle"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Conversation history yükle
                self.conversation_history = [
                    ConversationTurn(**turn) for turn in data.get('conversation_history', [])
                ]
                
                # User profiles yükle
                self.user_profiles = {
                    user_id: UserProfile(**profile) 
                    for user_id, profile in data.get('user_profiles', {}).items()
                }
                
                # Meeting history yükle
                self.meeting_history = [
                    MeetingMemory(**meeting) for meeting in data.get('meeting_history', [])
                ]
                
                print("💾 Hafıza başarıyla yüklendi")
                
            except Exception as e:
                print(f"⚠️ Hafıza yükleme hatası: {e}")
                self._initialize_empty_memory()
        else:
            self._initialize_empty_memory()
    
    def _initialize_empty_memory(self):
        """Boş hafıza başlat"""
        self.conversation_history = []
        self.user_profiles = {}
        self.meeting_history = []
        print("💾 Yeni hafıza başlatıldı")
    
    def save_memory(self):
        """Hafızayı dosyaya kaydet"""
        try:
            data = {
                'conversation_history': [asdict(turn) for turn in self.conversation_history],
                'user_profiles': {
                    user_id: asdict(profile) 
                    for user_id, profile in self.user_profiles.items()
                },
                'meeting_history': [asdict(meeting) for meeting in self.meeting_history],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            print("💾 Hafıza kaydedildi")
            
        except Exception as e:
            print(f"❌ Hafıza kaydetme hatası: {e}")
    
    def add_conversation_turn(self, user_input: str, agent_response: str, 
                            parsed_data: Dict[str, Any], success: bool,
                            meeting_id: Optional[str] = None):
        """Yeni konuşma turu ekle"""
        turn = ConversationTurn(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            agent_response=agent_response,
            parsed_data=parsed_data,
            success=success,
            meeting_created=meeting_id is not None,
            meeting_id=meeting_id
        )
        
        self.conversation_history.append(turn)
        
        # Son 50 konuşmayı tut (hafıza optimizasyonu)
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
        
        self.save_memory()
    
    def get_or_create_user_profile(self, user_email: str) -> UserProfile:
        """Kullanıcı profilini getir veya oluştur"""
        if user_email not in self.user_profiles:
            self.user_profiles[user_email] = UserProfile(
                user_id=user_email,
                email=user_email,
                last_interaction=datetime.now().isoformat()
            )
        else:
            self.user_profiles[user_email].last_interaction = datetime.now().isoformat()
        
        return self.user_profiles[user_email]
    
    def update_user_preferences(self, user_email: str, preferences: Dict[str, Any]):
        """Kullanıcı tercihlerini güncelle"""
        profile = self.get_or_create_user_profile(user_email)
        
        if 'preferred_duration' in preferences:
            profile.preferred_meeting_duration = preferences['preferred_duration']
        
        if 'preferred_times' in preferences:
            profile.preferred_meeting_times = preferences['preferred_times']
        
        if 'name' in preferences:
            profile.name = preferences['name']
        
        if 'timezone' in preferences:
            profile.timezone = preferences['timezone']
        
        self.save_memory()
    
    def add_frequent_participant(self, user_email: str, participant_email: str):
        """Sık kullanılan katılımcı ekle"""
        profile = self.get_or_create_user_profile(user_email)
        
        if participant_email not in profile.frequent_participants:
            profile.frequent_participants.append(participant_email)
        
        # En çok kullanılan 10 kişiyi tut
        if len(profile.frequent_participants) > 10:
            profile.frequent_participants = profile.frequent_participants[-10:]
        
        self.save_memory()
    
    def add_meeting_to_history(self, meeting_data: Dict[str, Any]) -> str:
        """Toplantıyı hafızaya ekle"""
        meeting_id = meeting_data.get('meeting_id', f"meeting_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        meeting = MeetingMemory(
            meeting_id=meeting_id,
            title=meeting_data.get('title', 'Toplantı'),
            participants=meeting_data.get('participants', []),
            organizer=meeting_data.get('organizer', ''),
            date=meeting_data.get('date', ''),
            time=meeting_data.get('start_time', ''),
            duration=meeting_data.get('duration', 60),
            status='scheduled',
            created_at=datetime.now().isoformat(),
            calendar_event_id=meeting_data.get('calendar_event_id'),
            notes=meeting_data.get('notes')
        )
        
        self.meeting_history.append(meeting)
        
        # Kullanıcı toplantı sayısını artır
        organizer_profile = self.get_or_create_user_profile(meeting.organizer)
        organizer_profile.total_meetings_scheduled += 1
        
        # Sık kullanılan katılımcıları güncelle
        for participant in meeting.participants:
            self.add_frequent_participant(meeting.organizer, participant)
        
        self.save_memory()
        return meeting_id
    
    def get_recent_meetings(self, user_email: str, days: int = 30) -> List[MeetingMemory]:
        """Son X gün içindeki toplantıları getir"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_meetings = []
        for meeting in self.meeting_history:
            if (meeting.organizer == user_email or user_email in meeting.participants):
                meeting_date = datetime.fromisoformat(meeting.created_at)
                if meeting_date >= cutoff_date:
                    recent_meetings.append(meeting)
        
        return sorted(recent_meetings, key=lambda m: m.created_at, reverse=True)
    
    def get_similar_past_meetings(self, participants: List[str], organizer: str) -> List[MeetingMemory]:
        """Benzer geçmiş toplantıları bul"""
        similar_meetings = []
        
        for meeting in self.meeting_history:
            if meeting.organizer == organizer:
                # Katılımcı benzerliği kontrol et
                common_participants = set(participants) & set(meeting.participants)
                if len(common_participants) > 0:
                    similar_meetings.append(meeting)
        
        return sorted(similar_meetings, key=lambda m: m.created_at, reverse=True)[:5]
    
    def get_user_stats(self, user_email: str) -> Dict[str, Any]:
        """Kullanıcı istatistiklerini getir"""
        profile = self.user_profiles.get(user_email)
        if not profile:
            return {}
        
        recent_meetings = self.get_recent_meetings(user_email, 30)
        
        return {
            'total_meetings': profile.total_meetings_scheduled,
            'recent_meetings_count': len(recent_meetings),
            'frequent_participants': profile.frequent_participants,
            'preferred_duration': profile.preferred_meeting_duration,
            'preferred_times': profile.preferred_meeting_times,
            'last_interaction': profile.last_interaction
        }
    
    def get_context_suggestions(self, current_request: str, user_email: str) -> Dict[str, Any]:
        """Mevcut istek için context önerileri"""
        suggestions = {
            'similar_meetings': [],
            'frequent_participants': [],
            'preferred_time': None,
            'preferred_duration': 60
        }
        
        profile = self.user_profiles.get(user_email)
        if profile:
            suggestions['frequent_participants'] = profile.frequent_participants
            suggestions['preferred_duration'] = profile.preferred_meeting_duration
            suggestions['preferred_time'] = profile.preferred_meeting_times[0] if profile.preferred_meeting_times else None
        
        # Benzer toplantıları bul
        if user_email in self.user_profiles:
            # Basit keyword matching ile benzer toplantıları bul
            request_lower = current_request.lower()
            for meeting in self.meeting_history[-10:]:  # Son 10 toplantıya bak
                if meeting.organizer == user_email:
                    title_words = meeting.title.lower().split()
                    if any(word in request_lower for word in title_words):
                        suggestions['similar_meetings'].append({
                            'title': meeting.title,
                            'participants': meeting.participants,
                            'duration': meeting.duration,
                            'time': meeting.time
                        })
        
        return suggestions
    
    def update_context(self, key: str, value: Any):
        """Mevcut session context'i güncelle"""
        self.current_context[key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Context değeri getir"""
        return self.current_context.get(key, default)
    
    def clear_context(self):
        """Context'i temizle"""
        self.current_context.clear()
    
    def get_conversation_summary(self, limit: int = 5) -> str:
        """Son konuşmaların özetini getir"""
        if not self.conversation_history:
            return "Henüz konuşma geçmişi yok."
        
        recent_turns = self.conversation_history[-limit:]
        summary_parts = []
        
        for turn in recent_turns:
            status = "✅" if turn.success else "❌"
            summary_parts.append(f"{status} {turn.user_input[:50]}...")
        
        return "\n".join(summary_parts)
    
    def analyze_user_patterns(self, user_email: str) -> Dict[str, Any]:
        """Kullanıcı davranış paternlerini analiz et"""
        if user_email not in self.user_profiles:
            return {}
        
        user_meetings = [m for m in self.meeting_history if m.organizer == user_email]
        
        if not user_meetings:
            return {}
        
        # En çok kullanılan süre
        durations = [m.duration for m in user_meetings]
        most_common_duration = max(set(durations), key=durations.count)
        
        # En çok kullanılan katılımcılar
        all_participants = []
        for meeting in user_meetings:
            all_participants.extend(meeting.participants)
        
        participant_counts = defaultdict(int)
        for participant in all_participants:
            participant_counts[participant] += 1
        
        top_participants = sorted(participant_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # En çok kullanılan gün/saat
        meeting_times = [m.time for m in user_meetings if m.time]
        most_common_time = max(set(meeting_times), key=meeting_times.count) if meeting_times else None
        
        return {
            'most_common_duration': most_common_duration,
            'top_participants': [p[0] for p in top_participants],
            'most_common_time': most_common_time,
            'total_meetings': len(user_meetings),
            'average_duration': sum(durations) / len(durations) if durations else 60
        }