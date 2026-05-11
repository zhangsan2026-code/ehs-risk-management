from flask import Flask, render_template, request, redirect, url_for, jsonify, session, send_from_directory
import pandas as pd
import os
import re
import uuid
from datetime import datetime, timedelta
from risk_ledger import RiskLedger, RiskRecord, RiskLevel, RiskStatus, RiskCategory, PHOTOS_DIR
from ehs_standards import EHSStandardsLibrary
from ai_reminder import AIReminder
from notification_system import NotificationSystem, NotificationType, NotificationPriority

app = Flask(__name__)
app.secret_key = 'risk_management_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

risk_ledger = RiskLedger()
ehs_library = EHSStandardsLibrary()
ai_reminder = AIReminder(risk_ledger)
notification_system = NotificationSystem()

LAST_OVERDUE_CHECK = None

DATA_FILE = 'overtime_data.csv'

def init_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8-sig') as f:
            f.write('日期,加班楼层,加班部门,加班人员,预计加班时间,值班人员,备注\n')

def load_data():
    init_file()
    df = pd.read_csv(DATA_FILE, encoding='utf-8-sig')
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')

def extract_overtime_info(text):
    results = []
    lines = text.split('\n')
    
    common_depts = ["个人信贷部", "秩序部", "客服部", "工程部", "保洁部", "安保部", 
                  "行政部", "财务部", "人事部", "维修部", "运维部", "夜班", "白班",
                  "开放办公区", "开放式办公区", "办公室"]
    
    ignore_names = ["加班", "值班", "预计", "需要", "保持", "确认", "检查", "巡查", "留意",
                   "玻璃门", "电梯厅", "设备", "窗户", "空调", "灯光", "区域", "楼层",
                   "部门", "人员", "时间", "备注", "开启", "关闭", "已关", "已开",
                   "保持开", "需要保", "无加班", "楼层无", "无人员"]
    
    processed_lines = set()
    
    for line in lines:
        line = line.strip()
        if not line or len(line) < 3:
            continue
        
        if line in processed_lines:
            continue
        processed_lines.add(line)
        
        floor = ""
        dept = ""
        person = ""
        time_start = "18:00"
        time_end = "20:00"
        on_duty = ""
        notes = ""
        
        floor_match = re.search(r'([0-9]{1,2})[楼层]', line)
        if floor_match:
            floor = f"{floor_match.group(1)}楼"
        
        dept_codes = re.findall(r'(\d{4})', line)
        if dept_codes:
            code = dept_codes[0]
            floor_from_code = code[:2]
            if floor_from_code.isdigit() and int(floor_from_code) > 0 and int(floor_from_code) <= 99:
                if not floor:
                    floor = f"{floor_from_code}楼"
            dept = f"{code}开放式办公区"
        
        time_match = re.search(r'加班到\s*(\d{1,2}):(\d{2})', line)
        if time_match:
            time_end = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
        
        time_range_match = re.search(r'(\d{1,2}):(\d{2})[\s\-~到至]+(\d{1,2}):(\d{2})', line)
        if time_range_match:
            time_start = f"{int(time_range_match.group(1)):02d}:{time_range_match.group(2)}"
            time_end = f"{int(time_range_match.group(3)):02d}:{time_range_match.group(4)}"
        
        matched_depts = []
        for d in common_depts:
            if d in line:
                matched_depts.append(d)
        
        if matched_depts:
            dept = ",".join(matched_depts)
        
        complex_patterns = [
            r'([0-9]{1,2})[楼层]([\u4e00-\u9fa5]+部)([\u4e00-\u9fa5]{2,3})[总]?预计加班',
            r'([0-9]{1,2})[楼层]([\u4e00-\u9fa5]+部)([\u4e00-\u9fa5]{2,3})预计加班',
            r'([0-9]{1,2})[楼层]([\u4e00-\u9fa5]+部)([\u4e00-\u9fa5]{2,3})[总]?加班',
        ]
        
        found_person = ""
        for pattern in complex_patterns:
            match = re.search(pattern, line)
            if match:
                if not floor:
                    floor = f"{match.group(1)}楼"
                if not dept:
                    dept = match.group(2)
                found_person = match.group(3)
                break
        
        if not found_person:
            person_patterns = [
                r'([\u4e00-\u9fa5]{2,3})[总经]理?\s*[加值]班',
                r'([\u4e00-\u9fa5]{2,3})[总经]理?预计',
                r'[加值]班[\u4e00-\u9fa5]{2,3}[总经]理?',
                r'[\u4e00-\u9fa5]{2,3}在[0-9]{1,2}[楼层]',
                r'安排[\u4e00-\u9fa5]{2,3}',
                r'[\u4e00-\u9fa5]{2,3}安排',
                r'([\u4e00-\u9fa5]{2,3})\s*预计加班',
            ]
            
            for pattern in person_patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1) if match.groups() else match.group(0)
                    name = name.replace("加班", "").replace("值班", "").replace("预计", "").strip()
                    if len(name) >= 2 and name not in ignore_names and name not in common_depts:
                        found_person = name
                        break
        
        person = found_person
        
        notes_parts = []
        if "需要" in line or "需" in line:
            need_match = re.search(r'(需要|需)\s*(.*?)(?:，|。|！|\]|\)|$)', line)
            if need_match:
                notes_parts.append("需要" + need_match.group(2).strip())
        
        if "保持" in line:
            keep_match = re.search(r'保持\s*(.*?)(?:，|。|！|\]|\)|$)', line)
            if keep_match:
                notes_parts.append("保持" + keep_match.group(1).strip())
        
        if "留意" in line:
            note_match = re.search(r'留意\s*(.*?)(?:，|。|！|\]|\)|$)', line)
            if note_match:
                notes_parts.append("留意" + note_match.group(1).strip())
        
        if "检查" in line:
            check_match = re.search(r'检查\s*(.*?)(?:，|。|！|\]|\)|$)', line)
            if check_match:
                notes_parts.append("检查" + check_match.group(1).strip())
        
        notes = "；".join(notes_parts)
        
        has_overtime_keyword = any(kw in line for kw in ["加班", "值班", "延时"])
        has_dept_or_floor = floor or dept or dept_codes
        
        if has_overtime_keyword or has_dept_or_floor or notes:
            result = {
                '日期': datetime.now().strftime("%Y-%m-%d"),
                '加班楼层': floor,
                '部门': dept,
                '人员': person if person else "",
                '预计加班时间': f"{time_start}-{time_end}",
                '值班人员': on_duty,
                '备注': notes.strip()[:100]
            }
            results.append(result)
    
    return results

