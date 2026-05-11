import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from meeting_minutes_processor import MeetingMinutesProcessor
from attendance_processor import AttendanceProcessor
from training_records_processor import TrainingRecordsProcessor
from ppt_generator import PPTGenerator

class EHSAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("珠海华润银行大厦 - EHS月度资料自动化系统")
        self.root.geometry("900x600")
        
        self.input_dir = ""
        self.output_dir = ""
        
        self.meeting_processor = MeetingMinutesProcessor()
        self.attendance_processor = AttendanceProcessor()
        self.training_processor = TrainingRecordsProcessor()
        self.ppt_generator = PPTGenerator()
        
        self.processed_data = {
            'meeting_minutes': None,
            'attendance': None,
            'training': None
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=tk.W, pady=10)
        
        title_label = ttk.Label(header_frame, text="EHS月度资料自动化系统", font=('Arial', 16, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        ttk.Label(header_frame, text="珠海华润银行大厦").pack(side=tk.RIGHT, padx=10)
        
        path_frame = ttk.LabelFrame(main_frame, text="工作路径设置", padding="10")
        path_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="输入目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_path_entry = ttk.Entry(path_frame, width=60)
        self.input_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(path_frame, text="浏览", command=self.browse_input_dir).grid(row=0, column=2, padx=5)
        
        ttk.Label(path_frame, text="输出目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_path_entry = ttk.Entry(path_frame, width=60)
        self.output_path_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=5)
        ttk.Button(path_frame, text="浏览", command=self.browse_output_dir).grid(row=1, column=2, padx=5)
        
        tabs = ttk.Notebook(main_frame)
        tabs.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        self.tab1 = ttk.Frame(tabs)
        self.tab2 = ttk.Frame(tabs)
        self.tab3 = ttk.Frame(tabs)
        self.tab4 = ttk.Frame(tabs)
        
        tabs.add(self.tab1, text="会议纪要处理")
        tabs.add(self.tab2, text="签到表统计")
        tabs.add(self.tab3, text="培训记录整理")
        tabs.add(self.tab4, text="月度PPT生成")
        
        self.setup_meeting_tab()
        self.setup_attendance_tab()
        self.setup_training_tab()
        self.setup_ppt_tab()
        
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        self.status_bar = ttk.Label(status_frame, text="就绪", relief=tk.SUNKEN)
        self.status_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        auto_frame = ttk.Frame(main_frame)
        auto_frame.grid(row=4, column=0, sticky=tk.CENTER, pady=10)
        
        ttk.Button(auto_frame, text="一键自动处理全部", command=self.auto_process_all, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(auto_frame, text="生成月度汇报PPT", command=self.generate_monthly_ppt, width=20).pack(side=tk.LEFT, padx=5)
    
    def setup_meeting_tab(self):
        frame = self.tab1
        
        ttk.Label(frame, text="会议纪要自动整理工具").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Button(frame, text="批量处理会议纪要", command=self.process_meeting_minutes).grid(row=1, column=0, pady=5)
        ttk.Button(frame, text="自动归档会议纪要", command=self.archive_meeting_minutes).grid(row=1, column=1, pady=5)
        
        self.meeting_result_text = tk.Text(frame, height=10, width=80)
        self.meeting_result_text.grid(row=2, column=0, columnspan=2, pady=5)
        
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.meeting_result_text.yview)
        scroll_y.grid(row=2, column=2, sticky='ns')
        self.meeting_result_text.configure(yscrollcommand=scroll_y.set)
    
    def setup_attendance_tab(self):
        frame = self.tab2
        
        ttk.Label(frame, text="签到表统计工具").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Button(frame, text="批量处理签到表", command=self.process_attendance).grid(row=1, column=0, pady=5)
        
        self.attendance_result_text = tk.Text(frame, height=10, width=80)
        self.attendance_result_text.grid(row=2, column=0, columnspan=2, pady=5)
        
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.attendance_result_text.yview)
        scroll_y.grid(row=2, column=2, sticky='ns')
        self.attendance_result_text.configure(yscrollcommand=scroll_y.set)
    
    def setup_training_tab(self):
        frame = self.tab3
        
        ttk.Label(frame, text="培训记录整理工具").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Button(frame, text="批量处理培训记录", command=self.process_training).grid(row=1, column=0, pady=5)
        
        self.training_result_text = tk.Text(frame, height=10, width=80)
        self.training_result_text.grid(row=2, column=0, columnspan=2, pady=5)
        
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.training_result_text.yview)
        scroll_y.grid(row=2, column=2, sticky='ns')
        self.training_result_text.configure(yscrollcommand=scroll_y.set)
    
    def setup_ppt_tab(self):
        frame = self.tab4
        
        ttk.Label(frame, text="PPT汇报材料生成").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(frame, text="汇报标题:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ppt_title_entry = ttk.Entry(frame, width=50)
        self.ppt_title_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        self.ppt_title_entry.insert(0, datetime.now().strftime('%Y年%m月') + "月度汇报材料")
        
        ttk.Button(frame, text="生成PPT", command=self.generate_ppt).grid(row=2, column=0, pady=10)
        
        self.ppt_result_text = tk.Text(frame, height=10, width=80)
        self.ppt_result_text.grid(row=3, column=0, columnspan=2, pady=5)
        
        scroll_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.ppt_result_text.yview)
        scroll_y.grid(row=3, column=2, sticky='ns')
        self.ppt_result_text.configure(yscrollcommand=scroll_y.set)
    
    def browse_input_dir(self):
        dir_path = filedialog.askdirectory(title="选择输入目录")
        if dir_path:
            self.input_dir = dir_path
            self.input_path_entry.delete(0, tk.END)
            self.input_path_entry.insert(0, dir_path)
    
    def browse_output_dir(self):
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir = dir_path
            self.output_path_entry.delete(0, tk.END)
            self.output_path_entry.insert(0, dir_path)
    
    def process_meeting_minutes(self):
        if not self.input_dir or not self.output_dir:
            messagebox.showwarning("警告", "请先设置输入和输出目录")
            return
        
        self.meeting_result_text.delete("1.0", tk.END)
        
        try:
            results = self.meeting_processor.batch_process(self.input_dir, self.output_dir)
            
            self.meeting_result_text.insert(tk.END, f"会议纪要处理完成\n")
            self.meeting_result_text.insert(tk.END, f"共处理 {len(results)} 份文件\n\n")
            
            for r in results:
                self.meeting_result_text.insert(tk.END, f"源文件: {r['source']}\n")
                self.meeting_result_text.insert(tk.END, f"输出: {os.path.basename(r['output'])}\n")
                self.meeting_result_text.insert(tk.END, f"参会人数: {r['participants_count']}人\n")
                self.meeting_result_text.insert(tk.END, f"行动项: {r['action_items_count']}项\n\n")
            
            if results:
                self.processed_data['meeting_minutes'] = self.meeting_processor.parse_minutes(
                    os.path.join(self.input_dir, results[0]['source'])
                )
            
            self.status_bar.config(text="会议纪要处理完成")
            messagebox.showinfo("成功", f"成功处理 {len(results)} 份会议纪要")
        
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")
    
    def archive_meeting_minutes(self):
        if not self.input_dir:
            messagebox.showwarning("警告", "请先设置输入目录")
            return
        
        archive_dir = os.path.join(self.input_dir, "归档")
        
        try:
            self.meeting_processor.auto_archive(self.input_dir, archive_dir)
            self.status_bar.config(text="会议纪要归档完成")
            messagebox.showinfo("成功", f"会议纪要已归档至: {archive_dir}")
        except Exception as e:
            messagebox.showerror("错误", f"归档失败: {str(e)}")
    
    def process_attendance(self):
        if not self.input_dir or not self.output_dir:
            messagebox.showwarning("警告", "请先设置输入和输出目录")
            return
        
        self.attendance_result_text.delete("1.0", tk.END)
        
        try:
            results = self.attendance_processor.batch_process(self.input_dir, self.output_dir)
            
            self.attendance_result_text.insert(tk.END, f"签到表处理完成\n")
            self.attendance_result_text.insert(tk.END, f"共处理 {len(results)} 份文件\n\n")
            
            for r in results:
                self.attendance_result_text.insert(tk.END, f"源文件: {r['source']}\n")
                self.attendance_result_text.insert(tk.END, f"输出: {os.path.basename(r['output'])}\n")
                self.attendance_result_text.insert(tk.END, f"应到: {r['total_expected']}人, 实到: {r['total_attended']}人\n")
                self.attendance_result_text.insert(tk.END, f"签到率: {r['rate']:.1f}%\n\n")
            
            if results:
                self.processed_data['attendance'] = self.attendance_processor.parse_excel_attendance(
                    os.path.join(self.input_dir, results[0]['source'])
                )
            
            self.status_bar.config(text="签到表处理完成")
            messagebox.showinfo("成功", f"成功处理 {len(results)} 份签到表")
        
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")
    
    def process_training(self):
        if not self.input_dir or not self.output_dir:
            messagebox.showwarning("警告", "请先设置输入和输出目录")
            return
        
        self.training_result_text.delete("1.0", tk.END)
        
        try:
            results = self.training_processor.batch_process(self.input_dir, self.output_dir)
            
            self.training_result_text.insert(tk.END, f"培训记录处理完成\n")
            self.training_result_text.insert(tk.END, f"共处理 {len(results)} 份文件\n\n")
            
            for r in results:
                self.training_result_text.insert(tk.END, f"源文件: {r['source']}\n")
                self.training_result_text.insert(tk.END, f"输出: {os.path.basename(r['output'])}\n")
                self.training_result_text.insert(tk.END, f"参与人数: {r['participants']}人\n")
                self.training_result_text.insert(tk.END, f"平均评分: {r['avg_score']:.1f}分\n\n")
            
            if results:
                self.processed_data['training'] = self.training_processor.parse_training_record(
                    os.path.join(self.input_dir, results[0]['source'])
                )
            
            self.status_bar.config(text="培训记录处理完成")
            messagebox.showinfo("成功", f"成功处理 {len(results)} 份培训记录")
        
        except Exception as e:
            messagebox.showerror("错误", f"处理失败: {str(e)}")
    
    def generate_ppt(self):
        if not self.output_dir:
            messagebox.showwarning("警告", "请先设置输出目录")
            return
        
        self.ppt_result_text.delete("1.0", tk.END)
        
        try:
            title = self.ppt_title_entry.get()
            output_path = os.path.join(self.output_dir, f"{title}.pptx")
            
            self.ppt_generator.generate_monthly_report(self.processed_data, output_path)
            
            self.ppt_result_text.insert(tk.END, f"PPT生成成功\n")
            self.ppt_result_text.insert(tk.END, f"文件路径: {output_path}\n")
            self.ppt_result_text.insert(tk.END, f"\n包含内容:\n")
            
            if self.processed_data.get('meeting_minutes'):
                self.ppt_result_text.insert(tk.END, "● 会议纪要\n")
            if self.processed_data.get('attendance'):
                self.ppt_result_text.insert(tk.END, "● 签到统计\n")
            if self.processed_data.get('training'):
                self.ppt_result_text.insert(tk.END, "● 培训报告\n")
            
            self.status_bar.config(text="PPT生成完成")
            messagebox.showinfo("成功", f"PPT已生成至: {output_path}")
        
        except Exception as e:
            messagebox.showerror("错误", f"生成失败: {str(e)}")
    
    def auto_process_all(self):
        if not self.input_dir or not self.output_dir:
            messagebox.showwarning("警告", "请先设置输入和输出目录")
            return
        
        try:
            self.status_bar.config(text="正在处理会议纪要...")
            self.root.update()
            self.process_meeting_minutes()
            
            self.status_bar.config(text="正在处理签到表...")
            self.root.update()
            self.process_attendance()
            
            self.status_bar.config(text="正在处理培训记录...")
            self.root.update()
            self.process_training()
            
            self.status_bar.config(text="一键处理完成")
            messagebox.showinfo("成功", "所有资料已处理完成！")
        
        except Exception as e:
            messagebox.showerror("错误", f"一键处理失败: {str(e)}")
    
    def generate_monthly_ppt(self):
        if not self.output_dir:
            messagebox.showwarning("警告", "请先设置输出目录")
            return
        
        auto_data = {}
        
        try:
            for filename in os.listdir(self.input_dir):
                filepath = os.path.join(self.input_dir, filename)
                
                if '会议纪要' in filename and (filename.endswith('.docx') or filename.endswith('.txt')):
                    auto_data['meeting_minutes'] = self.meeting_processor.parse_minutes(filepath)
                
                elif '签到' in filename and (filename.endswith('.xlsx') or filename.endswith('.xls')):
                    auto_data['attendance'] = self.attendance_processor.parse_excel_attendance(filepath)
                
                elif '培训' in filename and (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.docx')):
                    auto_data['training'] = self.training_processor.parse_training_record(filepath)
            
            month = datetime.now().strftime('%Y年%m月')
            output_path = os.path.join(self.output_dir, f"{month}月度汇报材料.pptx")
            
            self.ppt_generator.generate_monthly_report(auto_data, output_path)
            
            self.status_bar.config(text="月度PPT生成完成")
            messagebox.showinfo("成功", f"月度汇报PPT已生成至: {output_path}")
        
        except Exception as e:
            messagebox.showerror("错误", f"生成失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EHSAutomationApp(root)
    root.mainloop()