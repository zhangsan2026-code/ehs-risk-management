import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from risk_ledger import RiskLedger, RiskRecord, RiskLevel, RiskStatus

REMINDER_CONFIG = {
    "email_enabled": False,
    "smtp_server": "smtp.example.com",
    "smtp_port": 587,
    "smtp_username": "",
    "smtp_password": "",
    "sender_email": "risk@example.com",
    "recipient_emails": ["admin@example.com"]
}

class AIReminder:
    def __init__(self, risk_ledger: RiskLedger):
        self.risk_ledger = risk_ledger
        self.reminder_history: List[Dict] = []
        self.load_history()

    def load_history(self):
        history_file = os.path.join(os.path.dirname(__file__), "risk_data", "reminder_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.reminder_history = json.load(f)
            except Exception:
                self.reminder_history = []

    def save_history(self):
        history_file = os.path.join(os.path.dirname(__file__), "risk_data", "reminder_history.json")
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.reminder_history, f, ensure_ascii=False, indent=2)

    def add_reminder_record(self, record_id: str, message: str, recipients: List[str], method: str):
        self.reminder_history.append({
            "timestamp": datetime.now().isoformat(),
            "record_id": record_id,
            "message": message,
            "recipients": recipients,
            "method": method
        })
        self.save_history()

    def check_and_trigger_reminders(self) -> List[Dict]:
        triggered_reminders = []
        
        overdue_records = self.risk_ledger.get_overdue_records()
        for record in overdue_records:
            reminder = self.trigger_overdue_reminder(record)
            if reminder:
                triggered_reminders.append(reminder)
        
        high_priority_records = self.risk_ledger.get_high_priority_records()
        for record in high_priority_records:
            reminder = self.trigger_high_priority_reminder(record)
            if reminder:
                triggered_reminders.append(reminder)
        
        pending_records = self.risk_ledger.get_pending_records()
        for record in pending_records:
            reminder = self.trigger_pending_reminder(record)
            if reminder:
                triggered_reminders.append(reminder)
        
        return triggered_reminders

    def trigger_overdue_reminder(self, record: RiskRecord) -> Optional[Dict]:
        if not record.due_date:
            return None
        
        overdue_days = (datetime.now() - record.due_date).days
        if overdue_days < 1:
            return None
        
        message = f"【风险逾期提醒】\n\n风险编号: {record.id}\n标题: {record.title}\n风险等级: {record.level.value}\n逾期天数: {overdue_days}天\n负责人: {record.assigned_to or '未分配'}\n\n请尽快处理！"
        
        self.send_reminder(record.id, message)
        self.add_reminder_record(record.id, message, REMINDER_CONFIG["recipient_emails"], "auto")
        
        return {
            "type": "overdue",
            "record_id": record.id,
            "title": record.title,
            "level": record.level.value,
            "overdue_days": overdue_days,
            "message": message
        }

    def trigger_high_priority_reminder(self, record: RiskRecord) -> Optional[Dict]:
        if record.status == RiskStatus.RESOLVED or record.status == RiskStatus.CLOSED:
            return None
        
        if record.priority > 2:
            return None
        
        message = f"【高优先级风险提醒】\n\n风险编号: {record.id}\n标题: {record.title}\n风险等级: {record.level.value}\n优先级: P{record.priority}\n状态: {record.status.value}\n负责人: {record.assigned_to or '未分配'}\n\n请优先处理此风险！"
        
        self.send_reminder(record.id, message)
        self.add_reminder_record(record.id, message, REMINDER_CONFIG["recipient_emails"], "auto")
        
        return {
            "type": "high_priority",
            "record_id": record.id,
            "title": record.title,
            "level": record.level.value,
            "priority": record.priority,
            "message": message
        }

    def trigger_pending_reminder(self, record: RiskRecord) -> Optional[Dict]:
        if record.status != RiskStatus.PENDING:
            return None
        
        pending_hours = (datetime.now() - record.discovered_at).total_seconds() / 3600
        if pending_hours < 4:
            return None
        
        message = f"【待处理风险提醒】\n\n风险编号: {record.id}\n标题: {record.title}\n风险等级: {record.level.value}\n发现时间: {record.discovered_at.strftime('%Y-%m-%d %H:%M')}\n发现人: {record.discovered_by}\n\n该风险已等待处理超过{pending_hours:.1f}小时，请及时分配处理！"
        
        self.send_reminder(record.id, message)
        self.add_reminder_record(record.id, message, REMINDER_CONFIG["recipient_emails"], "auto")
        
        return {
            "type": "pending",
            "record_id": record.id,
            "title": record.title,
            "level": record.level.value,
            "pending_hours": pending_hours,
            "message": message
        }

    def send_reminder(self, record_id: str, message: str):
        if not REMINDER_CONFIG["email_enabled"]:
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = REMINDER_CONFIG["sender_email"]
            msg['To'] = ", ".join(REMINDER_CONFIG["recipient_emails"])
            msg['Subject'] = "风险提醒"
            
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            with smtplib.SMTP(REMINDER_CONFIG["smtp_server"], REMINDER_CONFIG["smtp_port"]) as server:
                server.starttls()
                server.login(REMINDER_CONFIG["smtp_username"], REMINDER_CONFIG["smtp_password"])
                server.sendmail(REMINDER_CONFIG["sender_email"], REMINDER_CONFIG["recipient_emails"], msg.as_string())
        except Exception as e:
            print(f"邮件发送失败: {e}")

    def predict_risk_trend(self, days: int = 7) -> Dict:
        records = self.risk_ledger.records
        recent_records = [
            r for r in records
            if datetime.now() - r.discovered_at < timedelta(days=30)
        ]
        
        level_counts = {level.value: 0 for level in RiskLevel}
        category_counts = {}
        trend_data = []
        
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            day_records = [
                r for r in recent_records
                if r.discovered_at.date() == date.date()
            ]
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": len(day_records)
            })
        
        for record in recent_records:
            level_counts[record.level.value] += 1
            category_counts[record.category.value] = category_counts.get(record.category.value, 0) + 1
        
        avg_resolution_time = 0
        resolved_count = 0
        for record in recent_records:
            if record.resolved_at and record.discovered_at:
                resolution_hours = (record.resolved_at - record.discovered_at).total_seconds() / 3600
                avg_resolution_time += resolution_hours
                resolved_count += 1
        
        avg_resolution_time = avg_resolution_time / resolved_count if resolved_count > 0 else 0
        
        return {
            "prediction_period": f"{days}天趋势预测",
            "recent_records_count": len(recent_records),
            "level_distribution": level_counts,
            "category_distribution": category_counts,
            "daily_trend": trend_data[::-1],
            "avg_resolution_hours": round(avg_resolution_time, 1),
            "prediction": self._generate_prediction(trend_data, level_counts)
        }

    def _generate_prediction(self, trend_data: List[Dict], level_counts: Dict) -> str:
        if len(trend_data) < 3:
            return "数据不足，无法预测"
        
        recent_counts = [d["count"] for d in trend_data[-3:]]
        avg_recent = sum(recent_counts) / 3
        
        high_risk_ratio = (level_counts.get("高风险", 0) + level_counts.get("极高风险", 0)) / sum(level_counts.values()) if sum(level_counts.values()) > 0 else 0
        
        if avg_recent > 5 and high_risk_ratio > 0.3:
            return "⚠️ 预警：近期风险数量较高，且高风险占比大，建议加强风险管控措施"
        elif avg_recent > 3:
            return "⚠️ 提示：近期风险数量有所上升，建议关注趋势变化"
        elif high_risk_ratio > 0.2:
            return "⚠️ 提示：高风险事件占比较高，建议重点关注"
        else:
            return "✅ 当前风险状况稳定，继续保持现有管控措施"

    def generate_daily_summary(self) -> Dict:
        today = datetime.now().date()
        today_records = [
            r for r in self.risk_ledger.records
            if r.discovered_at.date() == today
        ]
        
        pending_count = len(self.risk_ledger.get_pending_records())
        overdue_count = len(self.risk_ledger.get_overdue_records())
        high_risk_count = len(self.risk_ledger.get_records_by_level(RiskLevel.CRITICAL)) + len(self.risk_ledger.get_records_by_level(RiskLevel.HIGH))
        
        return {
            "report_date": today.strftime("%Y-%m-%d"),
            "today_new_records": len(today_records),
            "pending_count": pending_count,
            "overdue_count": overdue_count,
            "high_risk_count": high_risk_count,
            "summary": self._generate_summary_text(pending_count, overdue_count, high_risk_count),
            "generated_at": datetime.now().isoformat()
        }

    def _generate_summary_text(self, pending: int, overdue: int, high_risk: int) -> str:
        parts = []
        
        if pending > 0:
            parts.append(f"待处理风险 {pending} 项")
        if overdue > 0:
            parts.append(f"逾期风险 {overdue} 项")
        if high_risk > 0:
            parts.append(f"高风险 {high_risk} 项")
        
        if parts:
            return "；".join(parts)
        return "今日无风险告警，运行正常"

    def get_reminder_stats(self) -> Dict:
        today_count = 0
        week_count = 0
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        for reminder in self.reminder_history:
            timestamp = datetime.fromisoformat(reminder["timestamp"])
            if timestamp.date() == today.date():
                today_count += 1
            if timestamp >= week_ago:
                week_count += 1
        
        return {
            "total_reminders": len(self.reminder_history),
            "today_reminders": today_count,
            "week_reminders": week_count,
            "last_triggered": self.reminder_history[-1]["timestamp"] if self.reminder_history else None
        }