import asyncio
import aiohttp
import json
import os
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

LOCATION_CONFIG = {
    "address": "珠海市高新区金业南路",
    "latitude": 22.3333,
    "longitude": 113.5500,
    "city": "珠海",
    "district": "高新区"
}

API_KEYS = {
    "newsapi": "7a3b8c9d4e5f6a7b8c9d0e1f2a3b4c5d",
    "amap": "b63327aeddbcd2c7133a0cffc19bda3c"
}

RISK_LEVELS = {
    "safe": {"level": 0, "label": "安全", "color": colors.green, "bg_color": colors.Color(0.8, 0.95, 0.8), "threshold": 20},
    "low": {"level": 1, "label": "低风险", "color": colors.darkgoldenrod, "bg_color": colors.Color(0.95, 0.95, 0.8), "threshold": 40},
    "medium": {"level": 2, "label": "中风险", "color": colors.orange, "bg_color": colors.Color(1.0, 0.85, 0.7), "threshold": 60},
    "high": {"level": 3, "label": "高风险", "color": colors.red, "bg_color": colors.Color(1.0, 0.85, 0.85), "threshold": 80},
    "critical": {"level": 4, "label": "极高风险", "color": colors.darkred, "bg_color": colors.Color(0.95, 0.8, 0.9), "threshold": 100}
}

RISK_WEIGHTS = {
    "weather": 0.20,
    "social_media": 0.25,
    "security": 0.20,
    "traffic": 0.10,
    "fire": 0.25
}

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "risk_reports")

def get_chinese_font_path():
    font_paths = [
        "C:/Windows/Fonts/simsun.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/msyh.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
    ]
    for path in font_paths:
        if os.path.exists(path):
            return path
    return None

CHINESE_FONT_PATH = get_chinese_font_path()
CHINESE_FONT_NAME = "ChineseFont"


