
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import pandas as pd
import os
from datetime import datetime

class RepairRecordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("报事报修记录系统")
        self.root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
        self.root.resizable(True, True)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.style.configure('Header.TLabel', font=('微软雅黑', 14, 'bold'), foreground='#1F4E79')
        self.style.configure('Title.TLabel', font=('微软雅黑', 18, 'bold'), foreground='#1F4E79')
        self.style.configure('Button.TButton', font=('微软雅黑', 10), background='#4A90D9', foreground='white')
        self.style.map('Button.TButton', background=[('active', '#3A7BC8')])
        self.style.configure('Treeview', font=('微软雅黑', 10), rowheight=25)
        self.style.configure('Treeview.Heading', font=('微软雅黑', 11, 'bold'), background='#E8F4FC', foreground='#1F4E79')
        
        self.data_file = "repair_records.xlsx"
        self.df = self.load_data()
        
        self.create_widgets()
    
    def load_data(self):
        if os.path.exists(self.data_file):
            return pd.read_excel(self.data_file)
        else:
            return pd.DataFrame({
                "序号": [],
                "报修人": [],
                "部门": [],
                "报修事项": [],
                "地点": [],
                "报修日期": [],
                "完成状态": [],
                "完成情况": []
            })
    
    def save_data(self):
        self.df.to_excel(self.data_file, index=False)
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        title_label = ttk.Label(title_frame, text="🏢 报事报修记录系统", style='Title.TLabel')
        title_label.pack(anchor=tk.CENTER)
        
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        self.add_frame = ttk.Frame(notebook, padding="20")
        self.list_frame = ttk.Frame(notebook, padding="10")
        self.stats_frame = ttk.Frame(notebook, padding="20")
        
        notebook.add(self.add_frame, text="📝 新增报修")
        notebook.add(self.list_frame, text="📋 报修列表")
        notebook.add(self.stats_frame, text="📊 统计分析")
        
        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        import_btn = ttk.Button(toolbar, text="📥 导入数据", command=self.import_data, style='Button.TButton')
        import_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = ttk.Button(toolbar, text="📤 导出数据", command=self.export_data, style='Button.TButton')
        export_btn.pack(side=tk.LEFT, padx=5)
        
        self.create_add_tab()
        self.create_list_tab()
        self.create_stats_tab()
    
    def create_add_tab(self):
        center_frame = ttk.Frame(self.add_frame)
        center_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        header_label = ttk.Label(center_frame, text="新增报修记录", style='Header.TLabel')
        header_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        fields = [
            ("报修人", "entry"),
            ("部门", "combobox", ["润创港湾", "华润银行大厦", "楼层内服", "食堂", "其他"]),
            ("报修事项", "entry"),
            ("地点", "entry"),
            ("完成情况", "text")
        ]
        
        self.entries = {}
        row = 1
        
        for label_text, field_type, *options in fields:
            ttk.Label(center_frame, text=label_text + "：", font=('微软雅黑', 11)).grid(row=row, column=0, sticky=tk.E, pady=8, padx=10)
            if field_type == "entry":
                entry = ttk.Entry(center_frame, width=45, font=('微软雅黑', 11))
                entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=8)
                self.entries[label_text] = entry
            elif field_type == "combobox":
                combo = ttk.Combobox(center_frame, values=options[0], width=42, font=('微软雅黑', 11))
                combo.current(0)
                combo.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=8)
                self.entries[label_text] = combo
            elif field_type == "text":
                text = tk.Text(center_frame, width=45, height=4, font=('微软雅黑', 11))
                text.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=8)
                self.entries[label_text] = text
            row += 1
        
        button_frame = ttk.Frame(center_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        submit_btn = ttk.Button(button_frame, text="提交报修", command=self.add_record, style='Button.TButton', width=15)
        submit_btn.pack(side=tk.LEFT, padx=10)
        
        reset_btn = ttk.Button(button_frame, text="重置", command=self.reset_form, width=15)
        reset_btn.pack(side=tk.LEFT, padx=10)
    
    def reset_form(self):
        for key in self.entries:
            if isinstance(self.entries[key], tk.Text):
                self.entries[key].delete("1.0", tk.END)
            else:
                self.entries[key].delete(0, tk.END)
                if key == "部门":
                    self.entries[key].current(0)
    
    def add_record(self):
        try:
            new_id = len(self.df) + 1
            today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            record = {
                "序号": new_id,
                "报修人": self.entries["报修人"].get().strip(),
                "部门": self.entries["部门"].get(),
                "报修事项": self.entries["报修事项"].get().strip(),
                "地点": self.entries["地点"].get().strip(),
                "报修日期": today,
                "完成状态": "未整改",
                "完成情况": self.entries["完成情况"].get("1.0", tk.END).strip()
            }
            
            if not record["报修人"] or not record["报修事项"]:
                messagebox.showwarning("警告", "请填写报修人和报修事项！")
                return
            
            self.df = pd.concat([self.df, pd.DataFrame([record])], ignore_index=True)
            self.save_data()
            messagebox.showinfo("成功", "报修记录已添加！")
            self.reset_form()
            self.refresh_list()
            self.refresh_stats()
            
        except Exception as e:
            messagebox.showerror("错误", "添加失败：" + str(e))
    
    def create_list_tab(self):
        filter_frame = ttk.Frame(self.list_frame, padding="5")
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(filter_frame, text="部门：", font=('微软雅黑', 10)).pack(side=tk.LEFT, padx=2)
        self.dept_filter = ttk.Combobox(filter_frame, values=["全部", "润创港湾", "华润银行大厦", "楼层内服", "食堂", "其他"], width=15, font=('微软雅黑', 10))
        self.dept_filter.current(0)
        self.dept_filter.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(filter_frame, text="状态：", font=('微软雅黑', 10)).pack(side=tk.LEFT, padx=2)
        self.status_filter = ttk.Combobox(filter_frame, values=["全部", "已整改", "未整改"], width=10, font=('微软雅黑', 10))
        self.status_filter.current(0)
        self.status_filter.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(filter_frame, text="报修人：", font=('微软雅黑', 10)).pack(side=tk.LEFT, padx=2)
        self.person_filter = ttk.Entry(filter_frame, width=15, font=('微软雅黑', 10))
        self.person_filter.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(filter_frame, text="关键词：", font=('微软雅黑', 10)).pack(side=tk.LEFT, padx=2)
        self.keyword_filter = ttk.Entry(filter_frame, width=20, font=('微软雅黑', 10))
        self.keyword_filter.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(filter_frame, text="筛选", command=self.refresh_list, style='Button.TButton', width=6).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="重置", command=self.reset_filter, width=6).pack(side=tk.LEFT, padx=2)
        
        sort_frame = ttk.Frame(self.list_frame, padding="5")
        sort_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(sort_frame, text="排序：", font=('微软雅黑', 10)).pack(side=tk.LEFT, padx=2)
        self.sort_column = ttk.Combobox(sort_frame, values=["序号", "报修日期", "报修人", "部门"], width=10, font=('微软雅黑', 10))
        self.sort_column.current(0)
        self.sort_column.pack(side=tk.LEFT, padx=2)
        
        self.sort_order = ttk.Combobox(sort_frame, values=["升序", "降序"], width=6, font=('微软雅黑', 10))
        self.sort_order.current(1)
        self.sort_order.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(sort_frame, text="排序", command=self.refresh_list, style='Button.TButton', width=6).pack(side=tk.LEFT, padx=5)
        
        self.tree = ttk.Treeview(self.list_frame, columns=("序号", "报修人", "部门", "报修事项", "地点", "报修日期", "完成状态", "完成情况"), show="headings")
        
        columns = ["序号", "报修人", "部门", "报修事项", "地点", "报修日期", "完成状态", "完成情况"]
        weights = [1, 2, 2, 4, 2, 3, 2, 3]
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.on_column_click(c))
        
        for col, weight in zip(columns, weights):
            self.tree.column(col, stretch=True, anchor=tk.CENTER, minwidth=50)
        
        self.tree.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.list_frame.rowconfigure(2, weight=1)
        self.list_frame.columnconfigure(0, weight=1)
        
        self.list_frame.bind('<Configure>', self.on_frame_resize)
        
        scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(self.list_frame)
        button_frame.grid(row=3, column=0, pady=10)
        
        complete_btn = ttk.Button(button_frame, text="✅ 标记已整改", command=self.mark_completed, style='Button.TButton', width=12)
        complete_btn.pack(side=tk.LEFT, padx=8)
        
        self.current_sort_col = "序号"
        self.current_sort_asc = False
        
        edit_btn = ttk.Button(button_frame, text="🖊️ 编辑记录", command=self.edit_record, width=12)
        edit_btn.pack(side=tk.LEFT, padx=8)
        
        delete_btn = ttk.Button(button_frame, text="🗑️ 删除记录", command=self.delete_record, width=12)
        delete_btn.pack(side=tk.LEFT, padx=8)
        
        self.refresh_list()
    
    def on_frame_resize(self, event):
        total_width = event.width - 40
        weights = [1, 2, 2, 4, 2, 3, 2, 3]
        total_weight = sum(weights)
        
        columns = ["序号", "报修人", "部门", "报修事项", "地点", "报修日期", "完成状态", "完成情况"]
        for col, weight in zip(columns, weights):
            self.tree.column(col, width=int(total_width * weight / total_weight))
    
    def reset_filter(self):
        self.dept_filter.current(0)
        self.status_filter.current(0)
        self.person_filter.delete(0, tk.END)
        self.keyword_filter.delete(0, tk.END)
        self.sort_column.current(0)
        self.sort_order.current(1)
        self.refresh_list()
    
    def on_column_click(self, col):
        if self.current_sort_col == col:
            self.current_sort_asc = not self.current_sort_asc
        else:
            self.current_sort_col = col
            self.current_sort_asc = False
        
        self.sort_column.set(col)
        self.sort_order.set("升序" if self.current_sort_asc else "降序")
        self.refresh_list()
    
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        dept_filter = self.dept_filter.get() if hasattr(self, 'dept_filter') else "全部"
        status_filter = self.status_filter.get() if hasattr(self, 'status_filter') else "全部"
        person_filter = self.person_filter.get().strip() if hasattr(self, 'person_filter') else ""
        keyword_filter = self.keyword_filter.get().strip() if hasattr(self, 'keyword_filter') else ""
        sort_col = self.sort_column.get() if hasattr(self, 'sort_column') else "序号"
        sort_asc = self.sort_order.get() == "升序" if hasattr(self, 'sort_order') else False
        
        filtered_df = self.df.copy()
        
        if dept_filter != "全部":
            filtered_df = filtered_df[filtered_df["部门"] == dept_filter]
        
        if status_filter != "全部":
            filtered_df = filtered_df[filtered_df["完成状态"] == status_filter]
        
        if person_filter:
            filtered_df = filtered_df[filtered_df["报修人"].str.contains(person_filter, na=False)]
        
        if keyword_filter:
            filtered_df = filtered_df[
                filtered_df["报修事项"].str.contains(keyword_filter, na=False) |
                filtered_df["地点"].str.contains(keyword_filter, na=False) |
                filtered_df["完成情况"].str.contains(keyword_filter, na=False)
            ]
        
        if sort_col in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=sort_asc)
        
        for _, row in filtered_df.iterrows():
            values = [
                int(row["序号"]),
                str(row["报修人"]).strip() if pd.notna(row["报修人"]) else "",
                str(row["部门"]).strip() if pd.notna(row["部门"]) else "",
                str(row["报修事项"]).strip() if pd.notna(row["报修事项"]) else "",
                str(row["地点"]).strip() if pd.notna(row["地点"]) else "",
                str(row["报修日期"]).strip() if pd.notna(row["报修日期"]) else "",
                str(row["完成状态"]).strip() if pd.notna(row["完成状态"]) else "",
                str(row["完成情况"]).strip() if pd.notna(row["完成情况"]) else ""
            ]
            item = self.tree.insert("", tk.END, values=values)
            
            if row["完成状态"] == "已整改":
                self.tree.item(item, tags=("completed",))
            else:
                self.tree.item(item, tags=("pending",))
        
        self.tree.tag_configure("completed", foreground="#2ECC71")
        self.tree.tag_configure("pending", foreground="#E74C3C")
    
    def mark_completed(self):
        try:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择一条记录！")
                return
            
            item = selected[0]
            values = self.tree.item(item, "values")
            record_id = values[0]
            
            mask = self.df["序号"] == record_id
            if not mask.any():
                messagebox.showerror("错误", "记录不存在！")
                return
            
            self.df.loc[mask, "完成状态"] = "已整改"
            self.save_data()
            self.df = self.load_data()
            self.refresh_list()
            self.refresh_stats()
            messagebox.showinfo("成功", "已标记为已整改！")
            
        except Exception as e:
            messagebox.showerror("错误", "操作失败：" + str(e))
    
    def edit_record(self):
        try:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择一条记录！")
                return
            
            item = selected[0]
            values = self.tree.item(item, "values")
            record_id = values[0]
            
            edit_window = tk.Toplevel(self.root)
            edit_window.title("编辑记录")
            edit_window.geometry("500x400")
            edit_window.resizable(False, False)
            
            ttk.Label(edit_window, text="报修人：", font=('微软雅黑', 10)).grid(row=0, column=0, padx=10, pady=8, sticky=tk.W)
            person_entry = ttk.Entry(edit_window, width=30, font=('微软雅黑', 10))
            person_entry.insert(0, values[1])
            person_entry.grid(row=0, column=1, padx=10, pady=8)
            
            ttk.Label(edit_window, text="部门：", font=('微软雅黑', 10)).grid(row=1, column=0, padx=10, pady=8, sticky=tk.W)
            dept_combo = ttk.Combobox(edit_window, values=["润创港湾", "华润银行大厦", "楼层内服", "食堂", "其他"], width=28, font=('微软雅黑', 10))
            dept_combo.set(values[2])
            dept_combo.grid(row=1, column=1, padx=10, pady=8)
            
            ttk.Label(edit_window, text="报修事项：", font=('微软雅黑', 10)).grid(row=2, column=0, padx=10, pady=8, sticky=tk.W)
            item_entry = ttk.Entry(edit_window, width=30, font=('微软雅黑', 10))
            item_entry.insert(0, values[3])
            item_entry.grid(row=2, column=1, padx=10, pady=8)
            
            ttk.Label(edit_window, text="地点：", font=('微软雅黑', 10)).grid(row=3, column=0, padx=10, pady=8, sticky=tk.W)
            location_entry = ttk.Entry(edit_window, width=30, font=('微软雅黑', 10))
            location_entry.insert(0, values[4])
            location_entry.grid(row=3, column=1, padx=10, pady=8)
            
            ttk.Label(edit_window, text="报修日期：", font=('微软雅黑', 10)).grid(row=4, column=0, padx=10, pady=8, sticky=tk.W)
            date_entry = ttk.Entry(edit_window, width=30, font=('微软雅黑', 10))
            date_entry.insert(0, values[5])
            date_entry.grid(row=4, column=1, padx=10, pady=8)
            
            ttk.Label(edit_window, text="完成状态：", font=('微软雅黑', 10)).grid(row=5, column=0, padx=10, pady=8, sticky=tk.W)
            status_combo = ttk.Combobox(edit_window, values=["已整改", "未整改"], width=28, font=('微软雅黑', 10))
            status_combo.set(values[6])
            status_combo.grid(row=5, column=1, padx=10, pady=8)
            
            ttk.Label(edit_window, text="完成情况：", font=('微软雅黑', 10)).grid(row=6, column=0, padx=10, pady=8, sticky=tk.W)
            note_entry = ttk.Entry(edit_window, width=30, font=('微软雅黑', 10))
            note_entry.insert(0, values[7])
            note_entry.grid(row=6, column=1, padx=10, pady=8)
            
            def save_changes():
                mask = self.df["序号"] == record_id
                self.df.loc[mask, "报修人"] = person_entry.get().strip()
                self.df.loc[mask, "部门"] = dept_combo.get()
                self.df.loc[mask, "报修事项"] = item_entry.get().strip()
                self.df.loc[mask, "地点"] = location_entry.get().strip()
                self.df.loc[mask, "报修日期"] = date_entry.get().strip()
                self.df.loc[mask, "完成状态"] = status_combo.get()
                self.df.loc[mask, "完成情况"] = note_entry.get().strip()
                self.save_data()
                self.df = self.load_data()
                self.refresh_list()
                self.refresh_stats()
                edit_window.destroy()
                messagebox.showinfo("成功", "记录已更新！")
            
            button_frame = ttk.Frame(edit_window)
            button_frame.grid(row=7, column=0, columnspan=2, pady=20)
            ttk.Button(button_frame, text="确定", command=save_changes, style='Button.TButton', width=10).pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="取消", command=edit_window.destroy, width=10).pack(side=tk.LEFT, padx=10)
            
            edit_window.grab_set()
            
        except Exception as e:
            messagebox.showerror("错误", "操作失败：" + str(e))
    
    def delete_record(self):
        try:
            selected = self.tree.selection()
            if not selected:
                messagebox.showwarning("警告", "请先选择一条记录！")
                return
            
            if not messagebox.askyesno("确认删除", "确定要删除这条记录吗？"):
                return
            
            item = selected[0]
            values = self.tree.item(item, "values")
            record_id = values[0]
            
            self.df = self.df[self.df["序号"] != record_id]
            self.df["序号"] = range(1, len(self.df) + 1)
            self.save_data()
            self.df = self.load_data()
            self.refresh_list()
            self.refresh_stats()
            messagebox.showinfo("成功", "记录已删除！")
            
        except Exception as e:
            messagebox.showerror("错误", "操作失败：" + str(e))
    
    def create_stats_tab(self):
        header_label = ttk.Label(self.stats_frame, text="统计分析报告", style='Header.TLabel')
        header_label.pack(anchor=tk.CENTER, pady=10)
        
        stats_container = ttk.Frame(self.stats_frame)
        stats_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        stats_container.columnconfigure(0, weight=1)
        stats_container.rowconfigure(0, weight=1)
        
        self.stats_text = tk.Text(stats_container, width=90, height=30, font=('微软雅黑', 11), bg='#F8FAFC', relief=tk.FLAT)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(stats_container, orient=tk.VERTICAL, command=self.stats_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        ttk.Button(self.stats_frame, text="🔄 刷新统计", command=self.refresh_stats, style='Button.TButton').pack(pady=10)
        
        self.refresh_stats()
    
    def refresh_stats(self):
        self.stats_text.delete("1.0", tk.END)
        
        total = len(self.df)
        if total == 0:
            self.stats_text.insert("1.0", "暂无数据，请先添加报修记录！")
            self.stats_text.config(state=tk.DISABLED)
            return
        
        completed = len(self.df[self.df["完成状态"] == "已整改"])
        pending = len(self.df[self.df["完成状态"] == "未整改"])
        
        comp_rate = completed / total * 100
        pend_rate = pending / total * 100
        
        stats = "=" * 70 + "\n"
        stats += "                报事报修统计报告\n"
        stats += "=" * 70 + "\n\n"
        
        stats += "【数据概览】\n"
        stats += "-" * 40 + "\n"
        stats += f"总记录数：{total} 条\n"
        stats += f"已整改：{completed} 条 ({comp_rate:.1f}%)\n"
        stats += f"未整改：{pending} 条 ({pend_rate:.1f}%)\n\n"
        
        stats += "【各部门统计】\n"
        stats += "-" * 40 + "\n"
        
        dept_stats = self.df.groupby("部门")["完成状态"].value_counts().unstack(fill_value=0)
        for dept in dept_stats.index:
            dept_completed = dept_stats.loc[dept].get("已整改", 0)
            dept_pending = dept_stats.loc[dept].get("未整改", 0)
            dept_total = dept_completed + dept_pending
            rate = (dept_completed/dept_total*100) if dept_total > 0 else 0
            stats += f"• {dept}：\n"
            stats += f"   ├─ 已整改：{dept_completed} 条\n"
            stats += f"   ├─ 未整改：{dept_pending} 条\n"
            stats += f"   └─ 整改率：{rate:.1f}%\n\n"
        
        stats += "【最近7天新增】\n"
        stats += "-" * 40 + "\n"
        
        seven_days_ago = datetime.now() - pd.Timedelta(days=7)
        recent = self.df[self.df["报修日期"] >= seven_days_ago.strftime("%Y-%m-%d")]
        recent_completed = len(recent[recent["完成状态"] == "已整改"])
        recent_pending = len(recent[recent["完成状态"] == "未整改"])
        
        stats += f"最近7天新增：{len(recent)} 条\n"
        stats += f"其中已整改：{recent_completed} 条\n"
        stats += f"其中未整改：{recent_pending} 条\n\n"
        
        stats += "=" * 70 + "\n"
        stats += f"生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n"
        stats += "=" * 70
        
        self.stats_text.insert("1.0", stats)
        self.stats_text.config(state=tk.DISABLED)
    
    def import_data(self):
        try:
            file_path = simpledialog.askstring("导入数据", "请输入要导入的Excel文件路径（如：C:\\data\\records.xlsx）：")
            if not file_path:
                return
            
            if not os.path.exists(file_path):
                messagebox.showerror("错误", "文件不存在！")
                return
            
            imported_df = pd.read_excel(file_path)
            
            required_cols = ["序号", "报修人", "部门", "报修事项", "地点", "报修日期", "完成状态", "完成情况"]
            if not all(col in imported_df.columns for col in required_cols):
                messagebox.showerror("错误", "文件格式不正确！请确保包含所有必需列。")
                return
            
            self.df = imported_df
            self.save_data()
            self.refresh_list()
            self.refresh_stats()
            messagebox.showinfo("成功", f"已成功导入 {len(imported_df)} 条记录！")
            
        except Exception as e:
            messagebox.showerror("错误", "导入失败：" + str(e))
    
    def export_data(self):
        try:
            file_path = simpledialog.askstring("导出数据", "请输入导出文件路径（如：C:\\data\\export.xlsx）：")
            if not file_path:
                return
            
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            
            self.df.to_excel(file_path, index=False)
            messagebox.showinfo("成功", f"已成功导出到 {file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", "导出失败：" + str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = RepairRecordApp(root)
    root.mainloop()
