# Lead Finder — 快充头 / 快充线 欧美 B2B 客户采集工具

为中国快充头、快充线、GaN 充电器、USB-C/Lightning 数据线的批发商，
从公开企业联系页面采集欧美 B2B 潜在买家邮箱，并按可信度打分导出 CSV。

> 工具只采集**公开发布**的业务邮箱（如 `info@`, `sales@`, `purchasing@`），
> 默认遵守 `robots.txt`，**不**绕过登录、验证码或反爬措施。
> 外发前请阅读下方"合规说明"。

## 功能

- 关键词搜索：基于 DuckDuckGo（免 API key）按多区域 / 多关键词检索潜在 B2B 买家
- 网站抓取：抓首页 + 联系页（contact / about / impressum / wholesale 等）
- 反混淆：识别 `name [at] domain [dot] com`、`&#64;`、`mailto:` 等常见形式
- 评分：邮箱域 == 站点域、B2B 前缀、国家匹配、行业关键词、过滤个人邮箱
- 增量写盘：每抓完一个站点就更新 CSV，长跑也安全
- 黑名单：过滤社媒、CDN、`noreply`、`careers` 等无效邮箱
- 双语外发模板：英文 + 德文，含 GDPR / CAN-SPAM 友好表述

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 使用

```bash
python -m lead_finder.cli \
  --config config/queries.yaml \
  --output output/leads.csv \
  --target 100 \
  --regions us-en uk-en de-de fr-fr nl-nl ca-en au-en
```

主要参数：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--config` | `config/queries.yaml` | 关键词、前缀、黑名单等配置 |
| `--output` | `output/leads.csv` | 导出 CSV 路径（增量写） |
| `--target` | `100` | 目标 Lead 数量（按 score 排序取前 N） |
| `--per-query` | `25` | 每条 query × region 的搜索结果数 |
| `--pause` | `2.0` | 搜索请求间隔（秒），防限流 |
| `--regions` | `us-en …` | DDG 区域代码 |
| `--no-robots` | off | **不建议**关闭 robots.txt 校验 |
| `-v` | off | DEBUG 日志 |

CSV 字段：`company, domain, email, country_hint, score, source_url, snippet`。
`score` 越高表示越像采购对接邮箱（建议从 ≥ 60 分起人工核验）。

## 配置自定义关键词

编辑 `config/queries.yaml`：

- `search_queries`：B2B 买家画像关键词，已内置 18 条覆盖进口商 / 批发商 /
  连锁零售 / 跨境电商 / OEM 采购方
- `preferred_prefixes`：业务邮箱前缀（参与打分）
- `blocklist_domains` / `blocklist_locals`：黑名单域名 / 邮箱前缀

## 外发模板

- `templates/cold_email_en.txt` — 英文（含 CAN-SPAM 退订声明）
- `templates/cold_email_de.txt` — 德文（含 GDPR Art. 6(1)(f) 合法利益说明）

模板里的 `{sender_*}` / `{recipient_*}` 占位符可用 `string.Formatter`
或任何模板引擎在外发系统（Mailshake / Lemlist / Instantly / 自建 SMTP）
里替换。

## 合规说明（务必阅读）

不同地区对未经请求的商业邮件（"冷邮件"）有不同要求。本工具的设计前提
是**只采公开 B2B 联系邮箱**并发送**针对其业务的合规商业询盘**：

1. **美国 — CAN-SPAM Act**
   - 主题不得误导，必须能明确识别为商业邮件
   - 必须含**真实发件人物理地址**
   - 必须提供**可见的退订方式**，并在 10 个工作日内处理退订
2. **欧盟 — GDPR + ePrivacy**
   - B2B 通用业务邮箱（`info@`, `sales@`, `purchasing@`）通常可基于
     **合法利益（Art. 6(1)(f)）**联系，但必须：
     - 在邮件中说明数据来源、处理目的、退订方式
     - 收到拒绝/退订后立即停止并删除联系数据
   - 联系**自然人姓名 + 公司域名**邮箱（如 `john.smith@…`）门槛更高，
     建议先看其网站隐私政策是否允许商业询盘
3. **英国 — PECR**
   - B2B 邮件可在合法利益基础上发送，仍需提供退订方式
4. **加拿大 — CASL**
   - 默认要求"明确同意"。冷邮件应**保守**发送，并明确表明身份和退订方式
5. **通用建议**
   - 单域名/单收件人**每周不超过 1 次**跟进，3–4 次后停止
   - 不要使用购买的列表，不要伪造发件人信息
   - 维护**全局退订列表（suppression list）**

> 工具采集到的是公开商业邮箱，但**是否、何时、如何**外发由你自行决定。
> 若有疑问，请咨询当地法务。

## 目录结构

```
lead_finder/
  __init__.py
  search.py        # DuckDuckGo 搜索
  scraper.py       # 网站抓取 + 邮箱反混淆 + 打分
  cli.py           # 命令行入口
config/
  queries.yaml
templates/
  cold_email_en.txt
  cold_email_de.txt
requirements.txt
README.md
```

## 路线图

- [ ] LinkedIn Sales Navigator / Apollo / Hunter API 适配（需账号）
- [ ] 从邮箱推断对接人姓名（`first.last@…` 模式）
- [ ] 接入 NeverBounce / ZeroBounce 校验邮箱送达性
- [ ] Playwright 渲染：抓 JS 动态生成的联系信息
- [ ] HubSpot / Pipedrive 直推

## 免责声明

本仓库仅为研究和合法 B2B 拓展目的提供。使用者应自行确保符合当地数据
保护与反垃圾邮件法律。作者不对滥用造成的后果负责。
