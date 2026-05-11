# FastCharge Leads

FastCharge Leads 是一个面向外贸业务的 Python 获客系统，聚焦 **手机快充头、GaN 充电器、USB-C PD 充电器、快充线、Type-C / iPhone 快充线** 等产品。系统把 Serper.dev 搜索、Apollo.io 联系人补全、LinkedIn 官方 API 公司补全，以及可配置的海关数据接口串成一条可落地的获客流水线。

## 能力概览

- 针对快充头和快充线自动生成高意向搜索词。
- 通过 Serper.dev 获取潜在进口商、分销商、批发商、零售商和电商卖家。
- 通过 Apollo.io 根据公司域名、关键词和采购类职位查找联系人。
- 通过 LinkedIn 官方 API 补全 LinkedIn 公司页公开组织信息。
- 通过通用海关数据接口获取进口商记录，并与网页线索合并。
- 对公司线索去重、打分、落库到 SQLite，并导出 CSV。
- 所有外部接口都集中在 `src/fastcharge_leads/clients/`，便于替换实际服务商。

## 项目结构

```text
src/fastcharge_leads/
  clients/          # Serper、Apollo、LinkedIn、海关数据 HTTP 适配器
  cli.py            # 命令行入口
  config.py         # 环境变量配置
  models.py         # 标准化公司、联系人、搜索结果、海关记录模型
  pipeline.py       # 获客主流程：搜索 -> 海关 -> 补全 -> 评分 -> 存储
  query_builder.py  # 快充产品和目标市场搜索词模板
  scoring.py        # 线索评分规则
  store.py          # SQLite 存储与 CSV 导出
tests/              # 单元测试
examples/           # 示例种子配置
```

## 配置

复制示例配置：

```bash
cp .env.example .env
```

关键环境变量：

| 变量 | 说明 |
| --- | --- |
| `SERPER_API_KEY` | Serper.dev API Key，用于 Google 搜索结果 |
| `APOLLO_API_KEY` | Apollo.io API Key，用于联系人搜索 |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn 官方 API token；可访问能力取决于应用权限 |
| `CUSTOMS_API_BASE` | 海关数据服务商 REST API base URL |
| `CUSTOMS_API_KEY` | 海关数据接口 Key，可为空 |
| `CUSTOMS_IMPORT_ENDPOINT` | 海关进口记录路径，默认 `/import-records` |
| `LEADS_DB_PATH` | SQLite 数据库路径，默认 `fastcharge_leads.sqlite3` |

海关接口适配器会发起：

```http
GET {CUSTOMS_API_BASE}{CUSTOMS_IMPORT_ENDPOINT}?q={product}&product={product}&country={country}&limit={limit}
```

并兼容常见返回字段：`records`、`results` 或 `data`；单条记录兼容 `importer_name`、`buyer_name`、`company_name`、`consignee`、`product_description`、`description`、`hs_code` 等字段。

## 使用

无需 API Key 也可以先预览搜索词：

```bash
PYTHONPATH=src python3 -m fastcharge_leads.cli run \
  --products "GaN fast charger,USB-C fast charging cable" \
  --markets "United States,Germany" \
  --max-queries 6 \
  --dry-run
```

初始化数据库：

```bash
PYTHONPATH=src python3 -m fastcharge_leads.cli init-db
```

配置 API Key 后运行真实采集：

```bash
PYTHONPATH=src python3 -m fastcharge_leads.cli run \
  --products "GaN fast charger,USB-C PD charger,fast charging cable" \
  --markets "United States,Germany,United Arab Emirates" \
  --per-query 10 \
  --max-queries 30
```

导出 CSV：

```bash
PYTHONPATH=src python3 -m fastcharge_leads.cli export \
  --output exports/fastcharge_leads.csv \
  --limit 1000
```

## 线索评分逻辑

系统会综合以下信号给公司线索打 0-100 分：

- 是否有官网域名或 LinkedIn 公司页。
- 是否命中海关进口记录。
- Apollo 是否找到采购、老板、创始人、进口经理、品类经理等联系人。
- 文本中是否出现 GaN、PD charger、USB-C、charging cable、mobile accessories 等产品词。
- 文本中是否出现 importer、distributor、wholesale、retailer、buyer 等买家意图词。
- 是否有目标国家/地区信息。

## 合规说明

- LinkedIn 集成只调用官方 API，不包含页面抓取逻辑。
- Apollo 与海关数据的可用字段、额度和授权范围取决于账号及服务商合同。
- 建议在实际外联前对邮箱、公司状态和采购角色进行二次校验。

## 测试

```bash
PYTHONPATH=src python3 -m unittest discover -s tests
```
