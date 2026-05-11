
import pandas as pd
import os

def verify_data():
    source_file = r"c:\Users\lenovo\Desktop\2026年华润银行大厦综合信息记录表.xlsx"
    target_file = "repair_records.xlsx"
    
    print("=" * 70)
    print("          数据核对分析报告")
    print("=" * 70)
    
    if not os.path.exists(source_file):
        print(f"错误：源文件不存在 - {source_file}")
        return
    
    if not os.path.exists(target_file):
        print(f"错误：目标文件不存在 - {target_file}")
        return
    
    xls = pd.ExcelFile(source_file)
    source_records = []
    
    print("\n1. 读取源文件数据...")
    
    df1 = pd.read_excel(xls, sheet_name='润创港湾报事报修记录表', header=1)
    df1 = df1[1:]
    df1 = df1[df1['Unnamed: 5'].notna()]
    for _, row in df1.iterrows():
        source_records.append({
            "来源": "润创港湾",
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "润创港湾",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else "",
            "完成状态": "已整改" if str(row['Unnamed: 7']).strip() == "已完成" else "未整改",
            "完成情况": str(row['Unnamed: 8']).strip() if pd.notna(row['Unnamed: 8']) else ""
        })
    
    df2 = pd.read_excel(xls, sheet_name='华润银行大厦报事报修记录表', header=1)
    df2 = df2[1:]
    df2 = df2[df2['Unnamed: 5'].notna()]
    for _, row in df2.iterrows():
        status = "已整改" if str(row['Unnamed: 7']).strip() in ['已完成', '工程已处理', '完成', '已处理'] else "未整改"
        source_records.append({
            "来源": "华润银行大厦",
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "华润银行大厦",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else "",
            "完成状态": status,
            "完成情况": str(row['Unnamed: 8']).strip() if pd.notna(row['Unnamed: 8']) else ""
        })
    
    df3 = pd.read_excel(xls, sheet_name='（楼层内服）信息反馈表', header=1)
    df3 = df3[1:]
    df3 = df3[(df3['Unnamed: 5'].notna()) | (df3['Unnamed: 6'] == '未完成')]
    for _, row in df3.iterrows():
        status = "已整改" if str(row['Unnamed: 7']).strip() in ['已完成', '工程已处理', '完成', '已处理'] else "未整改"
        source_records.append({
            "来源": "楼层内服",
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "楼层内服",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else "",
            "完成状态": status,
            "完成情况": str(row['Unnamed: 8']).strip() if pd.notna(row['Unnamed: 8']) else ""
        })
    
    df4 = pd.read_excel(xls, sheet_name='食堂问题反馈记录表', header=1)
    df4 = df4[1:]
    df4 = df4[df4['Unnamed: 3'].notna()]
    for _, row in df4.iterrows():
        status = "已整改" if str(row['Unnamed: 4']).strip() == "完成" else "未整改"
        source_records.append({
            "来源": "食堂",
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "食堂",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "完成状态": status,
            "完成情况": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else ""
        })
    
    source_df = pd.DataFrame(source_records)
    
    target_df = pd.read_excel(target_file)
    
    print(f"\n2. 数据量对比：")
    print("-" * 50)
    print(f"源文件记录数：{len(source_df)}")
    print(f"系统记录数：{len(target_df)}")
    print(f"差异：{abs(len(source_df) - len(target_df))} 条")
    
    if len(source_df) != len(target_df):
        print(" ⚠️ 警告：记录数不一致！")
    
    print(f"\n3. 各部门数据对比：")
    print("-" * 50)
    
    source_dept = source_df.groupby('部门').size()
    target_dept = target_df.groupby('部门').size()
    
    all_depts = set(source_dept.index) | set(target_dept.index)
    
    for dept in sorted(all_depts):
        source_count = source_dept.get(dept, 0)
        target_count = target_dept.get(dept, 0)
        status = "✅" if source_count == target_count else "❌"
        print(f" {status} {dept}: 源文件={source_count}, 系统={target_count}")
    
    print(f"\n4. 报事日期格式检查：")
    print("-" * 50)
    
    invalid_dates = []
    for idx, row in target_df.iterrows():
        date_str = str(row['报修日期']).strip()
        if date_str and date_str != 'nan':
            try:
                pd.to_datetime(date_str)
            except:
                invalid_dates.append((idx + 1, date_str))
    
    if invalid_dates:
        print(f" ⚠️ 发现 {len(invalid_dates)} 条日期格式异常记录：")
        for seq, date in invalid_dates[:5]:
            print(f"   序号{seq}: {date}")
        if len(invalid_dates) > 5:
            print(f"   ... 还有 {len(invalid_dates) - 5} 条")
    else:
        print(" ✅ 所有日期格式均有效")
    
    print(f"\n5. 完成状态一致性检查：")
    print("-" * 50)
    
    source_status_counts = source_df['完成状态'].value_counts()
    target_status_counts = target_df['完成状态'].value_counts()
    
    print(f"源文件 - 已整改: {source_status_counts.get('已整改', 0)}, 未整改: {source_status_counts.get('未整改', 0)}")
    print(f"系统   - 已整改: {target_status_counts.get('已整改', 0)}, 未整改: {target_status_counts.get('未整改', 0)}")
    
    if source_status_counts.get('已整改', 0) == target_status_counts.get('已整改', 0):
        print(" ✅ 已整改数量一致")
    else:
        print(" ❌ 已整改数量不一致")
    
    print(f"\n6. 数据完整性检查：")
    print("-" * 50)
    
    target_missing = target_df.isna().sum()
    has_missing = False
    for col, count in target_missing.items():
        if count > 0:
            has_missing = True
            print(f" ⚠️ {col} 列有 {count} 个空值")
    
    if not has_missing:
        print(" ✅ 无空值")
    
    print(f"\n7. 日期范围统计：")
    print("-" * 50)
    
    valid_dates = pd.to_datetime(target_df['报修日期'], errors='coerce')
    valid_dates = valid_dates.dropna()
    
    if len(valid_dates) > 0:
        min_date = valid_dates.min().strftime('%Y-%m-%d')
        max_date = valid_dates.max().strftime('%Y-%m-%d')
        print(f"最早日期：{min_date}")
        print(f"最晚日期：{max_date}")
        print(f"日期跨度：{(valid_dates.max() - valid_dates.min()).days} 天")
    else:
        print(" ⚠️ 无有效日期")
    
    print("\n" + "=" * 70)
    print("          核对完成")
    print("=" * 70)

if __name__ == "__main__":
    verify_data()
