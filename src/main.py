import asyncio
import json
import time
import aiohttp
import os
from datetime import datetime
from email.mime.base import MIMEBase
from email import encoders
from .risk_monitor import RiskMonitor

CONFIG = {
    "wechat_enabled": False,
    "wechat_token": "",
    "wechat_url": "",
    "email_enabled": True,
    "email_sender": "3666488010@qq.com",
    "email_password": "pdrbyjvhpwxmdbih",
    "email_smtp_server": "smtp.qq.com",
    "email_smtp_port": 587,
    "email_recipient": "3666488010@qq.com",
    "ai_enable": True,
    "auto_reconnect": True,
    "anti_block": True,
    "group_support": True,
    "timing_task": True,
    "hourly_report": True
}

SESSION = None
RISK_MONITOR = RiskMonitor()
COMMAND_LIST = {
    "help": "[指令列表]\n1.【时间】查看当前时间\n2.【办公】启动办公助手\n3.【关闭AI】关闭智能回复\n4.【风险监测】启动实时风险监测\n5.【风险报告】查看完整评估报告",
    "办公": "办公自动化已激活：可支持表格/文件批量处理指令",
    "关闭AI": "AI智能回复已关闭，仅文本回复",
    "风险监测": "正在启动珠海华润银行风险监测...",
    "风险报告": "正在生成最新风险评估报告..."
}


def check_wechat_config():
    return CONFIG["wechat_enabled"] and CONFIG["wechat_token"] and CONFIG["wechat_token"] != ""

def check_email_config():
    return CONFIG["email_enabled"] and CONFIG["email_sender"] and CONFIG["email_password"]


async def ai_answer(text: str) -> str:
    base = "[智能回复] %s - 已解析\n可对接Excel自动化、文件整理、消息提醒等办公功能" % text
    if "时间" in text:
        return "当前时间：%s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if "代码" in text or "工具" in text:
        return "支持：代码生成、脚本编写、Excel处理、批量文件整理、自动化办公"
    if "风险" in text or "监测" in text:
        return "发送【风险监测】启动实时监测，发送【风险报告】查看完整评估"
    return base


async def handle_risk_monitor(command: str) -> str:
    if command == "风险监测":
        await RISK_MONITOR.get_risk_assessment()
        report = RISK_MONITOR.format_report()
        if check_wechat_config():
            await send_msg(report)
        return report
    elif command == "风险报告":
        if RISK_MONITOR.risk_data:
            report = RISK_MONITOR.format_report()
            if check_wechat_config():
                await send_msg(report)
            return report
        else:
            return "尚未进行风险监测，请先发送【风险监测】"
    return "未知指令"


async def send_msg(reply_text: str):
    if not check_wechat_config():
        print("[微信消息] 未发送：微信功能未启用或未配置token")
        return False
        
    try:
        import urllib.parse
        title = "珠海华润银行风险监测"
        desp = reply_text[:2000] if len(reply_text) > 2000 else reply_text
        encoded_title = urllib.parse.quote(title)
        encoded_desp = urllib.parse.quote(desp)
        url = f"{CONFIG['wechat_url']}?title={encoded_title}&desp={encoded_desp}"
        
        async with SESSION.get(url, timeout=10) as resp:
            result = await resp.text()
            print(f"[微信消息] 发送结果：{result}")
            if "success" in result or "ok" in result.lower():
                print("[微信消息] 发送成功")
                return True
            else:
                print("[微信消息] 发送失败：%s" % result)
                return False
    except Exception as e:
        print("[微信消息] 发送失败：%s" % str(e))
        return False

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(subject: str, content: str, attachment_path: str = None):
    if not check_email_config():
        print("[邮件] 未发送：邮件功能未启用或未配置")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = CONFIG["email_sender"]
        msg['To'] = CONFIG["email_recipient"]
        msg['Subject'] = subject
        
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(attachment_path)}"')
                msg.attach(part)
        
        server = smtplib.SMTP(CONFIG["email_smtp_server"], CONFIG["email_smtp_port"])
        server.starttls()
        server.login(CONFIG["email_sender"], CONFIG["email_password"])
        server.sendmail(CONFIG["email_sender"], CONFIG["email_recipient"], msg.as_string())
        server.quit()
        
        print("[邮件] 发送成功")
        return True
    except Exception as e:
        print(f"[邮件] 发送失败：{str(e)}")
        return False


async def console_mode():
    print("="*60)
    print("珠海华润银行总行大厦 - 风险监测系统")
    print("="*60)
    print("功能列表：")
    print("  1. 实时风险监测")
    print("  2. PDF报告自动生成")
    print("  3. 每小时自动更新")
    print("  4. 提前6-12小时风险预警")
    print("="*60)
    
    if CONFIG["hourly_report"]:
        print("自动报告模式已开启（每小时生成报告）")
    if not CONFIG["wechat_enabled"]:
        print("警告：微信推送功能未启用")
        print("   如需启用，请配置 CONFIG['wechat_enabled'] = True")
        print("   并设置 CONFIG['wechat_token']")
    print("="*60)
    
    while True:
        try:
            if CONFIG["hourly_report"]:
                await RISK_MONITOR.get_risk_assessment()
                
                data = RISK_MONITOR.risk_data
                risk = data["risk_level"]
                pdf_path = RISK_MONITOR.get_latest_pdf_path()
                
                print("\n[%s]" % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                print("位置：%s" % data['location'])
                print("当前风险：%s - %s/100" % (risk['label'], data['current_score']))
                pred_label = "高风险" if data['predicted_score'] >= 60 else "中等风险" if data['predicted_score'] >= 40 else "安全"
                print("预测风险：%s - %s/100" % (pred_label, data['predicted_score']))
                print("报告已保存：%s" % pdf_path)
                
                if check_email_config():
                    report_content = f"""【珠海华润银行总行大厦风险监测报告】

监测位置：{data['location']}
更新时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}

当前风险：{risk['label']} - {data['current_score']}/100
预测风险：{pred_label} - {data['predicted_score']}/100

分项风险：
🌡️ 天气风险：{data['components']['weather'].get('risk_score', 0)}/20
💬 舆情风险：{data['components']['social_media'].get('risk_score', 0)}/25
🔒 治安风险：{data['components']['security'].get('risk_score', 0)}/20
🚦 交通风险：{data['components']['traffic'].get('risk_score', 0)}/10
🔥 消防风险：{data['components']['fire'].get('risk_score', 0)}/25

详见附件PDF报告。"""
                    send_email("珠海华润银行风险监测报告", report_content, pdf_path)
                    print("邮件已发送")
                
                if data['predicted_score'] >= 60 or data['current_score'] >= 60:
                    report = RISK_MONITOR.format_report()
                    await send_msg("[高风险预警]\n%s" % report)
                elif data['predicted_score'] >= 40 or data['current_score'] >= 40:
                    brief = "[中等风险提示]\n当前：%s(%s分)\n预测：%s分" % (risk['label'], data['current_score'], data['predicted_score'])
                    await send_msg(brief)
                
                await asyncio.sleep(3600)
            
            else:
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            print("\n\n风险监测系统已停止")
            break
        except Exception as e:
            print("[错误] %s" % str(e))
            await asyncio.sleep(60)


async def main():
    global SESSION
    SESSION = aiohttp.ClientSession()
    
    try:
        await console_mode()
    finally:
        if SESSION and not SESSION.closed:
            await SESSION.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n系统已停止运行")