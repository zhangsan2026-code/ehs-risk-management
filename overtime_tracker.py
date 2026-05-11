import pandas as pd
import os
import re
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

class OvertimeTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("珠海华润银行大厦延时加班统计表")
        self.root.geometry("1000x700")
        
        self.df = pd.DataFrame(columns=["日期", "加班楼层", "加班部门", "加班人员", "预计加班时间", "值班人员", "备注"])
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Button(toolbar, text="添加记录", command=self.add_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导入数据", command=self.import_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导出报表", command=self.export_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="编辑记录", command=self.edit_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="删除记录", command=self.delete_record).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="聊天解析", command=self.parse_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="清空数据", command=self.clear_data).pack(side=tk.LEFT, padx=5)
        
        self.tree_frame = ttk.Frame(main_frame)
        self.tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        scroll_y = ttk.Scrollbar(self.tree_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x = ttk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree = ttk.Treeview(self.tree_frame, yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.tree.pack(expand=True, fill='both')
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.show_tree_context_menu)
        
        self.tree_context_menu = tk.Menu(self.root, tearoff=0)
        self.tree_context_menu.add_command(label="编辑记录", command=self.edit_record)
        self.tree_context_menu.add_command(label="删除记录", command=self.delete_record)
        
        self.update_tree()
        
        self.status_bar = ttk.Label(main_frame, text="就绪", relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E))
    
    def show_tree_context_menu(self, event):
        try:
            self.tree.selection_set(self.tree.identify_row(event.y))
            self.tree_context_menu.post(event.x_root, event.y_root)
        except:
            pass
    
    def on_double_click(self, event):
        self.edit_record()
    
    def update_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.tree["columns"] = list(self.df.columns)
        self.tree["show"] = "headings"
        
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        for idx, row in self.df.iterrows():
            self.tree.insert("", "end", iid=idx, values=list(row))
    
    def add_record(self, edit_mode=False, edit_idx=None, initial_data=None):
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑加班记录" if edit_mode else "添加加班记录")
        dialog.geometry("400x350")
        dialog.transient(self.root)
        dialog.grab_set()
        
        labels = ["日期", "加班楼层", "加班部门", "加班人员", "预计加班时间", "值班人员", "备注"]
        entries = {}
        
        for i, label in enumerate(labels):
            ttk.Label(dialog, text=label).grid(row=i, column=0, padx=5, pady=5, sticky=tk.W)
            entry = ttk.Entry(dialog, width=30)
            
            if initial_data and label in initial_data:
                entry.insert(0, initial_data[label])
            elif label == "日期":
                entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            elif label == "预计加班时间":
                entry.insert(0, "18:00-20:00")
            
            entry.grid(row=i, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
            entries[label] = entry
        
        def save():
            new_record = {}
            for label in labels:
                new_record[label] = entries[label].get()
            
            if not new_record["日期"] or not new_record["加班人员"]:
                messagebox.showwarning("警告", "请填写日期和加班人员")
                return
            
            if edit_mode and edit_idx is not None:
                for key, value in new_record.items():
                    self.df.at[edit_idx, key] = value
                self.status_bar.config(text=f"已修改记录")
            else:
                self.df = pd.concat([self.df, pd.DataFrame([new_record])], ignore_index=True)
                self.status_bar.config(text=f"已添加记录，共 {len(self.df)} 条")
            
            self.update_tree()
            dialog.destroy()
        
        ttk.Button(dialog, text="保存", command=save).grid(row=7, column=0, padx=5, pady=10)
        ttk.Button(dialog, text="取消", command=dialog.destroy).grid(row=7, column=1, padx=5, pady=10)
    
    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要编辑的记录")
            return
        
        idx = int(selected[0])
        row_data = self.df.iloc[idx].to_dict()
        self.add_record(edit_mode=True, edit_idx=idx, initial_data=row_data)
    
    def import_data(self):
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx"), ("Excel文件", "*.xls")]
        )
        if not file_path:
            return
        
        try:
            imported_df = pd.read_excel(file_path)
            
            required_cols = ["日期", "加班楼层", "加班部门", "加班人员", "预计加班时间", "值班人员"]
            missing_cols = [col for col in required_cols if col not in imported_df.columns]
            
            if missing_cols:
                messagebox.showerror("错误", f"缺少必要列: {', '.join(missing_cols)}")
                return
            
            self.df = pd.concat([self.df, imported_df], ignore_index=True)
            self.update_tree()
            self.status_bar.config(text=f"已导入 {len(imported_df)} 条记录，共 {len(self.df)} 条")
            messagebox.showinfo("成功", f"成功导入 {len(imported_df)} 条记录")
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def export_report(self):
        if self.df.empty:
            messagebox.showwarning("警告", "没有数据可导出")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存加班报表",
            defaultextension=".xlsx",
            filetypes=[("Excel文件", "*.xlsx")]
        )
        
        if not file_path:
            return
        
        try:
            with pd.ExcelWriter(file_path) as writer:
                self.df.to_excel(writer, sheet_name="延时加班统计", index=False)
                
                summary_df = self.df.groupby(["加班部门", "加班楼层"]).size().reset_index(name="加班次数")
                summary_df.to_excel(writer, sheet_name="部门楼层汇总", index=False)
            
            messagebox.showinfo("成功", f"报表已导出至: {file_path}")
            self.status_bar.config(text="报表已导出")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")
    
    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请选择要删除的记录")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的记录吗？"):
            idx = int(selected[0])
            self.df = self.df.drop(idx).reset_index(drop=True)
            self.update_tree()
            self.status_bar.config(text=f"已删除记录，共 {len(self.df)} 条")
    
    def clear_data(self):
        if self.df.empty:
            messagebox.showinfo("提示", "当前没有数据")
            return
        
        if messagebox.askyesno("确认", "确定要清空所有数据吗？"):
            self.df = pd.DataFrame(columns=["日期", "加班楼层", "加班部门", "加班人员", "预计加班时间", "值班人员", "备注"])
            self.update_tree()
            self.status_bar.config(text="数据已清空")
    
    def parse_chat(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("聊天记录解析")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="请粘贴聊天记录:").pack(pady=5)
        
        chat_text = tk.Text(dialog, height=15, width=80)
        chat_text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        def paste():
            try:
                text = dialog.clipboard_get()
                chat_text.insert(tk.INSERT, text)
            except:
                pass
        
        def clear_text():
            chat_text.delete("1.0", tk.END)
        
        chat_menu = tk.Menu(chat_text, tearoff=0)
        chat_menu.add_command(label="粘贴", command=paste)
        chat_menu.add_command(label="清空", command=clear_text)
        
        def show_chat_context_menu(event):
            chat_menu.post(event.x_root, event.y_root)
        
        chat_text.bind("<Button-3>", show_chat_context_menu)
        
        parsed_frame = ttk.Frame(dialog)
        parsed_frame.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        scroll_y = ttk.Scrollbar(parsed_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        parsed_tree = ttk.Treeview(parsed_frame, yscrollcommand=scroll_y.set)
        parsed_tree.pack(expand=True, fill='both')
        scroll_y.config(command=parsed_tree.yview)
        
        parsed_cols = ["日期", "加班楼层", "加班部门", "加班人员", "预计加班时间", "值班人员", "备注"]
        parsed_tree["columns"] = parsed_cols
        parsed_tree["show"] = "headings"
        for col in parsed_cols:
            parsed_tree.heading(col, text=col)
            parsed_tree.column(col, width=100)
        
        parsed_results = []
        
        def parse():
            nonlocal parsed_results
            text = chat_text.get("1.0", tk.END)
            parsed_results = self.extract_overtime_info(text)
            
            for item in parsed_tree.get_children():
                parsed_tree.delete(item)
            
            for idx, result in enumerate(parsed_results):
                parsed_tree.insert("", "end", iid=idx, values=[
                    result["日期"], result["加班楼层"], result["部门"],
                    result["人员"], result["时间"], result["值班"], result["备注"]
                ])
            
            if parsed_results:
                messagebox.showinfo("解析完成", f"共解析出 {len(parsed_results)} 条加班记录")
            else:
                messagebox.showinfo("解析完成", "未找到加班记录")
        
        def add_selected():
            selected = parsed_tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请选择要添加的记录")
                return
            
            for idx in selected:
                result = parsed_results[int(idx)]
                self.df = pd.concat([self.df, pd.DataFrame([{
                    "日期": result["日期"],
                    "加班楼层": result["加班楼层"],
                    "加班部门": result["部门"],
                    "加班人员": result["人员"],
                    "预计加班时间": result["时间"],
                    "值班人员": result["值班"],
                    "备注": result["备注"]
                }])], ignore_index=True)
            
            self.update_tree()
            self.status_bar.config(text=f"已添加 {len(selected)} 条记录，共 {len(self.df)} 条")
            messagebox.showinfo("成功", f"已添加 {len(selected)} 条记录")
        
        def add_all():
            if not parsed_results:
                messagebox.showwarning("警告", "没有可添加的记录")
                return
            
            for result in parsed_results:
                self.df = pd.concat([self.df, pd.DataFrame([{
                    "日期": result["日期"],
                    "加班楼层": result["加班楼层"],
                    "加班部门": result["部门"],
                    "加班人员": result["人员"],
                    "预计加班时间": result["时间"],
                    "值班人员": result["值班"],
                    "备注": result["备注"]
                }])], ignore_index=True)
            
            self.update_tree()
            self.status_bar.config(text=f"已添加 {len(parsed_results)} 条记录，共 {len(self.df)} 条")
            messagebox.showinfo("成功", f"已添加 {len(parsed_results)} 条记录")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="解析", command=parse).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="添加选中", command=add_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="添加全部", command=add_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="关闭", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def extract_overtime_info(self, text):
        results = []
        
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
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
            
            time_range_match = re.search(r'(\d{1,2}):(\d{2})\s*[-至到~]\s*(\d{1,2}):(\d{2})', line)
            if time_range_match:
                time_start = f"{int(time_range_match.group(1)):02d}:{time_range_match.group(2)}"
                time_end = f"{int(time_range_match.group(3)):02d}:{time_range_match.group(4)}"
            
            common_depts = ["个人信贷部", "秩序部", "客服部", "工程部", "保洁部", "安保部", 
                          "行政部", "财务部", "人事部", "维修部", "运维部", "夜班", "白班"]
            for d in common_depts:
                if d in line:
                    if dept:
                        dept += "," + d
                    else:
                        dept = d
            
            name_pattern = re.compile(r'([\u4e00-\u9fa5]{2,4})(?:总|经理|主管|主任|组长)?')
            names = []
            for match in name_pattern.finditer(line):
                name = match.group(1)
                if name not in ["加班", "值班", "预计", "需要", "保持", "确认", "检查", "巡查", "留意"]:
                    names.append(name)
            
            if names:
                person = names[0]
            
            if "需要" in line or "需" in line:
                need_match = re.search(r'(需要|需)\s*(.*?)(?:，|。|！|\s|$)', line)
                if need_match:
                    notes = need_match.group(2).strip()
            
            if "保持" in line:
                keep_match = re.search(r'保持\s*(.*?)(?:，|。|！|\s|$)', line)
                if keep_match:
                    notes = keep_match.group(1).strip()
            
            if "留意" in line:
                note_match = re.search(r'留意\s*(.*?)(?:，|。|！|\s|$)', line)
                if note_match:
                    notes = note_match.group(1).strip()
            
            has_overtime_keyword = any(kw in line for kw in ["加班", "值班", "延时"])
            
            if has_overtime_keyword or floor or dept or person or notes:
                if not person:
                    person = "待确认"
                
                result = {
                    "日期": datetime.now().strftime("%Y-%m-%d"),
                    "加班楼层": floor,
                    "部门": dept,
                    "人员": person.replace("总", "").replace("经理", "").replace("主管", "").strip(),
                    "时间": f"{time_start}-{time_end}",
                    "值班": on_duty,
                    "备注": notes.strip()[:50]
                }
                results.append(result)
        
        return results

if __name__ == "__main__":
    root = tk.Tk()
    app = OvertimeTracker(root)
    root.mainloop()