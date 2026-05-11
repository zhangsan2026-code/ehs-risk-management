
import pandas as pd

df = pd.read_excel("repair_records.xlsx")

print("当前数据文件列顺序：")
print("-" * 50)
for i, col in enumerate(df.columns):
    print(f"{i+1}. {col}")

print("\n前3行数据预览：")
print("-" * 50)
print(df.head(3).to_string())