@app.route('/')
def index():
    summary = risk_ledger.get_summary()
    daily_summary = ai_reminder.generate_daily_summary()
    recent_records = sorted(risk_ledger.records, key=lambda x: x.discovered_at, reverse=True)[:5]
    return render_template('dashboard.html', summary=summary, daily_summary=daily_summary, recent_records=recent_records)

@app.route('/dashboard')
def dashboard():
    summary = risk_ledger.get_summary()
    daily_summary = ai_reminder.generate_daily_summary()
    recent_records = sorted(risk_ledger.records, key=lambda x: x.discovered_at, reverse=True)[:5]
    return render_template('dashboard.html', summary=summary, daily_summary=daily_summary, recent_records=recent_records)

@app.route('/risk/list')
def risk_list():
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    level_filter = request.args.get('level', '')
    keyword = request.args.get('keyword', '')
    
    records = risk_ledger.records
    
    if status_filter:
        try:
            records = risk_ledger.get_records_by_status(RiskStatus(status_filter))
        except:
            pass
    elif category_filter:
        try:
            records = risk_ledger.get_records_by_category(RiskCategory(category_filter))
        except:
            pass
    elif level_filter:
        try:
            records = risk_ledger.get_records_by_level(RiskLevel(level_filter))
        except:
            pass
    elif keyword:
        records = risk_ledger.search_records(keyword)
    
    records = sorted(records, key=lambda x: x.discovered_at, reverse=True)
    
    return render_template('risk_list.html', 
                           records=records,
                           status_filter=status_filter,
                           category_filter=category_filter,
                           level_filter=level_filter,
                           keyword=keyword,
                           status_options=[s.value for s in RiskStatus],
                           category_options=[c.value for c in RiskCategory],
                           level_options=[l.value for l in RiskLevel])

