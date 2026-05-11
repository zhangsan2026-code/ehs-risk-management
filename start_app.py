import subprocess
import platform
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    local_ip = get_local_ip()
    
    print("=" * 50)
    print("珠海华润银行大厦延时加班统计表")
    print("=" * 50)
    print("本地地址: http://127.0.0.1:5001")
    print("局域网地址: http://%s:5001" % local_ip)
    print("")
    print("使用说明:")
    print("  1. 在浏览器中打开上述地址")
    print("  2. 点击'添加记录'添加加班信息")
    print("  3. 点击'聊天解析'粘贴聊天记录自动解析")
    print("  4. 点击'导出报表'下载Excel文件")
    print("")
    print("如需外网访问:")
    print("  1. 下载 ngrok: https://ngrok.com/download")
    print("  2. 运行: ngrok http 5001")
    print("  3. 将生成的 https 地址分享给同事")
    print("=" * 50)
    print("")
    
    app_script = "app.py"
    
    if platform.system() == "Windows":
        subprocess.run(["python", app_script], shell=True)
    else:
        subprocess.run(["python", app_script])

if __name__ == "__main__":
    main()