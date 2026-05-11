
import pandas as pd

df = pd.read_excel("repair_records.xlsx")

print("修复前数据：")
print(df.head(3).to_string())

temp_repairman = df['报修人'].copy()
temp_issue = df['报修事项'].copy()
temp_location = df['地点'].copy()

df['报修人'] = temp_location
df['报修事项'] = temp_repairman
df['地点'] = temp_issue

print("\n修复后数据：")
print(df.head(3).to_string())

df.to_excel("repair_records.xlsx", index=False)
print("\n数据已修复并保存！")
