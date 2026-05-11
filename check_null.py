
import pandas as pd

df = pd.read_excel("repair_records.xlsx")

print("完成情况列空值统计：")
print("-" * 50)

total_null = df["完成情况"].isna().sum()
total = len(df)
print(f"总记录数：{total}")
print(f"空值数量：{total_null}")
print(f"空值比例：{(total_null/total*100):.1f}%")
print()

print("各部门空值统计：")
print("-" * 50)
dept_null = df.groupby("部门")["完成情况"].apply(lambda x: x.isna().sum())
dept_total = df.groupby("部门").size()

for dept in dept_null.index:
    null_count = dept_null[dept]
    total_count = dept_total[dept]
    print(f"{dept}：空值 {null_count} / 总计 {total_count} ({(null_count/total_count*100):.1f}%)")

print()
print("非空值的完成情况类型：")
print("-" * 50)
non_null_values = df[df["完成情况"].notna()]["完成情况"].value_counts()
for value, count in non_null_values.items():
    print(f"'{value}'：{count} 条")