@app.route('/risk/add', methods=['GET', 'POST'])
def add_risk():
    if request.method == 'POST':
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        category = request.form.get('category', '')
        level = request.form.get('level', '')
        location = request.form.get('location', '')
        discovered_by = request.form.get('discovered_by', '')
        ehs_standard = request.form.get('ehs_standard', '')
        priority = int(request.form.get('priority', 3))
        corrective_dept = request.form.get('corrective_dept', '')
        corrective_by = request.form.get('corrective_by', '')
        
        photos = []
        if 'photos' in request.files:
            for file in request.files.getlist('photos'):
                if file and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    photo_name = f"{uuid.uuid4()}.{ext}"
                    file.save(os.path.join(PHOTOS_DIR, photo_name))
                    photos.append(photo_name)
        
        record = RiskRecord(
            title=title,
            description=description,
            category=RiskCategory(category),
            level=RiskLevel(level),
            location=location,
            discovered_by=discovered_by,
            ehs_standard=ehs_standard,
            priority=priority,
            photos=photos,
            corrective_dept=corrective_dept,
            corrective_by=corrective_by
        )
        
        risk_ledger.add_record(record)
        return redirect(url_for('risk_list'))
    
    ehs_standards = ehs_library.standards
    return render_template('risk_add.html',
                           categories=[c.value for c in RiskCategory],
                           levels=[l.value for l in RiskLevel],
                           ehs_standards=ehs_standards)

@app.route('/risk/detail/<record_id>')
def risk_detail(record_id):
    record = risk_ledger.get_record(record_id)
    if not record:
        return "风险记录不存在", 404
    
    related_standards = ehs_library.suggest_standards(record.category.value)
    return render_template('risk_detail.html', record=record, related_standards=related_standards, datetime=datetime)

@app.route('/risk/edit/<record_id>', methods=['GET', 'POST'])
def edit_risk(record_id):
    record = risk_ledger.get_record(record_id)
    if not record:
        return "风险记录不存在", 404
    
    if request.method == 'POST':
        updates = {
            'title': request.form.get('title', ''),
            'description': request.form.get('description', ''),
            'category': RiskCategory(request.form.get('category', '')),
            'level': RiskLevel(request.form.get('level', '')),
            'location': request.form.get('location', ''),
            'ehs_standard': request.form.get('ehs_standard', ''),
            'priority': int(request.form.get('priority', 3))
        }
        risk_ledger.update_record(record_id, updates)
        return redirect(url_for('risk_detail', record_id=record_id))
    
    ehs_standards = ehs_library.standards
    return render_template('risk_edit.html',
                           record=record,
                           categories=[c.value for c in RiskCategory],
                           levels=[l.value for l in RiskLevel],
                           ehs_standards=ehs_standards)

@app.route('/risk/assign/<record_id>', methods=['POST'])
def assign_risk(record_id):
    record = risk_ledger.get_record(record_id)
    if not record:
        return jsonify({"success": False, "message": "风险记录不存在"})
    
    assignee = request.form.get('assignee', '')
    record.assign(assignee)
    risk_ledger.save_records()
    return jsonify({"success": True, "message": f"已分配给 {assignee}"})

@app.route('/risk/update_progress/<record_id>', methods=['POST'])
def update_progress(record_id):
    record = risk_ledger.get_record(record_id)
    if not record:
        return jsonify({"success": False, "message": "风险记录不存在"})
    
    progress = int(request.form.get('progress', 0))
    record.update_progress(progress)
    risk_ledger.save_records()
    return jsonify({"success": True, "progress": record.progress})

@app.route('/risk/resolve/<record_id>', methods=['POST'])
def resolve_risk(record_id):
    record = risk_ledger.get_record(record_id)
    if not record:
        return jsonify({"success": False, "message": "风险记录不存在"})
    
    resolver = request.form.get('resolver', '')
    note = request.form.get('note', '')
    record.resolve(resolver, note)
    risk_ledger.save_records()
    return jsonify({"success": True, "message": "风险已解决"})

