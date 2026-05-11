
import pandas as pd

df = pd.read_excel("repair_records.xlsx")

df = df.rename(columns={"备注": "完成情况"})

df.to_excel("repair_records.xlsx", index=False)

print("已将'备注'列改名为'完成情况'")
