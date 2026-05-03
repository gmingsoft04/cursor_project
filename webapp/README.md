# 欧美快充客户采集工具 · Charger Leads Toolkit

一个**纯前端单页应用**（HTML + CSS + Vanilla JS），专为中国快充头 / 快充线 /
GaN 充电器 / USB-C 数据线批发商打造，覆盖找客户从"关键词→平台→跟进→开发信"
的整条链路。

> 100% 本地运行，无后端、无 API key。所有数据保存在浏览器 localStorage。

## 5 个功能模块

### 1. 🔍 搜索关键词（48 个分类）
- 6 大类共 48 个关键词：买家搜索词、采购角色（LinkedIn）、北美定向、欧洲定向、销售渠道、外贸/海关
- **点击即复制**到剪贴板，粘贴到 Google / LinkedIn / Apollo / DuckDuckGo 即用
- 8 条 Google Dork 高级语法，**点击直接打开 Google 搜索结果**

### 2. 🌐 8 个推荐获客平台
- **Apollo.io**（首选）— 行业 + 国家筛选，免费档每月 60 邮箱
- **ImportGenius / Panjiva**（高精准）— 美国海关进口数据，找近 6 个月真实买家
- **Hunter.io**（必备）— 域名 → 邮箱
- **LinkedIn Sales Navigator**、**Alibaba RFQ**、**Global Sources**、**Europages / Kompass**
- 每个平台都附"使用要点"清单

### 3. 📇 客户追踪（本地 CRM）
- 增删改查 + 6 种状态（新增 / 已发开发信 / 已回复 / 谈判中 / 成交 / 流失）
- 实时按公司 / 邮箱 / 国家过滤
- **CSV 导入 / 导出**（兼容父目录 `lead_finder` Python 工具的 CSV 格式）
- 顶部 dashboard：总数 / 各阶段计数

### 4. ✉️ 开发信模板（3 种风格）
- ① **正式商务**（Formal）— 完整 introduction，适合首次冷邮件
- ② **简洁直接**（Concise）— 5 行短邮件，适合二次跟进
- ③ **产品介绍**（Product Pitch）— 突出产品参数 + CTA，适合已知品类需求的买家
- 实时预览，所有发件人信息自动持久化
- 含 CAN-SPAM / GDPR 合规要求的"来源说明 + 退订选项"

### 5. 🤖 AI 生成客户开发策略
- 输入：目标国家 × 客户类型 × 订单规模
- 输出：买家画像 / 必备认证 / 付款方式 / 主流热销 SKU
  + 推荐平台组合 + 推荐关键词 + **4 周行动计划**
- 离线规则化推理（基于内置知识库），无外部 API 调用

## 快速开始

```bash
# 任意静态服务器都可以
cd webapp
python3 -m http.server 8000
# 浏览器打开 http://127.0.0.1:8000
```

或直接双击 `webapp/index.html` 用 file:// 协议打开（剪贴板复制可能受限于浏览器安全策略，建议用 http 服务器）。

## 与 Python 工具配合使用

仓库根目录有一个 Python 命令行工具 `lead_finder/`，能批量从公开企业网站抓取
B2B 邮箱并导出 CSV：

```bash
pip install -r requirements.txt
python -m lead_finder.cli --target 100
```

输出的 `output/leads.csv` **可以直接导入 webapp 的"客户追踪"模块**，
然后切到"开发信模板"批量生成邮件。

## 找到 100 个邮箱的最快路径

1. **Apollo.io**：筛选 美国 / 德国，行业 = "Consumer Electronics" 或
   "Phone Accessories"，导出 ~50 个联系人
2. **ImportGenius**：查近 6 个月从中国进口 USB-C charger / cable / GaN
   charger 的美国公司，再用 **Hunter.io** 补全邮箱（~30 个）
3. **LinkedIn**：搜 `phone accessories buyer USA` /
   `purchasing manager mobile accessories`，逐一加好友（~20 个）
4. 全部导入 webapp 客户追踪模块，按 4 周计划推进

## 技术栈

- 纯 HTML5 + CSS3 + Vanilla ES2017 JavaScript
- 无构建步骤、无 npm 依赖
- 数据持久化：`localStorage`
- 浏览器要求：Chrome / Edge / Safari / Firefox 最近 2 年版本

## 目录结构

```
webapp/
├── index.html
├── css/
│   └── styles.css
├── js/
│   ├── data.js          # 关键词 / 平台 / AI 知识库（静态数据）
│   ├── keywords.js      # 模块 1
│   ├── platforms.js     # 模块 2
│   ├── crm.js           # 模块 3
│   ├── templates.js     # 模块 4
│   ├── ai.js            # 模块 5
│   └── app.js           # Tab 切换 + toast
└── README.md
```

## 合规提醒

- 仅采集**公开商业邮箱**（info@ / sales@ / purchasing@ 等）
- 外发须遵守 CAN-SPAM（美）/ GDPR + ePrivacy（欧）/ PECR（英）/ CASL（加）
- 邮件中**必须**包含真实物理地址 + 可见退订方式
- 收到拒绝/退订请立即从列表移除
- 不要使用购买的列表，不要伪造发件人信息

## License

MIT
