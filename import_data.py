
import pandas as pd
import os

def import_from_excel():
    source_file = r"c:\Users\lenovo\Desktop\2026年华润银行大厦综合信息记录表.xlsx"
    target_file = "repair_records.xlsx"
    
    if not os.path.exists(source_file):
        print(f"错误：未找到文件 {source_file}")
        return
    
    xls = pd.ExcelFile(source_file)
    all_records = []
    
    print("正在导入数据...")
    
    df1 = pd.read_excel(xls, sheet_name='润创港湾报事报修记录表', header=1)
    df1 = df1[1:]
    df1 = df1[df1['Unnamed: 5'].notna()]
    for _, row in df1.iterrows():
        all_records.append({
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "润创港湾",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else "",
            "完成状态": "已整改" if str(row['Unnamed: 7']).strip() == "已完成" else "未整改",
            "备注": str(row['Unnamed: 8']).strip() if pd.notna(row['Unnamed: 8']) else ""
        })
    print(f"已导入润创港湾：{len([r for r in all_records if r['部门'] == '润创港湾'])} 条")
    
    df2 = pd.read_excel(xls, sheet_name='华润银行大厦报事报修记录表', header=1)
    df2 = df2[1:]
    df2 = df2[df2['Unnamed: 5'].notna()]
    for _, row in df2.iterrows():
        status = "已整改" if str(row['Unnamed: 7']).strip() in ['已完成', '工程已处理', '完成', '已处理'] else "未整改"
        all_records.append({
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "华润银行大厦",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else "",
            "完成状态": status,
            "备注": str(row['Unnamed: 8']).strip() if pd.notna(row['Unnamed: 8']) else ""
        })
    print(f"已导入华润银行大厦：{len([r for r in all_records if r['部门'] == '华润银行大厦'])} 条")
    
    df3 = pd.read_excel(xls, sheet_name='（楼层内服）信息反馈表', header=1)
    df3 = df3[1:]
    df3 = df3[(df3['Unnamed: 5'].notna()) | (df3['Unnamed: 6'] == '未完成')]
    for _, row in df3.iterrows():
        status = "已整改" if str(row['Unnamed: 7']).strip() in ['已完成', '工程已处理', '完成', '已处理'] else "未整改"
        all_records.append({
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "楼层内服",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else "",
            "完成状态": status,
            "备注": str(row['Unnamed: 8']).strip() if pd.notna(row['Unnamed: 8']) else ""
        })
    print(f"已导入楼层内服：{len([r for r in all_records if r['部门'] == '楼层内服'])} 条")
    
    df4 = pd.read_excel(xls, sheet_name='食堂问题反馈记录表', header=1)
    df4 = df4[1:]
    df4 = df4[df4['Unnamed: 3'].notna()]
    for _, row in df4.iterrows():
        status = "已整改" if str(row['Unnamed: 4']).strip() == "完成" else "未整改"
        all_records.append({
            "报修人": str(row['Unnamed: 1']).strip() if pd.notna(row['Unnamed: 1']) else "",
            "部门": "食堂",
            "报修事项": str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else "",
            "地点": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "报修日期": str(row['Unnamed: 3']).strip() if pd.notna(row['Unnamed: 3']) else "",
            "完成状态": status,
            "备注": str(row['Unnamed: 5']).strip() if pd.notna(row['Unnamed: 5']) else ""
        })
    print(f"已导入食堂：{len([r for r in all_records if r['部门'] == '食堂'])} 条")
    
    df = pd.DataFrame(all_records)
    df['序号'] = range(1, len(df) + 1)
    df = df[['序号', '报修人', '部门', '报修事项', '地点', '报修日期', '完成状态', '备注']]
    
    df.to_excel(target_file, index=False)
    print(f"\n✅ 导入完成！共导入 {len(df)} 条记录")
    print(f"文件已保存为：{target_file}")

if __name__ == "__main__":
    import_from_excel()
