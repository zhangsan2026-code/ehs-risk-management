import json
import os
from datetime import datetime
from .config import PERSONALITY_TYPES, ATTACHMENT_STYLES, FIGHTING_STYLES

class PersonaGenerator:
    def __init__(self):
        self.personas = {}
        self.load_personas()
    
    def load_personas(self):
        if os.path.exists("personas.json"):
            with open("personas.json", "r", encoding="utf-8") as f:
                self.personas = json.load(f)
    
    def save_personas(self):
        with open("personas.json", "w", encoding="utf-8") as f:
            json.dump(self.personas, f, ensure_ascii=False, indent=2)
    
    def create_persona(self, name, personality_type, attachment_style, fighting_style, 
                       memories=None, chat_history=None, photo_url=None):
        persona_id = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        persona = {
            "id": persona_id,
            "name": name,
            "personality_type": personality_type,
            "attachment_style": attachment_style,
            "fighting_style": fighting_style,
            "memories": memories or [],
            "chat_history": chat_history or [],
            "photo_url": photo_url,
            "created_at": datetime.now().isoformat(),
            "last_interaction": None,
            "interaction_count": 0
        }
        
        self.personas[persona_id] = persona
        self.save_personas()
        return persona
    
    def get_persona(self, persona_id):
        return self.personas.get(persona_id)
    
    def update_persona(self, persona_id, updates):
        if persona_id in self.personas:
            self.personas[persona_id].update(updates)
            self.save_personas()
            return True
        return False
    
    def delete_persona(self, persona_id):
        if persona_id in self.personas:
            del self.personas[persona_id]
            self.save_personas()
            return True
        return False
    
    def get_all_personas(self):
        return list(self.personas.values())
    
    def analyze_chat_history(self, chat_history):
        patterns = {
            "avg_message_length": 0,
            "response_time_pattern": "mixed",
            "favorite_topics": [],
            "emoji_frequency": 0,
            "sentiment_trend": "neutral"
        }
        
        if not chat_history:
            return patterns
        
        total_length = sum(len(msg["content"]) for msg in chat_history)
        patterns["avg_message_length"] = total_length / len(chat_history)
        
        emoji_count = sum(msg["content"].count(c) for msg in chat_history 
                          for c in "😀😃😄😁😆😅🤣😂🙂😊😇🥰😍🤩😘😗😚😙🥲😋😛")
        patterns["emoji_frequency"] = emoji_count / len(chat_history)
        
        return patterns
    
    def suggest_personality(self, chat_history):
        analysis = self.analyze_chat_history(chat_history)
        
        if analysis["emoji_frequency"] > 0.5:
            return "撒娇型" if analysis["avg_message_length"] < 20 else "温柔型"
        elif analysis["avg_message_length"] < 10:
            return "高冷型"
        else:
            return "温柔型"