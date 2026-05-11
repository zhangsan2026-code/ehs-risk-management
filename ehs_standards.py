import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

EHS_DATA_DIR = os.path.join(os.path.dirname(__file__), "ehs_data")
os.makedirs(EHS_DATA_DIR, exist_ok=True)

class EHSStandard:
    def __init__(
        self,
        code: str,
        title: str,
        category: str,
        content: str,
        version: str = "1.0",
        effective_date: Optional[datetime] = None,
        reference: str = "",
        applicable_areas: List[str] = None,
        keywords: List[str] = None
    ):
        self.code = code
        self.title = title
        self.category = category
        self.content = content
        self.version = version
        self.effective_date = effective_date or datetime.now()
        self.reference = reference
        self.applicable_areas = applicable_areas or []
        self.keywords = keywords or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "code": self.code,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "version": self.version,
            "effective_date": self.effective_date.isoformat(),
            "reference": self.reference,
            "applicable_areas": self.applicable_areas,
            "keywords": self.keywords,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'EHSStandard':
        standard = cls(
            code=data["code"],
            title=data["title"],
            category=data["category"],
            content=data["content"],
            version=data.get("version", "1.0"),
            effective_date=datetime.fromisoformat(data["effective_date"]) if data.get("effective_date") else datetime.now(),
            reference=data.get("reference", ""),
            applicable_areas=data.get("applicable_areas", []),
            keywords=data.get("keywords", [])
        )
        standard.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        standard.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        return standard