@app.route('/risk/delete/<record_id>', methods=['POST'])
def delete_risk(record_id):
    success = risk_ledger.delete_record(record_id)
    if success:
        return jsonify({"success": True, "message": "删除成功"})
    return jsonify({"success": False, "message": "删除失败"})

@app.route('/ehs/list')
def ehs_list():
    category_filter = request.args.get('category', '')
    keyword = request.args.get('keyword', '')
    
    standards = ehs_library.standards
    
    if category_filter:
        standards = ehs_library.get_standards_by_category(category_filter)
    elif keyword:
        standards = ehs_library.search_standards(keyword)
    
    return render_template('ehs_list.html',
                           standards=standards,
                           category_filter=category_filter,
                           keyword=keyword,
                           categories=ehs_library.get_categories())

@app.route('/ehs/detail/<code>')
def ehs_detail(code):
    standard = ehs_library.get_standard(code)
    if not standard:
        return "EHS标准不存在", 404
    return render_template('ehs_detail.html', standard=standard)

@app.route('/ehs/add', methods=['GET', 'POST'])
def add_ehs():
    if request.method == 'POST':
        code = request.form.get('code', '')
        title = request.form.get('title', '')
        category = request.form.get('category', '')
        content = request.form.get('content', '')
        version = request.form.get('version', '1.0')
        reference = request.form.get('reference', '')
        applicable_areas = request.form.get('applicable_areas', '').split(',')
        keywords = request.form.get('keywords', '').split(',')
        
        applicable_areas = [a.strip() for a in applicable_areas if a.strip()]
        keywords = [k.strip() for k in keywords if k.strip()]
        
        from ehs_standards import EHSStandard
        standard = EHSStandard(
            code=code,
            title=title,
            category=category,
            content=content,
            version=version,
            reference=reference,
            applicable_areas=applicable_areas,
            keywords=keywords
        )
        
        ehs_library.add_standard(standard)
        return redirect(url_for('ehs_list'))
    
    return render_template('ehs_add.html', categories=ehs_library.get_categories())

@app.route('/reminder/trigger')
def trigger_reminder():
    reminders = ai_reminder.check_and_trigger_reminders()
    return jsonify({"success": True, "reminders": reminders})

@app.route('/reminder/daily_summary')
def daily_summary():
    summary = ai_reminder.generate_daily_summary()
    return jsonify(summary)

@app.route('/risk/<risk_id>/check_item/add', methods=['POST'])
def add_check_item(risk_id):
    record = risk_ledger.get_record(risk_id)
    if not record:
        return jsonify({"success": False, "message": "风险记录不存在"})
    
    description = request.form.get('description', '')
    if not description:
        return jsonify({"success": False, "message": "请输入检查项描述"})
    
    record.add_check_item(description)
    risk_ledger.save_records()
    
    return jsonify({"success": True, "message": "检查项添加成功", "progress": record.progress})

@app.route('/risk/<risk_id>/check_item/<item_id>/complete', methods=['POST'])
def complete_check_item(risk_id, item_id):
    record = risk_ledger.get_record(risk_id)
    if not record:
        return jsonify({"success": False, "message": "风险记录不存在"})
    
    completed_by = request.form.get('completed_by', '')
    if not completed_by:
        return jsonify({"success": False, "message": "请输入完成人"})
    
    photo = ""
    if 'photo' in request.files:
        file = request.files['photo']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            photo = f"{uuid.uuid4()}.{ext}"
            file.save(os.path.join(PHOTOS_DIR, photo))
    
    record.complete_check_item(item_id, completed_by, photo)
    risk_ledger.save_records()
    
    notification_system.add_notification(
        risk_id=risk_id,
        risk_title=record.title,
        notification_type=NotificationType.PROGRESS_UPDATE,
        message=f"检查项已完成，当前进度: {record.progress}%",
        priority=NotificationPriority.MEDIUM
    )
    
    return jsonify({"success": True, "message": "检查项完成成功", "progress": record.progress})

