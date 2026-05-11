import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum

NOTIFICATION_DATA_DIR = os.path.join(os.path.dirname(__file__), "notification_data")
os.makedirs(NOTIFICATION_DATA_DIR, exist_ok=True)

class NotificationType(Enum):
    NEW_RISK = "新隐患"
    RESOLVED = "整改完成"
    PROGRESS_UPDATE = "进度更新"
    OVERDUE_WARNING = "即将逾期"
    OVERDUE = "已逾期"
    OVERDUE_REMINDER = "逾期提醒"
    EXTENSION_REQUEST = "延期申请"
    EXTENSION_APPROVED = "延期批准"
    EXTENSION_REJECTED = "延期驳回"

class NotificationPriority(Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    URGENT = "紧急"

class Notification:
    def __init__(
        self,
        risk_id: str,
        risk_title: str,
        notification_type: NotificationType,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        assignee: str = "",
        read: bool = False,
        created_at: Optional[datetime] = None
    ):
        self.id = str(os.urandom(8).hex())
        self.risk_id = risk_id
        self.risk_title = risk_title
        self.notification_type = notification_type
        self.message = message
        self.priority = priority
        self.assignee = assignee
        self.read = read
        self.created_at = created_at or datetime.now()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "risk_id": self.risk_id,
            "risk_title": self.risk_title,
            "notification_type": self.notification_type.value,
            "message": self.message,
            "priority": self.priority.value,
            "assignee": self.assignee,
            "read": self.read,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Notification':
        notification = cls(
            risk_id=data["risk_id"],
            risk_title=data["risk_title"],
            notification_type=NotificationType(data["notification_type"]),
            message=data["message"],
            priority=NotificationPriority(data["priority"]),
            assignee=data.get("assignee", ""),
            read=data.get("read", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        )
        notification.id = data["id"]
        return notification

class ExtensionRequest:
    def __init__(
        self,
        risk_id: str,
        risk_title: str,
        requester: str,
        reason: str,
        requested_days: int,
        status: str = "pending"
    ):
        self.id = str(os.urandom(8).hex())
        self.risk_id = risk_id
        self.risk_title = risk_title
        self.requester = requester
        self.reason = reason
        self.requested_days = requested_days
        self.status = status
        self.created_at = datetime.now()
        self.approved_by = ""
        self.approved_days = 0
        self.approved_at = None
        self.notes = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "risk_id": self.risk_id,
            "risk_title": self.risk_title,
            "requester": self.requester,
            "reason": self.reason,
            "requested_days": self.requested_days,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "approved_by": self.approved_by,
            "approved_days": self.approved_days,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "notes": self.notes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ExtensionRequest':
        request = cls(
            risk_id=data["risk_id"],
            risk_title=data["risk_title"],
            requester=data["requester"],
            reason=data["reason"],
            requested_days=data["requested_days"],
            status=data.get("status", "pending")
        )
        request.id = data["id"]
        request.approved_by = data.get("approved_by", "")
        request.approved_days = data.get("approved_days", 0)
        request.approved_at = datetime.fromisoformat(data["approved_at"]) if data.get("approved_at") else None
        request.notes = data.get("notes", "")
        return request

class NotificationSystem:
    def __init__(self):
        self.notifications: List[Notification] = []
        self.extension_requests: List[ExtensionRequest] = []
        self.load_notifications()
        self.load_extension_requests()

    def load_notifications(self):
        file_path = os.path.join(NOTIFICATION_DATA_DIR, "notifications.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.notifications = [Notification.from_dict(item) for item in data]
            except Exception:
                self.notifications = []

    def save_notifications(self):
        file_path = os.path.join(NOTIFICATION_DATA_DIR, "notifications.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([n.to_dict() for n in self.notifications], f, ensure_ascii=False, indent=2)

    def load_extension_requests(self):
        file_path = os.path.join(NOTIFICATION_DATA_DIR, "extension_requests.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.extension_requests = [ExtensionRequest.from_dict(item) for item in data]
            except Exception:
                self.extension_requests = []

    def save_extension_requests(self):
        file_path = os.path.join(NOTIFICATION_DATA_DIR, "extension_requests.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([r.to_dict() for r in self.extension_requests], f, ensure_ascii=False, indent=2)

    def add_notification(
        self,
        risk_id: str,
        risk_title: str,
        notification_type: NotificationType,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        assignee: str = ""
    ):
        notification = Notification(
            risk_id=risk_id,
            risk_title=risk_title,
            notification_type=notification_type,
            message=message,
            priority=priority,
            assignee=assignee
        )
        self.notifications.append(notification)
        self.save_notifications()
        return notification

    def mark_as_read(self, notification_id: str):
        for n in self.notifications:
            if n.id == notification_id:
                n.read = True
                self.save_notifications()
                break

    def mark_all_read(self):
        for n in self.notifications:
            n.read = False
        self.save_notifications()

    def get_unread_count(self) -> int:
        return sum(1 for n in self.notifications if not n.read)

    def get_notifications(self, limit: int = 50) -> List[Notification]:
        return sorted(self.notifications, key=lambda x: x.created_at, reverse=True)[:limit]

    def get_notifications_by_type(self, notification_type: NotificationType) -> List[Notification]:
        return [n for n in self.notifications if n.notification_type == notification_type]

    def create_extension_request(
        self,
        risk_id: str,
        risk_title: str,
        requester: str,
        reason: str,
        requested_days: int
    ) -> ExtensionRequest:
        request = ExtensionRequest(
            risk_id=risk_id,
            risk_title=risk_title,
            requester=requester,
            reason=reason,
            requested_days=requested_days
        )
        self.extension_requests.append(request)
        self.save_extension_requests()
        
        self.add_notification(
            risk_id=risk_id,
            risk_title=risk_title,
            notification_type=NotificationType.EXTENSION_REQUEST,
            message=f"申请延期 {requested_days} 天，原因: {reason}",
            priority=NotificationPriority.HIGH
        )
        
        return request

    def approve_extension(self, request_id: str, approver: str, approved_days: int, notes: str = ""):
        for req in self.extension_requests:
            if req.id == request_id:
                req.status = "approved"
                req.approved_by = approver
                req.approved_days = approved_days
                req.approved_at = datetime.now()
                req.notes = notes
                self.save_extension_requests()
                
                self.add_notification(
                    risk_id=req.risk_id,
                    risk_title=req.risk_title,
                    notification_type=NotificationType.EXTENSION_APPROVED,
                    message=f"延期申请已批准，延长 {approved_days} 天",
                    priority=NotificationPriority.MEDIUM
                )
                return True
        return False

    def reject_extension(self, request_id: str, approver: str, notes: str = ""):
        for req in self.extension_requests:
            if req.id == request_id:
                req.status = "rejected"
                req.approved_by = approver
                req.approved_at = datetime.now()
                req.notes = notes
                self.save_extension_requests()
                
                self.add_notification(
                    risk_id=req.risk_id,
                    risk_title=req.risk_title,
                    notification_type=NotificationType.EXTENSION_REJECTED,
                    message=f"延期申请已驳回: {notes}",
                    priority=NotificationPriority.HIGH
                )
                return True
        return False

    def get_pending_requests(self) -> List[ExtensionRequest]:
        return [req for req in self.extension_requests if req.status == "pending"]

    def get_requests_by_risk(self, risk_id: str) -> List[ExtensionRequest]:
        return [req for req in self.extension_requests if req.risk_id == risk_id]
