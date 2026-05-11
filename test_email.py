import os
import smtplib
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate

def send_email_with_attachment():
    subject = '珠海华润银行风险监测报告'
    content = '''【珠海华润银行总行大厦风险监测报告】

监测位置：珠海市高新区金业南路
更新时间：2026年04月29日

当前风险：安全 - 6.6/100
预测风险：安全 - 11.1/100

分项风险：
天气风险：0/25 | 雷阵中雨
舆情风险：13/30 | 正面情感
治安风险：9/30 | 良好
交通风险：0/15 | 畅通

预警提示：未来12小时有强降水

详见附件PDF报告。
'''

    msg = MIMEMultipart()
    msg['From'] = '3666488010@qq.com'
    msg['To'] = '3666488010@qq.com'
    msg['Subject'] = subject
    msg['Date'] = formatdate(localtime=True)

    msg.attach(MIMEText(content, 'plain', 'utf-8'))

    pdf_path = r'C:\Users\lenovo\Desktop\张浚宁桌面文件\python_project\risk_reports\latest_report.pdf'
    
    if os.path.exists(pdf_path):
        print(f'找到PDF文件: {pdf_path}')
        print(f'文件大小: {os.path.getsize(pdf_path)} 字节')
        
        with open(pdf_path, 'rb') as f:
            pdf_data = f.read()
        
        part = MIMEBase('application', 'pdf')
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=('utf-8', '', '风险监测报告.pdf'))
        part.add_header('Content-Transfer-Encoding', 'base64')
        msg.attach(part)
        print('PDF附件已添加')
    else:
        print('未找到PDF文件')
        return False

    try:
        server = smtplib.SMTP('smtp.qq.com', 587, timeout=30)
        server.set_debuglevel(1)
        server.starttls()
        server.login('3666488010@qq.com', 'pdrbyjvhpwxmdbih')
        server.sendmail('3666488010@qq.com', '3666488010@qq.com', msg.as_string())
        server.quit()
        print('邮件发送成功！')
        return True
    except Exception as e:
        print(f'发送失败: {str(e)}')
        return False

if __name__ == '__main__':
    send_email_with_attachment()