@app.route('/risk/<risk_id>/submit_audit', methods=['POST'])
def submit_audit(risk_id):
    record = risk_ledger.get_record(risk_id)
    if not record:
        return jsonify({"success": False, "message": "风险记录不存在"})
    
    submitter = request.form.get('submitter', '')
    if not submitter:
        return jsonify({"success": False, "message": "请输入提交人"})
    
    after_photos = []
    if 'after_photos' in request.files:
        for file in request.files.getlist('after_photos'):
            if file and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                photo_name = f"{uuid.uuid4()}.{ext}"
                file.save(os.path.join(PHOTOS_DIR, photo_name))
                after_photos.append(photo_name)
    
    record.after_photos.extend(after_photos)
    
    if record.submit_for_audit(submitter):
        risk_ledger.save_records()
        
        notification_system.add_notification(
            risk_id=risk_id,
            risk_title=record.title,
            notification_type=NotificationType.NEW_RISK,
            message=f"风险整改完成，等待审核",
            priority=NotificationPriority.HIGH
        )
        
        return jsonify({"success": True, "message": "已提交审核"})
    else:
        return jsonify({"success": False, "message": "进度未达到100%，无法提交审核"})

@app.route('/risk/<risk_id>/audit', methods=['POST'])
def audit_risk(risk_id):
    record = risk_ledger.get_record(risk_id)
    if not record:
        return jsonify({"success": False, "message": "风险记录不存在"})
    
    auditor = request.form.get('auditor', '')
    approved = request.form.get('approved', 'false').lower() == 'true'
    note = request.form.get('note', '')
    
    if not auditor:
        return jsonify({"success": False, "message": "请输入审核人"})
    
    record.audit(auditor, approved, note)
    risk_ledger.save_records()
    
    if approved:
        notification_system.add_notification(
            risk_id=risk_id,
            risk_title=record.title,
            notification_type=NotificationType.RESOLVED,
            message=f"审核通过，风险已解决",
            priority=NotificationPriority.MEDIUM
        )
    else:
        notification_system.add_notification(
            risk_id=risk_id,
            risk_title=record.title,
            notification_type=NotificationType.OVERDUE_WARNING,
            message=f"审核驳回: {note}",
            priority=NotificationPriority.HIGH
        )
    
    return jsonify({"success": True, "message": "审核完成"})

@app.route('/audit/list')
def audit_list():
    records = risk_ledger.get_records_by_status("待审核")
    return render_template('audit_list.html', records=records)

@app.route('/reminder/trend')
def trend_prediction():
    trend = ai_reminder.predict_risk_trend(days=7)
    return jsonify(trend)

@app.route('/reminder/stats')
def reminder_stats():
    stats = ai_reminder.get_reminder_stats()
    return jsonify(stats)

@app.route('/overtime')
def overtime_index():
    df = load_data()
    records = []
    for i in range(len(df)):
        record = {
            'idx': i,
            'date': str(df.iloc[i]['日期']) if pd.notna(df.iloc[i]['日期']) else '',
            'floor': str(df.iloc[i]['加班楼层']) if pd.notna(df.iloc[i]['加班楼层']) else '',
            'dept': str(df.iloc[i]['加班部门']) if pd.notna(df.iloc[i]['加班部门']) else '',
            'person': str(df.iloc[i]['加班人员']) if pd.notna(df.iloc[i]['加班人员']) else '',
            'time': str(df.iloc[i]['预计加班时间']) if pd.notna(df.iloc[i]['预计加班时间']) else '',
            'on_duty': str(df.iloc[i]['值班人员']) if pd.notna(df.iloc[i]['值班人员']) else '',
            'notes': str(df.iloc[i]['备注']) if pd.notna(df.iloc[i]['备注']) else ''
        }
        records.append(record)
    return render_template('overtime_index.html', records=records)

