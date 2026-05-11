import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

RISK_DATA_DIR = os.path.join(os.path.dirname(__file__), "risk_data")
os.makedirs(RISK_DATA_DIR, exist_ok=True)

class RiskLevel(Enum):
    CRITICAL = "极高风险"
    HIGH = "高风险"
    MEDIUM = "中风险"
    LOW = "低风险"
    INFO = "一般关注"

class RiskStatus(Enum):
    PENDING = "待处理"
    PROCESSING = "处理中"
    PENDING_AUDIT = "待审核"
    RESOLVED = "已解决"
    CLOSED = "已关闭"
    ESCALATED = "已升级"

class RiskCategory(Enum):
    FIRE = "消防安全"
    SECURITY = "治安安全"
    ENVIRONMENT = "环境安全"
    HEALTH = "职业健康"
    EQUIPMENT = "设备安全"
    TRAFFIC = "交通安全"
    PROCEDURE = "流程合规"
    CONTRACTOR = "外包管理"
    OTHER = "其他"

PHOTOS_DIR = os.path.join(os.path.dirname(__file__), "risk_photos")
os.makedirs(PHOTOS_DIR, exist_ok=True)

class RiskRecord:
    def __init__(
        self,
        title: str,
        description: str,
        category: RiskCategory,
        level: RiskLevel,
        location: str = "",
        discovered_by: str = "",
        discovered_at: Optional[datetime] = None,
        ehs_standard: str = "",
        priority: int = 3,
        photos: List[str] = None,
        corrective_dept: str = "",
        corrective_by: str = ""
    ):
        self.id = str(uuid.uuid4())[:8]
        self.title = title
        self.description = description
        self.category = category
        self.level = level
        self.location = location
        self.discovered_by = discovered_by
        self.discovered_at = discovered_at or datetime.now()
        self.ehs_standard = ehs_standard
        self.priority = priority
        self.status = RiskStatus.PENDING
        self.assigned_to = ""
        self.corrective_dept = corrective_dept
        self.corrective_by = corrective_by
        self.photos = photos or []
        self.before_photos = []
        self.after_photos = []
        self.check_items: List[Dict] = []
        self.assessed_at = None
        self.assessed_by = ""
        self.assessment_note = ""
        self.action_plan = ""
        self.due_date = None
        self.progress = 0
        self.resolved_at = None
        self.resolved_by = ""
        self.resolution_note = ""
        self.audit_status = "pending"
        self.audited_at = None
        self.audited_by = ""
        self.audit_note = ""
        self.reminders: List[Dict] = []
        self.history: List[Dict] = []
        self.add_history("风险记录创建", f"创建者: {discovered_by}")

    def add_history(self, action: str, detail: str):
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "detail": detail
        })

    def assign(self, assignee: str):
        self.assigned_to = assignee
        self.status = RiskStatus.PROCESSING
        self.add_history("风险分配", f"分配给: {assignee}")

    def assess(self, assessor: str, note: str):
        self.assessed_at = datetime.now()
        self.assessed_by = assessor
        self.assessment_note = note
        self.add_history("风险评估", f"评估人: {assessor}, 备注: {note}")

    def set_action_plan(self, plan: str, due_date: Optional[datetime] = None):
        self.action_plan = plan
        self.due_date = due_date
        self.add_history("制定处置方案", f"截止日期: {due_date.strftime('%Y-%m-%d') if due_date else '未设定'}")

    def update_progress(self, progress: int):
        self.progress = min(100, max(0, progress))
        if self.progress == 100 and self.status != RiskStatus.RESOLVED:
            self.status = RiskStatus.RESOLVED
            self.resolved_at = datetime.now()
        self.add_history("进度更新", f"进度: {self.progress}%")

    def add_check_item(self, description: str):
        self.check_items.append({
            "id": str(uuid.uuid4())[:6],
            "description": description,
            "completed": False,
            "completed_by": "",
            "completed_at": None,
            "photo": ""
        })
        self.update_auto_progress()
        self.add_history("添加检查项", description)

    def complete_check_item(self, item_id: str, completed_by: str, photo: str = ""):
        for item in self.check_items:
            if item["id"] == item_id:
                item["completed"] = True
                item["completed_by"] = completed_by
                item["completed_at"] = datetime.now().isoformat()
                item["photo"] = photo
                self.update_auto_progress()
                self.add_history("完成检查项", f"{completed_by}: {item['description']}")
                break

    def update_auto_progress(self):
        if self.check_items:
            completed = sum(1 for item in self.check_items if item["completed"])
            self.progress = int((completed / len(self.check_items)) * 100)
            if self.progress == 100 and self.status == RiskStatus.PROCESSING:
                self.status = RiskStatus.PENDING_AUDIT
        else:
            self.progress = 0

    def submit_for_audit(self, submitter: str):
        if self.progress >= 100:
            self.status = RiskStatus.PENDING_AUDIT
            self.audit_status = "pending"
            self.add_history("提交审核", f"提交人: {submitter}")
            return True
        return False

    def audit(self, auditor: str, approved: bool, note: str):
        if approved:
            self.audit_status = "approved"
            self.status = RiskStatus.RESOLVED
            self.resolved_at = datetime.now()
            self.resolved_by = auditor
            self.resolution_note = note
            self.add_history("审核通过", f"审核人: {auditor}, 备注: {note}")
        else:
            self.audit_status = "rejected"
            self.status = RiskStatus.PROCESSING
            self.progress = 90
            self.add_history("审核驳回", f"审核人: {auditor}, 原因: {note}")
        self.audited_at = datetime.now()
        self.audited_by = auditor
        self.audit_note = note

    def resolve(self, resolver: str, note: str):
        self.status = RiskStatus.RESOLVED
        self.resolved_at = datetime.now()
        self.resolved_by = resolver
        self.resolution_note = note
        self.progress = 100
        self.add_history("风险解决", f"解决人: {resolver}, 备注: {note}")

    def close(self, closer: str):
        self.status = RiskStatus.CLOSED
        self.add_history("风险关闭", f"关闭人: {closer}")

    def escalate(self, escalator: str, reason: str):
        self.status = RiskStatus.ESCALATED
        self.add_history("风险升级", f"升级人: {escalator}, 原因: {reason}")

    def add_reminder(self, reminder_time: datetime, message: str):
        self.reminders.append({
            "id": str(uuid.uuid4())[:6],
            "time": reminder_time.isoformat(),
            "message": message,
            "triggered": False
        })

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "level": self.level.value,
            "location": self.location,
            "discovered_by": self.discovered_by,
            "discovered_at": self.discovered_at.isoformat(),
            "ehs_standard": self.ehs_standard,
            "priority": self.priority,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "corrective_dept": self.corrective_dept,
            "corrective_by": self.corrective_by,
            "photos": self.photos,
            "before_photos": self.before_photos,
            "after_photos": self.after_photos,
            "check_items": self.check_items,
            "assessed_at": self.assessed_at.isoformat() if self.assessed_at else None,
            "assessed_by": self.assessed_by,
            "assessment_note": self.assessment_note,
            "action_plan": self.action_plan,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "progress": self.progress,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_note": self.resolution_note,
            "audit_status": self.audit_status,
            "audited_at": self.audited_at.isoformat() if self.audited_at else None,
            "audited_by": self.audited_by,
            "audit_note": self.audit_note,
            "reminders": self.reminders,
            "history": self.history
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'RiskRecord':
        record = cls(
            title=data["title"],
            description=data["description"],
            category=RiskCategory(data["category"]),
            level=RiskLevel(data["level"]),
            location=data.get("location", ""),
            discovered_by=data.get("discovered_by", ""),
            discovered_at=datetime.fromisoformat(data["discovered_at"]) if data.get("discovered_at") else datetime.now(),
            ehs_standard=data.get("ehs_standard", ""),
            priority=data.get("priority", 3),
            photos=data.get("photos", []),
            corrective_dept=data.get("corrective_dept", ""),
            corrective_by=data.get("corrective_by", "")
        )
        record.id = data["id"]
        record.status = RiskStatus(data.get("status", "待处理"))
        record.assigned_to = data.get("assigned_to", "")
        record.before_photos = data.get("before_photos", [])
        record.after_photos = data.get("after_photos", [])
        record.check_items = data.get("check_items", [])
        record.assessed_at = datetime.fromisoformat(data["assessed_at"]) if data.get("assessed_at") else None
        record.assessed_by = data.get("assessed_by", "")
        record.assessment_note = data.get("assessment_note", "")
        record.action_plan = data.get("action_plan", "")
        record.due_date = datetime.fromisoformat(data["due_date"]) if data.get("due_date") else None
        record.progress = data.get("progress", 0)
        record.resolved_at = datetime.fromisoformat(data["resolved_at"]) if data.get("resolved_at") else None
        record.resolved_by = data.get("resolved_by", "")
        record.resolution_note = data.get("resolution_note", "")
        record.audit_status = data.get("audit_status", "pending")
        record.audited_at = datetime.fromisoformat(data["audited_at"]) if data.get("audited_at") else None
        record.audited_by = data.get("audited_by", "")
        record.audit_note = data.get("audit_note", "")
        record.reminders = data.get("reminders", [])
        record.history = data.get("history", [])
        return record

