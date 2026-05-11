import random
from datetime import datetime
from .config import PERSONALITY_TYPES, ATTACHMENT_STYLES, FIGHTING_STYLES, EMOJIS

class ChatSimulator:
    def __init__(self, persona):
        self.persona = persona
        self.personality = PERSONALITY_TYPES[persona["personality_type"]]
        self.attachment = ATTACHMENT_STYLES[persona["attachment_style"]]
        self.fighting = FIGHTING_STYLES[persona["fighting_style"]]
        self.is_fighting = False
        self.memory_cache = persona["memories"]
    
    def generate_response(self, user_input):
        response = self._generate_base_response(user_input)
        response = self._apply_personality(response)
        response = self._apply_attachment(response)
        response = self._apply_fighting_mode(response)
        response = self._add_emojis(response)
        response = self._inject_memories(response, user_input)
        
        return response
    
    def _generate_base_response(self, user_input):
        greetings = ["你好呀", "嗨~", "在呢", "怎么啦", "想我了吗"]
        questions = ["你呢", "你觉得呢", "是吗", "真的吗"]
        
        if any(greet in user_input for greet in ["你好", "嗨", "哈喽", "在吗"]):
            return random.choice(greetings)
        elif any(word in user_input for word in ["想", "思念", "怀念"]):
            return random.choice([
                "我也想你", 
                "其实我一直都在", 
                "有时候也会想起以前",
                "嗯，我也常常想起"
            ])
        elif any(word in user_input for word in ["爱", "喜欢"]):
            return random.choice([
                "我也爱你",
                "傻瓜",
                "知道啦",
                "你还说这种话"
            ])
        elif any(word in user_input for word in ["吵架", "生气", "对不起"]):
            self.is_fighting = True
            return self._generate_fighting_response()
        else:
            return random.choice([
                "嗯，我在听",
                "继续说呀",
                "然后呢",
                random.choice(questions)
            ])
    
    def _apply_personality(self, response):
        patterns = self.personality["response_patterns"]
        
        if random.random() < 0.3:
            response = random.choice(patterns)
        
        if self.personality["sentiment_bias"] == "positive":
            response = response.replace("嗯", "嗯嗯~")
            response = response.replace("知道了", "知道啦~")
        elif self.personality["sentiment_bias"] == "neutral":
            response = response.replace("~", "")
            response = response.replace("啦", "")
        
        return response
    
    def _apply_attachment(self, response):
        if self.attachment["closeness_seeking"] > 0.6:
            closeness_phrases = ["陪我", "不要离开", "在一起", "想你"]
            if random.random() < 0.2:
                response += " " + random.choice(closeness_phrases)
        
        if self.attachment["anxiety_level"] > 0.5:
            anxiety_phrases = ["你不会离开我吧", "不要不理我", "真的吗"]
            if random.random() < 0.15:
                response = random.choice(anxiety_phrases) + " " + response
        
        return response
    
    def _apply_fighting_mode(self, response):
        if not self.is_fighting:
            return response
        
        if self.fighting["response_length"] == "short":
            response = random.choice(["嗯", "哦", "随便", "知道了"])
        elif self.fighting["response_length"] == "long":
            response = "你到底想怎么样？每次都是这样，我受够了！"
        
        if random.random() < 0.5:
            self.is_fighting = False
        
        return response
    
    def _add_emojis(self, response):
        if random.random() < self.personality["emoji_probability"]:
            if self.personality["sentiment_bias"] == "positive":
                emoji = random.choice(EMOJIS["happy"] + EMOJIS["love"])
            elif self.is_fighting:
                emoji = random.choice(EMOJIS["angry"])
            else:
                emoji = random.choice(EMOJIS["cute"])
            
            if random.random() < 0.5:
                response += emoji
            else:
                response = emoji + response
        
        return response
    
    def _inject_memories(self, response, user_input):
        if not self.memory_cache:
            return response
        
        for memory in self.memory_cache:
            if memory["tag"] in user_input or memory["content"] in user_input:
                memory_ref = f"记得我们{memory['content']}吗？"
                if random.random() < 0.4:
                    response = memory_ref + " " + response
                    break
        
        return response
    
    def toggle_fighting_mode(self, enabled):
        self.is_fighting = enabled
    
    def add_memory(self, memory):
        if memory not in self.memory_cache:
            self.memory_cache.append(memory)