@app.route('/overtime/add', methods=['GET', 'POST'])
def add_overtime():
    if request.method == 'POST':
        date = request.form.get('date', '')
        floor = request.form.get('floor', '')
        dept = request.form.get('department', '')
        person = request.form.get('person', '')
        time = request.form.get('time', '')
        on_duty = request.form.get('on_duty', '')
        notes = request.form.get('notes', '')
        
        df = load_data()
        new_row = pd.DataFrame([{
            '日期': date,
            '加班楼层': floor,
            '加班部门': dept,
            '加班人员': person,
            '预计加班时间': time,
            '值班人员': on_duty,
            '备注': notes
        }])
        df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        
        return redirect(url_for('overtime_index'))
    return render_template('overtime_add.html')

@app.route('/overtime/edit/<int:idx>', methods=['GET', 'POST'])
def edit_overtime(idx):
    df = load_data()
    if idx >= len(df):
        return redirect(url_for('overtime_index'))
    
    if request.method == 'POST':
        df.loc[idx, '日期'] = request.form.get('date', '')
        df.loc[idx, '加班楼层'] = request.form.get('floor', '')
        df.loc[idx, '加班部门'] = request.form.get('department', '')
        df.loc[idx, '加班人员'] = request.form.get('person', '')
        df.loc[idx, '预计加班时间'] = request.form.get('time', '')
        df.loc[idx, '值班人员'] = request.form.get('on_duty', '')
        df.loc[idx, '备注'] = request.form.get('notes', '')
        save_data(df)
        return redirect(url_for('overtime_index'))
    
    record = {
        'idx': idx,
        'date': str(df.iloc[idx]['日期']) if pd.notna(df.iloc[idx]['日期']) else '',
        'floor': str(df.iloc[idx]['加班楼层']) if pd.notna(df.iloc[idx]['加班楼层']) else '',
        'dept': str(df.iloc[idx]['加班部门']) if pd.notna(df.iloc[idx]['加班部门']) else '',
        'person': str(df.iloc[idx]['加班人员']) if pd.notna(df.iloc[idx]['加班人员']) else '',
        'time': str(df.iloc[idx]['预计加班时间']) if pd.notna(df.iloc[idx]['预计加班时间']) else '',
        'on_duty': str(df.iloc[idx]['值班人员']) if pd.notna(df.iloc[idx]['值班人员']) else '',
        'notes': str(df.iloc[idx]['备注']) if pd.notna(df.iloc[idx]['备注']) else ''
    }
    return render_template('overtime_edit.html', record=record)

@app.route('/overtime/delete/<int:idx>')
def delete_overtime(idx):
    df = load_data()
    if idx < len(df):
        df = df.drop(idx).reset_index(drop=True)
        save_data(df)
    return redirect(url_for('overtime_index'))

@app.route('/overtime/batch_delete', methods=['POST'])
def batch_delete_overtime():
    df = load_data()
    ids = request.form.getlist('ids')
    if ids:
        indices_to_delete = [int(idx) for idx in ids]
        indices_to_delete.sort(reverse=True)
        for idx in indices_to_delete:
            if idx < len(df):
                df = df.drop(idx).reset_index(drop=True)
        save_data(df)
    return redirect(url_for('overtime_index'))

@app.route('/overtime/parse', methods=['GET', 'POST'])
def parse_overtime_chat():
    parsed_results = session.get('parsed_results', [])
    
    if request.method == 'POST':
        chat_text = request.form.get('chat_text', '')
        parsed_results = extract_overtime_info(chat_text)
        session['parsed_results'] = parsed_results
    
    if request.args.get('add_all') == '1' and parsed_results:
        df = load_data()
        for result in parsed_results:
            new_row = pd.DataFrame([{
                '日期': result['日期'],
                '加班楼层': result['加班楼层'],
                '加班部门': result['部门'],
                '加班人员': result['人员'],
                '预计加班时间': result['预计加班时间'],
                '值班人员': result['值班人员'],
                '备注': result['备注']
            }])
            df = pd.concat([df, new_row], ignore_index=True)
        save_data(df)
        session.pop('parsed_results', None)
        return redirect(url_for('overtime_index'))
    
    return render_template('overtime_parse.html', parsed_results=parsed_results)

@app.route('/risk/photo/<photo_name>')
def risk_photo(photo_name):
    return send_from_directory(PHOTOS_DIR, photo_name)

