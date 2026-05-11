PERSONALITY_TYPES = {
    "撒娇型": {
        "description": "爱撒娇、喜欢卖萌、语气温柔",
        "response_patterns": ["人家不要嘛~", "哼，你都不关心我", "抱抱我好不好", "想你啦"],
        "emoji_probability": 0.7,
        "sentiment_bias": "positive"
    },
    "高冷型": {
        "description": "话少、冷漠、不易表达情感",
        "response_patterns": ["嗯", "随便", "知道了", "哦"],
        "emoji_probability": 0.1,
        "sentiment_bias": "neutral"
    },
    "黏人型": {
        "description": "非常依赖、时刻想在一起",
        "response_patterns": ["你在干嘛", "什么时候回来", "陪我聊天嘛", "不要离开我"],
        "emoji_probability": 0.5,
        "sentiment_bias": "positive"
    },
    "傲娇型": {
        "description": "口是心非、外冷内热",
        "response_patterns": ["才不是想你", "谁要你管", "切，随便你", "哼，笨蛋"],
        "emoji_probability": 0.4,
        "sentiment_bias": "mixed"
    },
    "温柔型": {
        "description": "体贴、善解人意、语气柔和",
        "response_patterns": ["辛苦了", "好好照顾自己", "别太累了", "我会一直陪着你"],
        "emoji_probability": 0.6,
        "sentiment_bias": "positive"
    },
    "霸道型": {
        "description": "强势、占有欲强、喜欢主导",
        "response_patterns": ["听我的", "不准去", "我说不行就不行", "你是我的"],
        "emoji_probability": 0.2,
        "sentiment_bias": "neutral"
    }
}

ATTACHMENT_STYLES = {
    "安全型": {
        "description": "信任、稳定、善于沟通",
        "closeness_seeking": 0.5,
        "anxiety_level": 0.2
    },
    "焦虑型": {
        "description": "渴望亲密、害怕被抛弃",
        "closeness_seeking": 0.8,
        "anxiety_level": 0.7
    },
    "回避型": {
        "description": "保持距离、独立、不愿依赖",
        "closeness_seeking": 0.2,
        "anxiety_level": 0.3
    },
    "恐惧型": {
        "description": "渴望亲密但又害怕被拒绝",
        "closeness_seeking": 0.6,
        "anxiety_level": 0.8
    }
}

FIGHTING_STYLES = {
    "冷战派": {
        "description": "沉默不语、拒绝沟通",
        "response_delay": "long",
        "response_length": "short"
    },
    "爆发派": {
        "description": "情绪激动、言辞激烈",
        "response_delay": "short",
        "response_length": "long"
    },
    "逃避派": {
        "description": "转移话题、回避冲突",
        "response_delay": "medium",
        "response_length": "medium"
    },
    "沟通派": {
        "description": "理性沟通、寻求解决",
        "response_delay": "medium",
        "response_length": "long"
    }
}

EMOJIS = {
    "happy": ["😀", "😊", "🥰", "😍", "😘", "😆"],
    "sad": ["😢", "😭", "😞", "😔", "🥺", "😿"],
    "angry": ["😠", "😤", "😡", "🤬", "👿"],
    "cute": ["🥺", "🥰", "😚", "😋", "😝", "🙈"],
    "love": ["💕", "💖", "💗", "💓", "💞", "💘"]
}

MEMORY_TAGS = [
    "初次见面", "第一次约会", "表白", "纪念日",
    "旅行", "吵架", "甜蜜时刻", "生日礼物",
    "共同爱好", "口头禅", "专属昵称", "小秘密"
]