class EHSStandardsLibrary:
    def __init__(self):
        self.standards: List[EHSStandard] = []
        self.categories = set()
        self.load_standards()
        self._load_default_standards()

    def load_standards(self):
        standards_file = os.path.join(EHS_DATA_DIR, "ehs_standards.json")
        if os.path.exists(standards_file):
            try:
                with open(standards_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.standards = [EHSStandard.from_dict(item) for item in data]
                    self.categories = {s.category for s in self.standards}
            except Exception:
                self.standards = []

    def save_standards(self):
        standards_file = os.path.join(EHS_DATA_DIR, "ehs_standards.json")
        with open(standards_file, 'w', encoding='utf-8') as f:
            json.dump([s.to_dict() for s in self.standards], f, ensure_ascii=False, indent=2)

    def _load_default_standards(self):
        if not self.standards:
            default_standards = [
                {
                    "code": "EHS-F-001",
                    "title": "消防安全管理制度",
                    "category": "消防安全",
                    "content": "1. 所有员工必须遵守消防安全规定，严禁在禁烟区域吸烟。\n2. 定期检查消防设施，确保灭火器、消防栓完好有效。\n3. 保持消防通道畅通，不得堆放杂物。\n4. 定期组织消防演练，确保员工掌握灭火器材使用方法。\n5. 发现火灾隐患应立即报告并采取措施消除。",
                    "version": "1.0",
                    "reference": "GB 25201-2010",
                    "applicable_areas": ["办公区", "机房", "仓库", "公共区域"],
                    "keywords": ["消防", "安全", "灭火", "疏散"]
                },
                {
                    "code": "EHS-S-001",
                    "title": "治安保卫管理规定",
                    "category": "治安安全",
                    "content": "1. 来访人员必须进行登记，佩戴访客证。\n2. 非工作时间出入需出示有效证件并登记。\n3. 贵重物品需妥善保管，重要区域需刷卡进入。\n4. 发现可疑人员或异常情况应立即报告安保人员。\n5. 监控设备应保持24小时正常运行。",
                    "version": "1.0",
                    "reference": "企业内部安全管理规范",
                    "applicable_areas": ["办公区", "出入口", "停车场", "设备间"],
                    "keywords": ["安保", "访客", "门禁", "监控"]
                },
                {
                    "code": "EHS-E-001",
                    "title": "环境管理标准",
                    "category": "环境安全",
                    "content": "1. 垃圾分类投放，可回收物与有害垃圾分开处理。\n2. 节约用水用电，下班后关闭不必要的设备电源。\n3. 化学品需妥善储存，防止泄漏污染。\n4. 定期进行环境监测，确保符合环保要求。\n5. 禁止在办公区域使用高污染物品。",
                    "version": "1.0",
                    "reference": "GB/T 24001-2016",
                    "applicable_areas": ["办公区", "实验室", "仓库", "卫生间"],
                    "keywords": ["环保", "节能", "垃圾分类", "污染"]
                },
                {
                    "code": "EHS-H-001",
                    "title": "职业健康管理规范",
                    "category": "职业健康",
                    "content": "1. 定期组织员工进行健康体检。\n2. 提供必要的劳动防护用品，确保正确使用。\n3. 工作场所应保持良好的通风和照明条件。\n4. 合理安排工作时间，避免过度劳累。\n5. 提供心理健康咨询服务，关注员工身心健康。",
                    "version": "1.0",
                    "reference": "GBZ 1-2010",
                    "applicable_areas": ["办公区", "车间", "施工现场", "机房"],
                    "keywords": ["健康", "体检", "防护", "心理"]
                },
                {
                    "code": "EHS-EQ-001",
                    "title": "设备安全操作规程",
                    "category": "设备安全",
                    "content": "1. 设备操作人员必须经过培训并持证上岗。\n2. 定期对设备进行维护保养，记录维护情况。\n3. 设备运行前需进行安全检查，确认无异常。\n4. 设备故障时应立即停机并报告维修人员。\n5. 严格按照操作规程操作，严禁违规操作。",
                    "version": "1.0",
                    "reference": "设备维护管理规范",
                    "applicable_areas": ["机房", "配电室", "设备间", "维修车间"],
                    "keywords": ["设备", "维护", "操作", "故障"]
                },
                {
                    "code": "EHS-T-001",
                    "title": "交通安全管理规定",
                    "category": "交通安全",
                    "content": "1. 驾驶车辆必须遵守交通规则，严禁酒后驾车。\n2. 公司车辆需定期进行安全检查和保养。\n3. 行人应走人行道，注意交通安全。\n4. 停车场内限速行驶，有序停放车辆。\n5. 非机动车应停放在指定区域。",
                    "version": "1.0",
                    "reference": "道路交通安全法",
                    "applicable_areas": ["停车场", "出入口", "周边道路"],
                    "keywords": ["交通", "车辆", "停车", "驾驶"]
                },
                {
                    "code": "EHS-P-001",
                    "title": "安全检查流程规范",
                    "category": "流程合规",
                    "content": "1. 每日进行安全巡检，记录发现的问题。\n2. 每周进行专项安全检查，重点关注高风险区域。\n3. 每月进行全面安全检查，形成检查报告。\n4. 对发现的隐患应及时整改，跟踪整改情况。\n5. 定期召开安全会议，通报安全状况。",
                    "version": "1.0",
                    "reference": "企业安全检查规范",
                    "applicable_areas": ["全区域"],
                    "keywords": ["检查", "巡检", "隐患", "整改"]
                },
                {
                    "code": "EHS-C-001",
                    "title": "外包单位安全管理要求",
                    "category": "外包管理",
                    "content": "1. 外包单位必须具备相应的资质和安全保障能力。\n2. 签订安全协议，明确双方安全责任。\n3. 外包人员进场前需进行安全培训。\n4. 对外包工作进行全程安全监督。\n5. 定期评估外包单位的安全绩效。",
                    "version": "1.0",
                    "reference": "外包安全管理规范",
                    "applicable_areas": ["施工现场", "外包作业区"],
                    "keywords": ["外包", "资质", "培训", "监督"]
                }
            ]
            for std_data in default_standards:
                std = EHSStandard(
                    code=std_data["code"],
                    title=std_data["title"],
                    category=std_data["category"],
                    content=std_data["content"],
                    version=std_data["version"],
                    reference=std_data["reference"],
                    applicable_areas=std_data["applicable_areas"],
                    keywords=std_data["keywords"]
                )
                self.standards.append(std)
            self.categories = {s.category for s in self.standards}
            self.save_standards()

    def add_standard(self, standard: EHSStandard):
        self.standards.append(standard)
        self.categories.add(standard.category)
        self.save_standards()
        return standard

    def get_standard(self, code: str) -> Optional[EHSStandard]:
        for standard in self.standards:
            if standard.code == code:
                return standard
        return None

    def get_standards_by_category(self, category: str) -> List[EHSStandard]:
        return [s for s in self.standards if s.category == category]

    def search_standards(self, keyword: str) -> List[EHSStandard]:
        keyword = keyword.lower()
        return [
            s for s in self.standards
            if keyword in s.title.lower() or 
               keyword in s.content.lower() or
               keyword in s.code.lower() or
               any(keyword in kw.lower() for kw in s.keywords)
        ]

    def update_standard(self, code: str, updates: Dict):
        standard = self.get_standard(code)
        if standard:
            for key, value in updates.items():
                if hasattr(standard, key):
                    setattr(standard, key, value)
            standard.updated_at = datetime.now()
            self.save_standards()
            return standard
        return None

    def delete_standard(self, code: str) -> bool:
        standard = self.get_standard(code)
        if standard:
            self.standards.remove(standard)
            self.save_standards()
            return True
        return False

    def get_categories(self) -> List[str]:
        return sorted(list(self.categories))

    def get_summary(self) -> Dict:
        category_counts = {}
        for cat in self.categories:
            category_counts[cat] = len(self.get_standards_by_category(cat))
        
        return {
            "total_standards": len(self.standards),
            "total_categories": len(self.categories),
            "category_counts": category_counts,
            "updated_at": datetime.now().isoformat()
        }

    def suggest_standards(self, risk_category: str) -> List[EHSStandard]:
        category_mapping = {
            "消防安全": "消防安全",
            "治安安全": "治安安全",
            "环境安全": "环境安全",
            "职业健康": "职业健康",
            "设备安全": "设备安全",
            "交通安全": "交通安全",
            "流程合规": "流程合规",
            "外包管理": "外包管理",
            "其他": "其他"
        }
        
        target_category = category_mapping.get(risk_category, risk_category)
        return self.get_standards_by_category(target_category)