class RiskMonitor:
    def __init__(self):
        self.session = None
        self.last_update = None
        self.risk_data = {}
        self.api_status = {}
        self.hourly_forecasts = []

    async def init_session(self):
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session and not self.session.closed:
            await self.session.close()

    def check_api_keys(self) -> Dict[str, bool]:
        return {
            "newsapi": API_KEYS.get("newsapi") and API_KEYS["newsapi"] != "your_newsapi_key",
            "amap": API_KEYS.get("amap") and API_KEYS["amap"] != "your_amap_key"
        }

    async def fetch_weather(self) -> Dict[str, Any]:
        try:
            await self.init_session()
            url = f"https://api.open-meteo.com/v1/forecast?latitude={LOCATION_CONFIG['latitude']}&longitude={LOCATION_CONFIG['longitude']}&hourly=temperature_2m,weather_code,wind_speed_10m,precipitation_probability&daily=weather_code,temperature_2m_max,temperature_2m_min&current_weather=true&timezone=Asia/Shanghai&forecast_days=3"

            async with self.session.get(url, timeout=10) as resp:
                data = await resp.json()

            weather_code = data['current_weather']['weathercode']
            temperature = data['current_weather']['temperature']
            wind_speed = data['current_weather']['windspeed']

            hourly_data = data.get('hourly', {})
            times = hourly_data.get('time', [])
            weather_codes = hourly_data.get('weather_code', [])
            temps = hourly_data.get('temperature_2m', [])
            winds = hourly_data.get('wind_speed_10m', [])
            precip = hourly_data.get('precipitation_probability', [])

            weather_map = {
                0: "晴天", 1: "晴", 2: "多云", 3: "阴天",
                45: "雾", 48: "雾凇",
                51: "小雨", 53: "中雨", 55: "大雨",
                61: "阵雨", 63: "阵中雨", 65: "阵大雨",
                71: "小雪", 73: "中雪", 75: "大雪",
                80: "雷阵雨", 81: "雷阵中雨", 82: "雷阵大雨",
                95: "雷暴", 96: "雷暴伴冰雹", 99: "强雷暴伴冰雹"
            }

            self.hourly_forecasts = []

            for i in range(12):
                idx = i
                if idx < len(times):
                    forecast_time = datetime.fromisoformat(times[idx].replace('Z', '+00:00'))
                    local_time = forecast_time + timedelta(hours=8)
                    wc = weather_codes[idx] if idx < len(weather_codes) else 0
                    severe_alerts = []

                    if wc in [55, 65, 82, 95, 96, 99]:
                        severe_alerts.append(f"极端天气: {weather_map.get(wc, '未知')}")
                    if idx < len(winds) and winds[idx] >= 20:
                        severe_alerts.append(f"大风: {winds[idx]}km/h")
                    if idx < len(precip) and precip[idx] >= 80:
                        severe_alerts.append(f"强降水: {precip[idx]}%")

                    self.hourly_forecasts.append({
                        "hour": local_time.strftime("%H:00"),
                        "weather": weather_map.get(wc, f"未知({wc})"),
                        "temp": temps[idx] if idx < len(temps) else 0,
                        "wind": winds[idx] if idx < len(winds) else 0,
                        "precip": precip[idx] if idx < len(precip) else 0,
                        "severe_alerts": severe_alerts,
                        "risk_score": len(severe_alerts) * 15
                    })

            weather_desc = weather_map.get(weather_code, f"未知({weather_code})")
            severe_alerts = []

            if weather_code in [55, 65, 82, 95, 96, 99]:
                severe_alerts.append(f"极端天气预警: {weather_desc}")
            if wind_speed >= 20:
                severe_alerts.append(f"大风预警: {wind_speed} km/h")

            self.api_status["weather"] = "success"

            return {
                "status": "success",
                "source": "Open-Meteo",
                "current_temp": temperature,
                "weather": weather_desc,
                "weather_code": weather_code,
                "wind_speed": wind_speed,
                "severe_alerts": severe_alerts,
                "risk_score": len(severe_alerts) * 15,
                "hourly_forecasts": self.hourly_forecasts
            }
        except Exception as e:
            self.api_status["weather"] = f"error: {str(e)}"
            return {
                "status": "error",
                "message": str(e),
                "source": "Open-Meteo",
                "risk_score": 0,
                "hourly_forecasts": []
            }

    async def fetch_social_media(self, keywords: List[str] = None) -> Dict[str, Any]:
        if keywords is None:
            keywords = [
                "珠海华润银行", "华润银行", "珠海高新区", "珠海银行", "金融风险", "银行安全",
                "金融舆情", "银行负面", "金融投诉", "银行问题", "金融诈骗", "银行违规",
                "珠海金融", "粤港澳金融", "银行监管", "金融稳定", "银行舆情", "金融事件"
            ]

        try:
            await self.init_session()

            newsapi_key = API_KEYS.get("newsapi")
            if not newsapi_key or newsapi_key == "your_newsapi_key":
                return {
                    "status": "error",
                    "message": "NewsAPI密钥未配置",
                    "source": "NewsAPI",
                    "risk_score": 0,
                    "requires_config": True,
                    "suggestion": "请在API_KEYS中配置NewsAPI密钥以获取舆情数据"
                }

            url = f"https://newsapi.org/v2/everything?q={' OR '.join(keywords)}&language=zh&sortBy=publishedAt&pageSize=50&apiKey={newsapi_key}"

            async with self.session.get(url, timeout=15) as resp:
                data = await resp.json()

            if data.get('status') != 'ok':
                return {
                    "status": "error",
                    "message": data.get('message', 'Unknown error'),
                    "source": "NewsAPI",
                    "risk_score": 0
                }

            articles = data.get('articles', [])
            total_posts = len(articles)

            risk_keywords = [
                "风险", "事故", "安全", "问题", "投诉", "负面", "倒闭", "诈骗", "违规", "调查",
                "危机", "暴雷", "跑路", "坏账", "违约", "破产", "查封", "冻结", "维权",
                "抗议", "纠纷", "诉讼", "处罚", "警告", "通报", "黑幕", "丑闻", "造假"
            ]
            
            negative_keywords = [
                "负面", "差评", "不满", "抱怨", "指责", "批评", "投诉", "举报", "曝光"
            ]
            
            risk_posts = 0
            negative_posts = 0
            article_details = []
            
            for article in articles[:10]:
                title = article.get('title', '')
                desc = article.get('description', '')
                content = title + desc
                
                has_risk = any(keyword in content for keyword in risk_keywords)
                has_negative = any(keyword in content for keyword in negative_keywords)
                
                if has_risk:
                    risk_posts += 1
                if has_negative:
                    negative_posts += 1
                
                if has_risk or has_negative:
                    article_details.append({
                        "title": title,
                        "source": article.get('source', {}).get('name', ''),
                        "url": article.get('url', ''),
                        "risk_type": "风险" if has_risk else "负面"
                    })

            sentiment_score = 1 - ((risk_posts + negative_posts) / max(total_posts * 2, 1))
            
            self.api_status["newsapi"] = "success"

            return {
                "status": "success",
                "source": "NewsAPI",
                "total_posts": total_posts,
                "risk_posts": risk_posts,
                "negative_posts": negative_posts,
                "sentiment_score": sentiment_score,
                "sentiment_label": "正面" if sentiment_score > 0.7 else "中性" if sentiment_score > 0.4 else "负面",
                "risk_score": min((risk_posts * 3 + negative_posts * 2), 35),
                "article_details": article_details[:5],
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.api_status["newsapi"] = f"error: {str(e)}"
            return self._get_social_media_mock_data()

    def _get_social_media_mock_data(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "source": "模拟数据",
            "total_posts": 25,
            "risk_posts": 3,
            "negative_posts": 2,
            "sentiment_score": 0.72,
            "sentiment_label": "正面",
            "risk_score": 13,
            "article_details": [
                {
                    "title": "珠海华润银行发布年度业绩报告，净利润同比增长15%",
                    "source": "财经新闻网",
                    "url": "#",
                    "risk_type": "风险"
                },
                {
                    "title": "监管部门对珠海部分银行进行合规检查",
                    "source": "金融时报",
                    "url": "#",
                    "risk_type": "风险"
                },
                {
                    "title": "市民投诉某银行服务态度问题",
                    "source": "本地新闻",
                    "url": "#",
                    "risk_type": "负面"
                },
                {
                    "title": "珠海高新区金融产业发展迅速，多家银行入驻",
                    "source": "经济日报",
                    "url": "#",
                    "risk_type": "风险"
                },
                {
                    "title": "银行理财产品收益下降引发投资者不满",
                    "source": "证券时报",
                    "url": "#",
                    "risk_type": "负面"
                }
            ],
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "note": "数据来自模拟，配置NewsAPI密钥后获取真实数据"
        }

    async def fetch_traffic(self) -> Dict[str, Any]:
        try:
            await self.init_session()

            amap_key = API_KEYS.get("amap")
            if not amap_key or amap_key == "your_amap_key":
                return {
                    "status": "error",
                    "message": "高德地图API密钥未配置",
                    "source": "高德地图",
                    "risk_score": 0,
                    "requires_config": True
                }

            url = f"https://restapi.amap.com/v3/traffic/status/circle?location={LOCATION_CONFIG['longitude']},{LOCATION_CONFIG['latitude']}&radius=3000&key={amap_key}"

            async with self.session.get(url, timeout=10) as resp:
                data = await resp.json()

            status = data.get('status')
            if status != '1':
                return {
                    "status": "error",
                    "message": data.get('info', 'API返回状态异常'),
                    "source": "高德地图",
                    "risk_score": 0
                }

            roads = data.get('trafficinfo', {}).get('roads', [])
            congestion_count = {"畅通": 0, "缓行": 0, "拥堵": 0}

            for road in roads[:10]:
                road_status = road.get('status')
                status_text = ["畅通", "缓行", "拥堵"][int(road_status) - 1] if road_status in ['1', '2', '3'] else "未知"
                congestion_count[status_text] = congestion_count.get(status_text, 0) + 1

            if congestion_count["拥堵"] > 0:
                congestion_level = "拥堵"
                risk_score = 15
            elif congestion_count["缓行"] > 0:
                congestion_level = "缓行"
                risk_score = 8
            else:
                congestion_level = "畅通"
                risk_score = 0

            self.api_status["amap"] = "success"

            return {
                "status": "success",
                "source": "高德地图",
                "congestion_level": congestion_level,
                "risk_score": min(risk_score, 20)
            }
        except Exception as e:
            self.api_status["amap"] = f"error: {str(e)}"
            return {
                "status": "error",
                "message": str(e),
                "source": "高德地图",
                "risk_score": 0
            }

    async def fetch_fire_info(self) -> Dict[str, Any]:
        try:
            await self.init_session()

            newsapi_key = API_KEYS.get("newsapi")
            if not newsapi_key or newsapi_key == "your_newsapi_key":
                return self._get_fire_mock_data()

            keywords = [
                "珠海 火灾", "珠海 消防", "珠海 火情", "珠海 着火",
                "珠海 消防救援", "珠海 火灾事故", "珠海 消防演练",
                "香洲 火灾", "斗门 火灾", "金湾 火灾", "高新区 火灾",
                "华润银行 火灾", "银行 火灾", "大厦 火灾", "写字楼 火灾",
                "高层建筑 火灾", "消防隐患", "消防检查", "消防整改"
            ]

            url = f"https://newsapi.org/v2/everything?q={' OR '.join(keywords)}&language=zh&sortBy=publishedAt&pageSize=20&apiKey={newsapi_key}"

            async with self.session.get(url, timeout=15) as resp:
                data = await resp.json()

            if data.get('status') != 'ok':
                return self._get_fire_mock_data()

            articles = data.get('articles', [])
            
            fire_keywords = ["火灾", "着火", "火情", "消防救援", "火灾事故"]
            hazard_keywords = ["消防隐患", "消防检查", "消防整改", "安全隐患"]
            
            fire_count = 0
            hazard_count = 0
            fire_details = []
            
            for article in articles[:10]:
                title = article.get('title', '')
                desc = article.get('description', '')
                content = title + desc
                
                is_fire = any(kw in content for kw in fire_keywords)
                is_hazard = any(kw in content for kw in hazard_keywords)
                
                if is_fire or is_hazard:
                    fire_details.append({
                        "title": title[:50] + "..." if len(title) > 50 else title,
                        "source": article.get('source', {}).get('name', ''),
                        "type": "火灾事件" if is_fire else "隐患排查",
                        "severity": "严重" if is_fire else "一般"
                    })
                    if is_fire:
                        fire_count += 1
                    if is_hazard:
                        hazard_count += 1

            risk_score = min(fire_count * 10 + hazard_count * 5, 25)
            
            fire_status = "安全"
            if fire_count > 0:
                fire_status = "有火灾记录"
            elif hazard_count > 0:
                fire_status = "有隐患"
            else:
                fire_status = "安全"

            self.api_status["fire"] = "success"

            return {
                "status": "success",
                "source": "NewsAPI",
                "fire_status": fire_status,
                "fire_count": fire_count,
                "hazard_count": hazard_count,
                "fire_details": fire_details[:5],
                "risk_score": risk_score,
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.api_status["fire"] = f"error: {str(e)}"
            return self._get_fire_mock_data()

    def _get_fire_mock_data(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "source": "模拟数据",
            "fire_status": "安全",
            "fire_count": 0,
            "hazard_count": 1,
            "fire_details": [
                {
                    "title": "高新区开展消防安全隐患排查",
                    "source": "珠海消防",
                    "type": "隐患排查",
                    "severity": "一般"
                },
                {
                    "title": "春季防火安全提醒",
                    "source": "消防部门",
                    "type": "隐患排查",
                    "severity": "一般"
                }
            ],
            "risk_score": 5,
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "note": "数据来自模拟，配置NewsAPI密钥后获取真实数据"
        }

    async def fetch_security_info(self) -> Dict[str, Any]:
        try:
            await self.init_session()

            newsapi_key = API_KEYS.get("newsapi")
            if not newsapi_key or newsapi_key == "your_newsapi_key":
                return {
                    "status": "error",
                    "message": "NewsAPI密钥未配置",
                    "source": "NewsAPI",
                    "risk_score": 0,
                    "requires_config": True,
                    "suggestion": "请在API_KEYS中配置NewsAPI密钥以获取治安数据"
                }

            keywords = [
                "珠海 治安", "珠海 警情", "珠海 安全", "珠海 案件", "珠海 警方", "珠海 公安",
                "珠海 犯罪", "珠海 盗窃", "珠海 抢劫", "珠海 诈骗", "珠海 火灾", "珠海 事故",
                "珠海 打架", "珠海 斗殴", "珠海 伤人", "珠海 命案", "珠海 枪击", "珠海 爆炸",
                "香洲 治安", "斗门 治安", "金湾 治安", "高新区 治安", "横琴 治安", "拱北 治安"
            ]
            url = f"https://newsapi.org/v2/everything?q={' OR '.join(keywords)}&language=zh&sortBy=publishedAt&pageSize=30&apiKey={newsapi_key}"

            async with self.session.get(url, timeout=15) as resp:
                data = await resp.json()

            if data.get('status') != 'ok':
                return {
                    "status": "error",
                    "message": data.get('message', 'Unknown error'),
                    "source": "NewsAPI",
                    "risk_score": 0
                }

            articles = data.get('articles', [])
            
            violent_keywords = ["杀人", "命案", "枪击", "爆炸", "伤人", "重伤", "死亡", "斗殴", "持刀"]
            theft_keywords = ["盗窃", "偷窃", "扒窃", "偷盗", "入室", "盗窃案"]
            fraud_keywords = ["诈骗", "骗", "虚假", "套路", "传销", "非法集资"]
            fire_keywords = ["火灾", "着火", "失火", "火情"]
            traffic_keywords = ["车祸", "事故", "撞人", "逃逸", "交通事故"]
            
            violent_count = 0
            theft_count = 0
            fraud_count = 0
            fire_count = 0
            traffic_count = 0
            incident_details = []
            
            for article in articles[:15]:
                title = article.get('title', '')
                desc = article.get('description', '')
                content = title + desc
                
                incident_type = []
                if any(kw in content for kw in violent_keywords):
                    violent_count += 1
                    incident_type.append("暴力")
                if any(kw in content for kw in theft_keywords):
                    theft_count += 1
                    incident_type.append("盗窃")
                if any(kw in content for kw in fraud_keywords):
                    fraud_count += 1
                    incident_type.append("诈骗")
                if any(kw in content for kw in fire_keywords):
                    fire_count += 1
                    incident_type.append("火灾")
                if any(kw in content for kw in traffic_keywords):
                    traffic_count += 1
                    incident_type.append("交通")
                
                if incident_type:
                    incident_details.append({
                        "title": title[:50] + "..." if len(title) > 50 else title,
                        "source": article.get('source', {}).get('name', ''),
                        "incident_types": incident_type,
                        "severity": "严重" if "暴力" in incident_type or "火灾" in incident_type else "一般"
                    })

            total_incidents = violent_count + theft_count + fraud_count + fire_count + traffic_count
            
            if violent_count > 0 or fire_count > 0:
                safety_level = "需关注"
                risk_multiplier = 2
            elif total_incidents <= 2:
                safety_level = "良好"
                risk_multiplier = 1
            elif total_incidents <= 5:
                safety_level = "一般"
                risk_multiplier = 1.5
            else:
                safety_level = "需关注"
                risk_multiplier = 1.8

            risk_score = min(total_incidents * 3 * risk_multiplier, 35)
            
            self.api_status["security"] = "success"

            return {
                "status": "success",
                "source": "NewsAPI",
                "district": LOCATION_CONFIG["district"],
                "overall_safety": safety_level,
                "total_incidents": total_incidents,
                "violent_count": violent_count,
                "theft_count": theft_count,
                "fraud_count": fraud_count,
                "fire_count": fire_count,
                "traffic_count": traffic_count,
                "incident_details": incident_details[:5],
                "risk_score": round(risk_score),
                "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            self.api_status["security"] = f"error: {str(e)}"
            return self._get_security_mock_data()

    def _get_security_mock_data(self) -> Dict[str, Any]:
        return {
            "status": "success",
            "source": "模拟数据",
            "district": LOCATION_CONFIG["district"],
            "overall_safety": "良好",
            "total_incidents": 3,
            "violent_count": 0,
            "theft_count": 1,
            "fraud_count": 2,
            "fire_count": 0,
            "traffic_count": 0,
            "incident_details": [
                {
                    "title": "高新区某小区发生入室盗窃案件",
                    "source": "珠海公安",
                    "incident_types": ["盗窃"],
                    "severity": "一般"
                },
                {
                    "title": "市民遭遇网络诈骗，损失金额较大",
                    "source": "警方通报",
                    "incident_types": ["诈骗"],
                    "severity": "一般"
                },
                {
                    "title": "警惕！新型电信诈骗手段出现",
                    "source": "反诈中心",
                    "incident_types": ["诈骗"],
                    "severity": "一般"
                }
            ],
            "risk_score": 9,
            "updated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "note": "数据来自模拟，配置NewsAPI密钥后获取真实数据"
        }

    def predict_risk(self, hourly_data: List[Dict]) -> Dict[str, Any]:
        if not hourly_data:
            return {"prediction": "无法预测", "peak_risk": 0, "peak_time": None, "warnings": []}

        warnings = []
        max_risk = 0
        peak_time = None

        for forecast in hourly_data:
            hour = forecast.get("hour", "")
            risk = forecast.get("risk_score", 0)
            alerts = forecast.get("severe_alerts", [])

            if risk > max_risk:
                max_risk = risk
                peak_time = hour

            if alerts:
                for alert in alerts:
                    warnings.append(f"{hour}: {alert}")

        if max_risk >= 30:
            prediction = "高风险预警"
        elif max_risk >= 15:
            prediction = "中等风险"
        else:
            prediction = "安全"

        return {
            "prediction": prediction,
            "peak_risk": max_risk,
            "peak_time": peak_time,
            "warnings": warnings,
            "hours_ahead": len(hourly_data)
        }

    async def get_risk_assessment(self) -> Dict[str, Any]:
        weather_data = await self.fetch_weather()
        social_data = await self.fetch_social_media()
        security_data = await self.fetch_security_info()
        traffic_data = await self.fetch_traffic()
        fire_data = await self.fetch_fire_info()

        hourly_forecasts = weather_data.get("hourly_forecasts", [])
        prediction = self.predict_risk(hourly_forecasts)

        current_risk = sum([
            weather_data.get("risk_score", 0) * RISK_WEIGHTS["weather"],
            social_data.get("risk_score", 0) * RISK_WEIGHTS["social_media"],
            security_data.get("risk_score", 0) * RISK_WEIGHTS["security"],
            traffic_data.get("risk_score", 0) * RISK_WEIGHTS["traffic"],
            fire_data.get("risk_score", 0) * RISK_WEIGHTS["fire"]
        ])

        predicted_risk = current_risk + prediction["peak_risk"] * 0.3

        risk_level = "safe"
        for level in ["critical", "high", "medium", "low", "safe"]:
            if current_risk >= RISK_LEVELS[level]["threshold"]:
                risk_level = level
                break

        self.last_update = datetime.now()
        self.risk_data = {
            "timestamp": self.last_update.isoformat(),
            "location": LOCATION_CONFIG["address"],
            "current_score": round(current_risk, 1),
            "predicted_score": round(predicted_risk, 1),
            "risk_level": RISK_LEVELS[risk_level],
            "components": {
                "weather": weather_data,
                "social_media": social_data,
                "security": security_data,
                "traffic": traffic_data,
                "fire": fire_data
            },
            "prediction": prediction,
            "api_status": self.api_status.copy(),
            "recommendations": self._generate_recommendations(current_risk, predicted_risk, weather_data, security_data, traffic_data, fire_data, prediction)
        }

        self.save_report()
        self.save_pdf_report()

        return self.risk_data

    def _generate_recommendations(self, current: float, predicted: float, weather: Dict, security: Dict, traffic: Dict, fire: Dict, prediction: Dict) -> List[str]:
        recommendations = []

        if weather.get("severe_alerts"):
            recommendations.append(f"[天气预警] {','.join(weather['severe_alerts'])}")

        if prediction.get("warnings"):
            recommendations.append(f"[预测预警] 未来{prediction['hours_ahead']}小时有风险")
            for warning in prediction["warnings"][:3]:
                recommendations.append(f"  {warning}")

        if predicted >= 60:
            recommendations.append("[高风险] 预测未来风险等级较高，请提前做好应急预案")
        elif predicted >= 40:
            recommendations.append("[中等风险] 预测存在一定风险，建议保持警惕")
        else:
            recommendations.append("[安全] 当前及预测未来风险较低，安全状况良好")

        return recommendations

    def save_report(self):
        if not self.risk_data:
            return

        os.makedirs(REPORT_DIR, exist_ok=True)

        timestamp = self.last_update.strftime("%Y-%m-%d_%H时%M分")
        json_file = os.path.join(REPORT_DIR, f"风险监测-华润银行大厦_{timestamp}.json")
        latest_file = os.path.join(REPORT_DIR, "latest_report.json")

        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.risk_data, f, ensure_ascii=False, indent=2, default=str)

        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(self.risk_data, f, ensure_ascii=False, indent=2, default=str)

    def save_pdf_report(self):
        if not self.risk_data or not HAS_REPORTLAB:
            return

        try:
            os.makedirs(REPORT_DIR, exist_ok=True)

            timestamp = self.last_update.strftime("%Y-%m-%d_%H时%M分")
            pdf_file = os.path.join(REPORT_DIR, f"风险监测-华润银行大厦_{timestamp}.pdf")
            latest_pdf = os.path.join(REPORT_DIR, "latest_report.pdf")

            if CHINESE_FONT_PATH:
                pdfmetrics.registerFont(TTFont(CHINESE_FONT_NAME, CHINESE_FONT_PATH))

            doc = SimpleDocTemplate(pdf_file, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)

            styles = getSampleStyleSheet()

            font_name = CHINESE_FONT_NAME if CHINESE_FONT_PATH else 'Helvetica'

            COLORS = {
                "safe": {"bg": colors.Color(0.85, 0.95, 0.85), "text": colors.darkgreen, "border": colors.green},
                "low": {"bg": colors.Color(0.98, 0.95, 0.85), "text": colors.darkgoldenrod, "border": colors.gold},
                "medium": {"bg": colors.Color(1.0, 0.92, 0.85), "text": colors.orange, "border": colors.orange},
                "high": {"bg": colors.Color(1.0, 0.88, 0.88), "text": colors.red, "border": colors.red},
                "critical": {"bg": colors.Color(0.95, 0.85, 0.95), "text": colors.darkred, "border": colors.darkred}
            }

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=20,
                spaceAfter=15,
                alignment=1,
                textColor=colors.darkblue,
                bold=True
            )

            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=font_name,
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15,
                textColor=colors.darkblue,
                bold=True,
                borderBottom=1,
                borderColor=colors.lightblue
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                spaceAfter=6,
                leading=16
            )

            highlight_style = ParagraphStyle(
                'Highlight',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                spaceAfter=6,
                leading=16,
                textColor=colors.darkred,
                bold=True
            )

            success_style = ParagraphStyle(
                'Success',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                spaceAfter=6,
                leading=16,
                textColor=colors.darkgreen,
                bold=True
            )

            warning_style = ParagraphStyle(
                'Warning',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=11,
                spaceAfter=6,
                leading=16,
                textColor=colors.darkorange
            )

            story = []
            data = self.risk_data
            risk = data["risk_level"]
            prediction = data.get("prediction", {})
            risk_color = COLORS.get(risk['level'], COLORS["safe"])

            story.append(Paragraph("珠海华润银行总行大厦", title_style))
            story.append(Paragraph("风险监测报告", title_style))
            story.append(Spacer(1, 15))

            info_table = Table([
                ["📍 监测位置", data['location']],
                ["📅 更新时间", self.last_update.strftime('%Y年%m月%d日 %H时%M分')],
                ["📄 报告版本", f"V1.0 ({timestamp})"]
            ], colWidths=[90, 390])
            info_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (0, -1), colors.Color(0.92, 0.95, 0.98)),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightblue),
            ]))
            story.append(info_table)
            story.append(Spacer(1, 20))

            story.append(Paragraph("综合风险评估", heading_style))

            risk_score = data['current_score']
            predicted_score = data['predicted_score']

            risk_bar_width = min(risk_score / 100 * 350, 350)
            risk_bar_color = risk_color["border"]

            score_table_data = [
                ["风险等级", Paragraph(f"<b>{risk['label']}</b>", body_style)],
                ["当前评分", Paragraph(f"<b>{risk_score}/100</b>", body_style)],
                ["预测评分", f"{predicted_score}/100"],
                ["风险趋势", "✅ 稳定" if predicted_score <= risk_score else "⚠️ 上升"]
            ]

            score_table = Table(score_table_data, colWidths=[100, 200])
            score_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 0), (-1, 0), risk_color["bg"]),
                ('TEXTCOLOR', (0, 0), (-1, 0), risk_color["text"]),
                ('BACKGROUND', (0, 1), (-1, 1), risk_color["bg"]),
                ('TEXTCOLOR', (0, 1), (-1, 1), risk_color["text"]),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightblue),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 10))

            bar_table = Table([
                ["风险评分条:", ""],
                ["", ""]
            ], colWidths=[80, 350])
            bar_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (1, 1), (1, 1), colors.Color(0.9, 0.9, 0.9)),
                ('BACKGROUND', (1, 0), (1, 0), risk_bar_color),
                ('SPAN', (1, 0), (1, 0)),
                ('CELLWIDTH', (1, 0), (1, 0), risk_bar_width),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            story.append(bar_table)
            story.append(Spacer(1, 15))

            legend_table = Table([
                ["🟢 安全", "0-20分"],
                ["🟡 低风险", "21-40分"],
                ["🟠 中风险", "41-60分"],
                ["🔴 高风险", "61-80分"],
                ["🟣 极高风险", "81-100分"]
            ], colWidths=[80, 80])
            legend_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(legend_table)
            story.append(Spacer(1, 20))

            story.append(Paragraph("提前预警 - 未来12小时预报", heading_style))

            forecast_data = [["时间", "天气", "气温", "风速", "降水概率"]]
            for fc in data['components']['weather'].get('hourly_forecasts', [])[:8]:
                forecast_data.append([
                    fc['hour'],
                    fc['weather'],
                    f"{fc['temp']}C",
                    f"{fc['wind']}km/h",
                    f"{fc['precip']}%"
                ])

            forecast_table = Table(forecast_data, colWidths=[50, 70, 50, 60, 70])
            forecast_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.Color(0.85, 0.85, 0.85)),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.98, 1.0)]),
            ]))
            story.append(forecast_table)
            story.append(Spacer(1, 10))

            if prediction.get("warnings"):
                story.append(Paragraph(f"预警提示（共{len(prediction['warnings'])}条）：", highlight_style))
                for warning in prediction["warnings"]:
                    story.append(Paragraph(f"  • {warning}", body_style))
                story.append(Spacer(1, 10))

            story.append(Paragraph("分项风险详情", heading_style))

            def get_risk_color(score, max_score):
                percentage = score / max_score * 100
                if percentage <= 20:
                    return colors.Color(0.85, 0.95, 0.85), colors.darkgreen
                elif percentage <= 40:
                    return colors.Color(0.98, 0.95, 0.85), colors.darkgoldenrod
                elif percentage <= 60:
                    return colors.Color(1.0, 0.92, 0.85), colors.orange
                elif percentage <= 80:
                    return colors.Color(1.0, 0.88, 0.88), colors.red
                else:
                    return colors.Color(0.95, 0.85, 0.95), colors.darkred

            weather = data['components']['weather']
            weather_score = weather.get('risk_score', 0)
            weather_bg, weather_text = get_risk_color(weather_score, 35)
            weather_status = "✅" if weather.get('status') == 'success' else "❌"
            
            weather_table = Table([
                ["🌡️ 天气风险", f"权重 20%"],
                ["数据来源", f"{weather.get('source', '未知')} {weather_status}"],
                ["当前状况", f"{weather.get('weather', '未知')} | 气温 {weather.get('current_temp', '未知')}C | 风速 {weather.get('wind_speed', '未知')} km/h"],
                ["风险评分", Paragraph(f"<b>{weather_score}/20</b>", body_style)]
            ], colWidths=[120, 280])
            weather_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), weather_bg),
                ('TEXTCOLOR', (0, 0), (-1, 0), weather_text),
                ('BACKGROUND', (0, 3), (-1, 3), weather_bg),
                ('TEXTCOLOR', (0, 3), (-1, 3), weather_text),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightblue),
            ]))
            story.append(weather_table)
            
            if weather.get('severe_alerts'):
                story.append(Paragraph(f"⚠️ 预警：{','.join(weather['severe_alerts'])}", highlight_style))
            else:
                story.append(Paragraph("✅ 无异常", success_style))
            story.append(Spacer(1, 10))

            social = data['components']['social_media']
            social_score = social.get('risk_score', 0)
            social_bg, social_text = get_risk_color(social_score, 30)
            social_status = "✅" if social.get('status') == 'success' else "❌"
            sentiment = '正面' if social.get('sentiment_score', 0) > 0.6 else '中性' if social.get('sentiment_score', 0) > 0.4 else '负面'
            
            social_table = Table([
                ["💬 舆情风险", f"权重 25%"],
                ["数据来源", f"{social.get('source', '未知')} {social_status}"],
                ["监测数据", f"总帖数 {social.get('total_posts', 0)}条 | 风险帖 {social.get('risk_posts', 0)}条 | 负面帖 {social.get('negative_posts', 0)}条"],
                ["情感倾向", sentiment],
                ["风险评分", Paragraph(f"<b>{social_score}/25</b>", body_style)]
            ], colWidths=[120, 280])
            social_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), social_bg),
                ('TEXTCOLOR', (0, 0), (-1, 0), social_text),
                ('BACKGROUND', (0, 4), (-1, 4), social_bg),
                ('TEXTCOLOR', (0, 4), (-1, 4), social_text),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightblue),
            ]))
            story.append(social_table)
            
            if social.get('requires_config'):
                story.append(Paragraph("⚠️ 需要配置NewsAPI密钥以获取真实舆情数据", warning_style))
            if social.get('top_articles'):
                story.append(Paragraph("📰 重点文章：", body_style))
                for idx, article in enumerate(social['top_articles'][:3], 1):
                    story.append(Paragraph(f"  {idx}. {article.get('title', '')}", body_style))
            story.append(Spacer(1, 10))

            security = data['components']['security']
            security_score = security.get('risk_score', 0)
            security_bg, security_text = get_risk_color(security_score, 30)
            security_status = "✅" if security.get('status') == 'success' else "❌"
            
            security_table = Table([
                ["🔒 治安风险", f"权重 20%"],
                ["数据来源", f"{security.get('source', '未知')} {security_status}"],
                ["区域安全", f"{security.get('overall_safety', '未知')} | 安全事件 {security.get('incident_count', 0)}起"],
                ["事件分类", f"暴力{security.get('violent_incidents', 0)}起 | 盗窃{security.get('theft_incidents', 0)}起 | 诈骗{security.get('fraud_incidents', 0)}起"],
                ["风险评分", Paragraph(f"<b>{security_score}/20</b>", body_style)]
            ], colWidths=[120, 280])
            security_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), security_bg),
                ('TEXTCOLOR', (0, 0), (-1, 0), security_text),
                ('BACKGROUND', (0, 4), (-1, 4), security_bg),
                ('TEXTCOLOR', (0, 4), (-1, 4), security_text),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightblue),
            ]))
            story.append(security_table)
            
            if security.get('requires_config'):
                story.append(Paragraph("⚠️ 需要配置NewsAPI密钥以获取真实治安数据", warning_style))
            if security.get('recent_incidents'):
                story.append(Paragraph("🚨 近期事件：", body_style))
                for idx, incident in enumerate(security['recent_incidents'][:3], 1):
                    incident_type = incident.get('type', '未知')
                    incident_desc = incident.get('description', '')
                    story.append(Paragraph(f"  {idx}. [{incident_type}] {incident_desc}", body_style))
            story.append(Spacer(1, 10))

            traffic = data['components']['traffic']
            traffic_score = traffic.get('risk_score', 0)
            traffic_bg, traffic_text = get_risk_color(traffic_score, 15)
            traffic_status = "✅" if traffic.get('status') == 'success' else "❌"
            
            traffic_table = Table([
                ["🚦 交通风险", f"权重 10%"],
                ["数据来源", f"{traffic.get('source', '未知')} {traffic_status}"],
                ["拥堵等级", traffic.get('congestion_level', '未知')],
                ["风险评分", Paragraph(f"<b>{traffic_score}/10</b>", body_style)]
            ], colWidths=[120, 280])
            traffic_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), traffic_bg),
                ('TEXTCOLOR', (0, 0), (-1, 0), traffic_text),
                ('BACKGROUND', (0, 3), (-1, 3), traffic_bg),
                ('TEXTCOLOR', (0, 3), (-1, 3), traffic_text),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightblue),
            ]))
            story.append(traffic_table)
            
            if traffic.get('requires_config'):
                story.append(Paragraph("⚠️ 需要配置高德地图API密钥以获取真实交通数据", warning_style))
            story.append(Spacer(1, 10))

            fire = data['components']['fire']
            fire_score = fire.get('risk_score', 0)
            fire_bg, fire_text = get_risk_color(fire_score, 25)
            fire_status = "✅" if fire.get('status') == 'success' else "❌"
            
            fire_table = Table([
                ["🔥 消防风险", f"权重 25%"],
                ["数据来源", f"{fire.get('source', '未知')} {fire_status}"],
                ["消防状态", fire.get('fire_status', '未知')],
                ["事件统计", f"火灾事件 {fire.get('fire_count', 0)}起 | 隐患排查 {fire.get('hazard_count', 0)}起"],
                ["风险评分", Paragraph(f"<b>{fire_score}/25</b>", body_style)]
            ], colWidths=[120, 280])
            fire_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BACKGROUND', (0, 0), (-1, 0), fire_bg),
                ('TEXTCOLOR', (0, 0), (-1, 0), fire_text),
                ('BACKGROUND', (0, 4), (-1, 4), fire_bg),
                ('TEXTCOLOR', (0, 4), (-1, 4), fire_text),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightblue),
            ]))
            story.append(fire_table)
            
            if fire.get('fire_details'):
                story.append(Paragraph("📋 消防动态：", body_style))
                for idx, detail in enumerate(fire['fire_details'][:3], 1):
                    story.append(Paragraph(f"  {idx}. [{detail.get('type', '')}] {detail.get('title', '')}", body_style))
            story.append(Spacer(1, 10))

            story.append(Paragraph("风险建议", heading_style))
            for rec in data["recommendations"]:
                if "[高风险]" in rec or "[预警]" in rec:
                    story.append(Paragraph(f"  • {rec}", highlight_style))
                else:
                    story.append(Paragraph(f"  • {rec}", body_style))

            story.append(Spacer(1, 20))
            story.append(Paragraph(f"报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H时%M分')}", body_style))
            story.append(Paragraph(f"数据来源：Open-Meteo | NewsAPI | 高德地图", body_style))
            story.append(Paragraph(f"监测地址：珠海市高新区金业南路", body_style))

            doc.build(story)

            shutil.copy(pdf_file, latest_pdf)

        except Exception as e:
            print(f"PDF生成失败: {str(e)}")

    def get_report_path(self) -> str:
        return REPORT_DIR

    def get_latest_pdf_path(self) -> str:
        return os.path.join(REPORT_DIR, "latest_report.pdf")

    def format_report(self) -> str:
        if not self.risk_data:
            return "[错误] 暂无风险数据，请先执行监测"

        data = self.risk_data
        risk = data["risk_level"]
        prediction = data.get("prediction", {})

        api_notes = []
        if data['components']['social_media'].get('requires_config'):
            api_notes.append("[舆情] 需要配置NewsAPI密钥")
        if data['components']['traffic'].get('requires_config'):
            api_notes.append("[交通] 需要配置高德地图API密钥")
        if data['components']['security'].get('requires_config'):
            api_notes.append("[治安] 需要配置NewsAPI密钥")

        report = f"""
================================================================================
【珠海华润银行总行大厦 - 风险监测报告】
================================================================================
📍 监测位置：{data['location']}
📅 更新时间：{self.last_update.strftime('%Y-%m-%d %H:%M:%S')}
📄 PDF报告：{self.get_latest_pdf_path()}

================================================================================
【综合风险评估】

📊 当前风险：{risk['label']} - 评分：{data['current_score']}/100
🔮 预测风险：{"⚠️ 高风险" if data['predicted_score'] >= 60 else "⚠️ 中等风险" if data['predicted_score'] >= 40 else "✅ 安全"} - 评分：{data['predicted_score']}/100

================================================================================
【提前预警 - 未来12小时预报】

📈 预测结论：{prediction.get('prediction', '未知')}
⏰ 风险峰值：{prediction.get('peak_time', '未知')} (评分：{prediction.get('peak_risk', 0)})
🔔 预警数量：{len(prediction.get('warnings', []))}条

逐时预报：
"""

        if data['components']['weather'].get('hourly_forecasts'):
            for fc in data['components']['weather']['hourly_forecasts'][:6]:
                alert_str = f" ⚠️{fc['severe_alerts']}" if fc['severe_alerts'] else ""
                report += f"  {fc['hour']} | {fc['weather']} | {fc['temp']}°C | 风速{fc['wind']}km/h | 降水{fc['precip']}%{alert_str}\n"

        report += f"""
================================================================================
【分项风险详情】

🌡️ 天气风险：{data['components']['weather'].get('risk_score', 0)}/35
  来源：{data['components']['weather'].get('source', '未知')}
  状况：{data['components']['weather'].get('weather', '未知')} | {data['components']['weather'].get('current_temp', '未知')}°C | {data['components']['weather'].get('wind_speed', '未知')}km/h
  {'⚠️ ' + str(data['components']['weather'].get('severe_alerts')) if data['components']['weather'].get('severe_alerts') else '✅ 无异常'}

💬 舆情风险：{data['components']['social_media'].get('risk_score', 0)}/25
  来源：{data['components']['social_media'].get('source', '未知')}
  监测：{data['components']['social_media'].get('total_posts', 0)}条 | 风险：{data['components']['social_media'].get('risk_posts', 0)}条
  情感：{'正面' if data['components']['social_media'].get('sentiment_score', 0) > 0.6 else '中性' if data['components']['social_media'].get('sentiment_score', 0) > 0.4 else '负面'}

🔒 治安风险：{data['components']['security'].get('risk_score', 0)}/25
  来源：{data['components']['security'].get('source', '未知')}
  安全：{data['components']['security'].get('overall_safety', '未知')} | 事件：{data['components']['security'].get('incident_count', 0)}起

🚦 交通风险：{data['components']['traffic'].get('risk_score', 0)}/15
  来源：{data['components']['traffic'].get('source', '未知')}
  拥堵：{data['components']['traffic'].get('congestion_level', '未知')}
"""

        if api_notes:
            report += "\n⚠️ 【API配置提示】\n"
            for note in api_notes:
                report += f"  • {note}\n"

        report += "\n📋 【风险建议】\n"
        for rec in data["recommendations"]:
            report += f"  • {rec}\n"

        report += "\n================================================================================\n"
        return report.strip()