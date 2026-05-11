# EHS风险隐患排查台账系统 - 部署指南

## 部署方式

### 方式一：Railway（推荐）

1. **登录Railway**
   - 访问 https://railway.app/
   - 使用GitHub账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 选择 "Deploy from GitHub repo"
   - 选择你的项目仓库

3. **配置环境变量**（如需要）
   - PORT: 8000

4. **部署完成**
   - Railway会自动检测项目类型并部署
   - 获取分配的域名即可访问

### 方式二：Vercel

1. **登录Vercel**
   - 访问 https://vercel.com/
   - 使用GitHub账号登录

2. **创建新项目**
   - 点击 "New Project"
   - 导入你的GitHub仓库

3. **配置Build Settings**
   - Framework Preset: Other
   - Build Command: pip install -r requirements.txt
   - Output Directory: (留空)
   - Development Command: python app.py

4. **部署完成**

### 方式三：Heroku

1. **安装Heroku CLI**
   ```bash
   npm install -g heroku
   ```

2. **登录并创建应用**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **部署**
   ```bash
   git push heroku main
   ```

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python app.py

# 访问地址
http://localhost:5001
```

## 项目结构

```
python_project/
├── app.py              # Flask主应用
├── wsgi.py             # WSGI入口
├── Procfile            # Heroku配置
├── railway.toml        # Railway配置
├── requirements.txt    # 依赖列表
├── templates/          # HTML模板
├── risk_ledger.py      # 风险台账核心模块
├── ehs_standards.py    # EHS标准库模块
└── risk_data/          # 风险数据存储
```

## 系统功能

- 📊 仪表盘 - 风险汇总统计
- 📋 风险台账 - 风险管理
- 📚 EHS标准库 - 标准规范查询
- 🔔 通知中心 - 逾期提醒