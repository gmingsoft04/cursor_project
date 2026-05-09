# 外贸客户开发系统（手机快充头 / 快充线）

> 1 人公司专用：通过开源/商业 API 搜索潜在客户邮箱、本地数据库储存、内置开发信模板、批量发送（自动跳过已退订客户）、合规一键退订。

## ✨ 主要功能

- **关键字 / 域名搜索潜在客户邮箱**
  - 支持 [Hunter.io](https://hunter.io/api)（按域名 / 公司）
  - 支持 [SerpAPI](https://serpapi.com/) + Hunter.io 联用（关键字 → 公司域名 → 邮箱）
  - 内置 **演示模式**：未配置 API key 时也能完整体验流程
- **本地客户管理**：增删改查、按邮箱/姓名/公司/国家筛选、批量退订/删除、导入去重
- **开发信模板**：内置 4 套（GaN 快充推荐、Type-C 线推荐、7 天跟进、节日问候），支持 Jinja 占位符 `{{first_name}}`、`{{company}}`、`{{country}}` 等
- **群发开发信**
  - 选择「全部可发送客户」或「自行勾选」
  - 渲染预览（HTML 和纯文本均可）
  - SMTP 发送（含节流间隔，防止被反垃圾系统识别）
  - **自动跳过已退订客户**，并在每封邮件中注入唯一签名的退订链接
- **合规退订**：每封邮件都带签名 token 的退订链接，客户点击即可写入数据库；支持中英文展示页

## 🧱 技术栈

| 端     | 技术                                                                |
| ------ | ------------------------------------------------------------------- |
| 后端   | Python 3.10+ · FastAPI · SQLAlchemy 2 · SQLite · Jinja2 · httpx · itsdangerous |
| 前端   | Vue 3 · Vite · Element Plus · Pinia · Vue Router · Axios            |
| 邮件   | 标准库 `smtplib`（兼容 Gmail / 163 / QQ / 自建邮箱）                  |

## 📁 目录结构

```
.
├── backend/
│   ├── app/
│   │   ├── routers/        # customers / templates / search / campaigns / unsubscribe / settings
│   │   ├── services/       # email_search.py / mailer.py / tokens.py
│   │   ├── models.py       # SQLAlchemy 模型
│   │   ├── schemas.py      # Pydantic
│   │   ├── seed.py         # 内置开发信模板
│   │   ├── config.py       # .env 配置
│   │   ├── database.py
│   │   └── main.py
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
└── frontend/
    ├── src/
    │   ├── views/          # Dashboard / Search / Customers / Templates / Campaigns / Settings
    │   ├── api/            # axios 客户端
    │   ├── router/
    │   ├── App.vue
    │   └── main.js
    ├── vite.config.js
    └── package.json
```

## 🚀 快速开始

### 1. 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # 编辑 .env 写入 SMTP / API key
python run.py                 # http://127.0.0.1:8000
```

后端启动后会自动：

- 在 `backend/data/app.db` 创建 SQLite 数据库
- 写入内置 4 套开发信模板
- 暴露 `/api/...` 与 `/unsubscribe`、`/api/health`、`/docs`（Swagger）

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev                   # http://127.0.0.1:5173 （默认代理后端 8000）
```

### 3. 生产部署（可选）

```bash
cd frontend && npm run build
# 后端会自动挂载 frontend/dist 静态资源
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## ⚙️ 配置说明（`backend/.env`）

```ini
APP_BASE_URL=https://your-domain.com   # 公网可访问的退订链接域名
SECRET_KEY=please-change-me            # 退订 token 签名密钥

# 搜索 API（任填一个，未配置时自动回退到演示模式）
HUNTER_API_KEY=                         # https://hunter.io/api
SERPAPI_KEY=                            # https://serpapi.com
SEARCH_PROVIDERS=hunter,serpapi,demo

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@example.com
SMTP_PASSWORD=app-password
SMTP_USE_TLS=true
SMTP_FROM_NAME=Your Name
SMTP_FROM_EMAIL=your@example.com
SEND_BATCH_INTERVAL=2                   # 单封邮件之间的间隔（秒），用于反垃圾节流
```

> Gmail 请使用「应用专用密码」；QQ / 163 请使用「授权码」。
>
> 强烈建议在自己的发件域名上配置 SPF / DKIM / DMARC，提高送达率，避免落入垃圾箱。

## 🔁 工作流

1. **客户搜索**：输入关键字（例：`phone charger importer USA`）或域名 → 选择需要的客户 → 「保存所选」入库
2. **客户管理**：补充客户备注、关键字标签；可手动添加；批量标记退订/删除
3. **开发信模板**：在 4 套内置话术上修改或新增
4. **群发开发信**：选择模板和收件方式（全部 / 勾选）→ 预览渲染 → 一键群发；已退订客户自动跳过
5. **客户主动退订**：邮件底部带签名退订链接，客户点击即写入数据库，下次群发自动排除

## 🔐 合规要点

- 每封邮件都包含可点击的退订链接（带 itsdangerous 签名 token，无法伪造）
- 邮件 Header / 正文中可加 `List-Unsubscribe`，本系统已强制注入正文链接
- 数据库以邮箱唯一键去重；保存时不会覆盖已存在客户
- SMTP 发送有可配置的间隔（默认 2 秒），降低被反垃圾系统识别的概率

## 🧪 演示模式

未配置 `HUNTER_API_KEY` / `SERPAPI_KEY` 时，搜索接口将返回标记为 `source=demo` 的样例数据，邮箱后缀为 `.example`，仅用于体验流程，请勿真实发送。

## 📜 许可

本项目仅供学习与个人外贸使用，请遵守目标客户所在地的反垃圾邮件法规（CAN-SPAM、GDPR、PIPL 等）。