class RiskLedger:
    def __init__(self):
        self.records: List[RiskRecord] = []
        self.load_records()

    def load_records(self):
        records_file = os.path.join(RISK_DATA_DIR, "risk_records.json")
        if os.path.exists(records_file):
            try:
                with open(records_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [RiskRecord.from_dict(item) for item in data]
            except Exception:
                self.records = []

    def save_records(self):
        records_file = os.path.join(RISK_DATA_DIR, "risk_records.json")
        with open(records_file, 'w', encoding='utf-8') as f:
            json.dump([record.to_dict() for record in self.records], f, ensure_ascii=False, indent=2)

    def add_record(self, record: RiskRecord):
        self.records.append(record)
        self.save_records()
        return record

    def get_record(self, record_id: str) -> Optional[RiskRecord]:
        for record in self.records:
            if record.id == record_id:
                return record
        return None

    def update_record(self, record_id: str, updates: Dict):
        record = self.get_record(record_id)
        if record:
            for key, value in updates.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.save_records()
            return record
        return None

    def delete_record(self, record_id: str) -> bool:
        record = self.get_record(record_id)
        if record:
            self.records.remove(record)
            self.save_records()
            return True
        return False

    def get_records_by_status(self, status: RiskStatus) -> List[RiskRecord]:
        return [r for r in self.records if r.status == status]

    def get_records_by_category(self, category: RiskCategory) -> List[RiskRecord]:
        return [r for r in self.records if r.category == category]

    def get_records_by_level(self, level: RiskLevel) -> List[RiskRecord]:
        return [r for r in self.records if r.level == level]

    def get_pending_records(self) -> List[RiskRecord]:
        return self.get_records_by_status(RiskStatus.PENDING)

    def get_overdue_records(self) -> List[RiskRecord]:
        now = datetime.now()
        return [
            r for r in self.records
            if r.due_date and r.due_date < now and r.status not in [RiskStatus.RESOLVED, RiskStatus.CLOSED]
        ]

    def get_high_priority_records(self) -> List[RiskRecord]:
        return [r for r in self.records if r.priority <= 2 and r.status not in [RiskStatus.RESOLVED, RiskStatus.CLOSED]]

    def get_records_needing_reminder(self) -> List[Dict]:
        now = datetime.now()
        reminders = []
        for record in self.records:
            for reminder in record.reminders:
                reminder_time = datetime.fromisoformat(reminder["time"])
                if not reminder["triggered"] and reminder_time <= now:
                    reminders.append({
                        "record_id": record.id,
                        "record_title": record.title,
                        "message": reminder["message"],
                        "reminder_time": reminder["time"]
                    })
                    reminder["triggered"] = True
        self.save_records()
        return reminders

    def get_summary(self) -> Dict:
        total = len(self.records)
        pending = len(self.get_records_by_status(RiskStatus.PENDING))
        processing = len(self.get_records_by_status(RiskStatus.PROCESSING))
        resolved = len(self.get_records_by_status(RiskStatus.RESOLVED))
        closed = len(self.get_records_by_status(RiskStatus.CLOSED))
        escalated = len(self.get_records_by_status(RiskStatus.ESCALATED))
        
        high_risk = len(self.get_records_by_level(RiskLevel.CRITICAL)) + len(self.get_records_by_level(RiskLevel.HIGH))
        overdue = len(self.get_overdue_records())
        
        category_counts = {}
        for cat in RiskCategory:
            category_counts[cat.value] = len(self.get_records_by_category(cat))

        return {
            "total": total,
            "pending": pending,
            "processing": processing,
            "resolved": resolved,
            "closed": closed,
            "escalated": escalated,
            "high_risk": high_risk,
            "overdue": overdue,
            "category_counts": category_counts,
            "updated_at": datetime.now().isoformat()
        }

    def search_records(self, keyword: str) -> List[RiskRecord]:
        keyword = keyword.lower()
        return [
            r for r in self.records
            if keyword in r.title.lower() or 
               keyword in r.description.lower() or 
               keyword in r.location.lower() or
               keyword in r.discovered_by.lower()
        ]

    def generate_report(self, period_days: int = 30) -> Dict:
        start_date = datetime.now() - timedelta(days=period_days)
        period_records = [
            r for r in self.records
            if datetime.fromisoformat(r.discovered_at) >= start_date
        ]
        
        level_counts = {level.value: 0 for level in RiskLevel}
        category_counts = {cat.value: 0 for cat in RiskCategory}
        status_counts = {status.value: 0 for status in RiskStatus}
        
        for record in period_records:
            level_counts[record.level.value] += 1
            category_counts[record.category.value] += 1
            status_counts[record.status.value] += 1

        return {
            "period": f"{period_days}天",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "total_records": len(period_records),
            "level_counts": level_counts,
            "category_counts": category_counts,
            "status_counts": status_counts,
            "records": [r.to_dict() for r in period_records]
        }