def check_overdue_reminders():
    global LAST_OVERDUE_CHECK
    now = datetime.now()
    
    if LAST_OVERDUE_CHECK is None or now - LAST_OVERDUE_CHECK >= timedelta(hours=4):
        LAST_OVERDUE_CHECK = now
        
        for record in risk_ledger.records:
            if record.due_date:
                due_date = record.due_date
                overdue_days = (now - due_date).days
                
                if overdue_days >= 0:
                    if overdue_days == 0:
                        notification_system.add_notification(
                            risk_id=record.id,
                            risk_title=record.title,
                            notification_type=NotificationType.OVERDUE_WARNING,
                            message=f"风险即将逾期，截止日期: {due_date.strftime('%Y-%m-%d')}",
                            priority=NotificationPriority.HIGH
                        )
                    elif overdue_days >= 1:
                        notification_system.add_notification(
                            risk_id=record.id,
                            risk_title=record.title,
                            notification_type=NotificationType.OVERDUE_REMINDER,
                            message=f"风险已逾期 {overdue_days} 天，请尽快处理",
                            priority=NotificationPriority.URGENT
                        )

@app.route('/notifications')
def notifications():
    check_overdue_reminders()
    notifications = notification_system.get_notifications()
    unread_count = notification_system.get_unread_count()
    return render_template('notifications.html', notifications=notifications, unread_count=unread_count)

@app.route('/notifications/mark_read/<notification_id>')
def mark_notification_read(notification_id):
    notification_system.mark_as_read(notification_id)
    return redirect(url_for('notifications'))

@app.route('/notifications/mark_all_read')
def mark_all_notifications_read():
    notification_system.mark_all_read()
    return redirect(url_for('notifications'))

@app.route('/extension/apply/<risk_id>', methods=['GET', 'POST'])
def apply_extension(risk_id):
    record = risk_ledger.get_record(risk_id)
    if not record:
        return "风险记录不存在", 404
    
    if request.method == 'POST':
        requester = request.form.get('requester', '')
        reason = request.form.get('reason', '')
        requested_days = int(request.form.get('requested_days', 3))
        
        if not requester or not reason:
            return "请填写完整信息", 400
        
        notification_system.create_extension_request(
            risk_id=risk_id,
            risk_title=record.title,
            requester=requester,
            reason=reason,
            requested_days=requested_days
        )
        
        return redirect(url_for('risk_detail', record_id=risk_id))
    
    return render_template('extension_apply.html', record=record)

@app.route('/extension/approve')
def extension_approve_list():
    requests = notification_system.get_pending_requests()
    return render_template('extension_approve.html', requests=requests)

@app.route('/extension/approve/<request_id>', methods=['POST'])
def approve_extension(request_id):
    action = request.form.get('action', '')
    approver = request.form.get('approver', '')
    notes = request.form.get('notes', '')
    approved_days = int(request.form.get('approved_days', 0))
    
    if action == 'approve':
        if notification_system.approve_extension(request_id, approver, approved_days, notes):
            req = next((r for r in notification_system.extension_requests if r.id == request_id), None)
            if req:
                record = risk_ledger.get_record(req.risk_id)
                if record and record.due_date:
                    record.due_date = record.due_date + timedelta(days=approved_days)
                    risk_ledger.save_records()
    elif action == 'reject':
        notification_system.reject_extension(request_id, approver, notes)
    
    return redirect(url_for('extension_approve_list'))

@app.route('/api/risk/summary')
def api_risk_summary():
    return jsonify(risk_ledger.get_summary())

@app.route('/api/risk/list')
def api_risk_list():
    records = risk_ledger.records
    return jsonify([r.to_dict() for r in records])

@app.route('/api/ehs/summary')
def api_ehs_summary():
    return jsonify(ehs_library.get_summary())

@app.route('/api/notifications/count')
def api_notification_count():
    check_overdue_reminders()
    return jsonify({"count": notification_system.get_unread_count()})

@app.route('/api/notifications')
def api_notifications():
    check_overdue_reminders()
    notifications = notification_system.get_notifications(limit=20)
    return jsonify([n.to_dict() for n in notifications])

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)