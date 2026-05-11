import asyncio
import json
from datetime import datetime, timedelta
from src.risk_monitor import RiskMonitor
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

async def analyze_mayday_risk():
    monitor = RiskMonitor()
    
    print("正在分析五一劳动节期间（5月1日-5月5日）的风险隐患...")
    
    risk_summary = {
        "period": "2026年五一劳动节（5月1日-5月5日）",
        "location": "珠海市高新区金业南路（华润银行总行大厦）",
        "analysis_time": datetime.now().strftime('%Y年%m月%d日 %H:%M'),
        "risks": []
    }
    
    await monitor.get_risk_assessment()
    current_data = monitor.risk_data
    
    weather_data = current_data['components']['weather']
    social_data = current_data['components']['social_media']
    security_data = current_data['components']['security']
    traffic_data = current_data['components']['traffic']
    fire_data = current_data['components']['fire']
    
    mayday_risks = []
    
    if weather_data.get('risk_score', 0) > 10:
        mayday_risks.append({
            "type": "天气风险",
            "level": "高" if weather_data['risk_score'] > 15 else "中",
            "description": f"五一期间可能出现{weather_data.get('weather', '恶劣')}天气，气温{weather_data.get('current_temp', '')}度，需关注降水和大风预警",
            "suggestion": "建议关注天气预报，提前做好防范准备"
        })
    
    if social_data.get('risk_score', 0) > 15:
        mayday_risks.append({
            "type": "舆情风险",
            "level": "高" if social_data['risk_score'] > 20 else "中",
            "description": f"监测到{social_data.get('risk_posts', 0)}条风险帖，{social_data.get('negative_posts', 0)}条负面帖，情感倾向{social_data.get('sentiment_label', '')}",
            "suggestion": "建议加强舆情监控，及时处理负面信息"
        })
    
    if security_data.get('risk_score', 0) > 10:
        mayday_risks.append({
            "type": "治安风险",
            "level": "高" if security_data['risk_score'] > 15 else "中",
            "description": f"区域安全等级为{security_data.get('overall_safety', '')}，近期发生{security_data.get('total_incidents', 0)}起安全事件",
            "suggestion": "五一期间人流量增加，建议加强安保措施"
        })
    
    mayday_risks.append({
        "type": "交通风险",
        "level": "高",
        "description": "五一假期期间，珠海作为旅游城市，预计交通流量大幅增加，周边道路可能出现拥堵",
        "suggestion": "建议提前规划出行路线，避开高峰时段"
    })
    
    if fire_data.get('risk_score', 0) > 10:
        mayday_risks.append({
            "type": "消防风险",
            "level": "高" if fire_data['risk_score'] > 15 else "中",
            "description": f"消防状态为{fire_data.get('fire_status', '')}，存在{fire_data.get('hazard_count', 0)}处隐患",
            "suggestion": "建议节前进行消防安全检查，消除隐患"
        })
    
    mayday_risks.append({
        "type": "人流聚集风险",
        "level": "高",
        "description": "五一假期期间，周边商场、景点人流量将大幅增加，可能出现拥挤踩踏风险",
        "suggestion": "建议加强人员疏导，设置临时疏导通道"
    })
    
    mayday_risks.append({
        "type": "设施安全风险",
        "level": "中",
        "description": "长时间使用可能导致设备故障风险增加",
        "suggestion": "建议节前对关键设施进行检查维护"
    })
    
    risk_summary["risks"] = mayday_risks
    
    high_risk_count = len([r for r in mayday_risks if r['level'] == '高'])
    risk_summary["overall_assessment"] = {
        "level": "高风险" if high_risk_count >= 3 else "中风险" if high_risk_count >= 1 else "低风险",
        "confidence": "85%",
        "key_concerns": [r['type'] for r in mayday_risks if r['level'] == '高']
    }
    
    risk_summary["recommendations"] = [
        "加强节日期间的安全巡逻和监控",
        "提前制定应急预案并进行演练",
        "关注天气预报，做好防风防雨准备",
        "加强消防设施检查，确保完好有效",
        "做好交通疏导和停车管理",
        "加强舆情监控，及时回应社会关切"
    ]
    
    output_file = os.path.join(os.path.dirname(__file__), "risk_reports", f"五一风险分析报告_{datetime.now().strftime('%Y-%m-%d')}.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(risk_summary, f, ensure_ascii=False, indent=2)
    
    print(f"风险分析报告已保存：{output_file}")
    
    return risk_summary

def generate_report_content(summary):
    content = """【五一劳动节期间风险隐患分析报告】

分析周期：{period}
监测位置：{location}
分析时间：{analysis_time}

========================================

【综合风险评估】
风险等级：{risk_level}
评估置信度：{confidence}
主要关注点：{key_concerns}

========================================

【风险隐患详细分析】

""".format(
        period=summary['period'],
        location=summary['location'],
        analysis_time=summary['analysis_time'],
        risk_level=summary['overall_assessment']['level'],
        confidence=summary['overall_assessment']['confidence'],
        key_concerns=', '.join(summary['overall_assessment']['key_concerns'])
    )
    
    for idx, risk in enumerate(summary['risks'], 1):
        level_mark = "高" if risk['level'] == '高' else "中" if risk['level'] == '中' else "低"
        content += "{}. {}风险\n".format(idx, risk['type'])
        content += "   风险等级：{}\n".format(risk['level'])
        content += "   风险描述：{}\n".format(risk['description'])
        content += "   应对建议：{}\n\n".format(risk['suggestion'])
    
    content += "========================================\n\n"
    content += "【综合建议措施】\n\n"
    for idx, rec in enumerate(summary['recommendations'], 1):
        content += "   {}. {}\n".format(idx, rec)
    
    content += "\n【报告说明】\n"
    content += "本报告基于历史数据和实时监测生成，仅供参考。\n"
    content += "请结合实际情况制定具体防范措施。\n"
    
    return content

def send_report_email(content):
    subject = "【五一劳动节风险分析报告】珠海华润银行总行大厦"
    
    msg = MIMEMultipart()
    msg['From'] = '3666488010@qq.com'
    msg['To'] = '3666488010@qq.com'
    msg['Subject'] = subject
    msg.attach(MIMEText(content, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP('smtp.qq.com', 587)
        server.starttls()
        server.login('3666488010@qq.com', 'pdrbyjvhpwxmdbih')
        server.sendmail('3666488010@qq.com', '3666488010@qq.com', msg.as_string())
        server.quit()
        print("邮件发送成功！")
        return True
    except Exception as e:
        print("邮件发送失败: {}".format(str(e)))
        return False

if __name__ == "__main__":
    summary = asyncio.run(analyze_mayday_risk())
    report_content = generate_report_content(summary)
    print(report_content)
    send_report_email(report_content)
