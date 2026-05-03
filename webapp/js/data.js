/* 静态数据：48 个分类关键词 + Google Dork + 8 个目标平台 + AI 知识库。
   仅本地静态数据，无网络请求。 */

window.KEYWORD_CATEGORIES = [
  {
    id: "buyer-search",
    name: "买家搜索词",
    desc: "买家在 Google 上找供应商时使用的真实词汇，反向定位他们。",
    items: [
      "wholesale phone charger supplier",
      "USB-C cable bulk buy",
      "GaN charger distributor",
      "phone accessories importer USA",
      "private label charger manufacturer",
      "MFi cable wholesale",
      "fast charger 65W bulk price",
      "type-c cable factory direct",
    ],
  },
  {
    id: "buyer-roles",
    name: "采购角色（LinkedIn）",
    desc: "LinkedIn / Apollo 中按头衔搜索 B2B 决策人。",
    items: [
      "phone accessories buyer",
      "purchasing manager mobile accessories",
      "sourcing manager consumer electronics",
      "category manager phone charger",
      "head of procurement electronics",
      "import manager mobile accessories",
      "product manager charging accessories",
      "merchandiser consumer electronics",
    ],
  },
  {
    id: "regions-us",
    name: "北美定向",
    desc: "美国 / 加拿大区域限定搜索。",
    items: [
      "phone charger wholesaler USA contact email",
      "USB-C cable importer United States",
      "consumer electronics distributor California",
      "Amazon FBA seller phone accessories USA",
      "wireless charger reseller Canada",
      "mobile accessories chain store USA",
    ],
  },
  {
    id: "regions-eu",
    name: "欧洲定向",
    desc: "DE / UK / FR / IT / ES / NL 等欧盟国家。",
    items: [
      "phone charger wholesaler Germany Großhandel",
      "USB-C cable distributor UK",
      "chargeur USB grossiste France",
      "caricabatterie ingrosso Italia",
      "cargador USB-C mayorista España",
      "telefoonoplader groothandel Nederland",
      "mobile accessories importer Europe",
      "consumer electronics distributor EU contact",
    ],
  },
  {
    id: "channels",
    name: "销售渠道关键词",
    desc: "锁定具体的渠道型买家（B2B 平台 / 连锁 / 电商）。",
    items: [
      "Amazon FBA seller phone charger sourcing",
      "eBay top seller mobile accessories supplier",
      "Walmart marketplace seller charger",
      "Best Buy vendor phone accessories",
      "Currys supplier mobile accessories UK",
      "MediaMarkt supplier consumer electronics",
      "Target vendor phone charger",
      "TikTok Shop charger seller",
    ],
  },
  {
    id: "trade",
    name: "外贸/海关线索",
    desc: "用于在 ImportGenius / Panjiva / 52WMB 等平台精准锁定。",
    items: [
      "USB charger import data China",
      "HS code 8504 importer United States",
      "GaN charger bill of lading USA",
      "type-c cable customs records",
      "phone accessories shipment from Shenzhen",
      "consumer electronics consignee USA recent",
    ],
  },
];

/* Google Dork：高级搜索语法，点击直接打开 Google 搜索结果。 */
window.DORKS = [
  {
    label: "site:linkedin.com/in 美国手机配件采购",
    query: 'site:linkedin.com/in ("phone accessories" OR "mobile accessories") (buyer OR purchasing OR sourcing) USA',
  },
  {
    label: "美国进口商 contact 页面 + 邮箱",
    query: '"phone charger" (importer OR wholesaler OR distributor) "@" (intitle:contact OR inurl:contact) -site:linkedin.com -site:facebook.com USA',
  },
  {
    label: "德国批发商 Impressum + 邮箱",
    query: '"USB-C" (Großhändler OR Distributor OR Importeur) "@" (Impressum OR Kontakt) Deutschland',
  },
  {
    label: "英国批发商 contact + Mailto",
    query: '"USB cable" (wholesale OR distributor) UK ("contact us" OR "get in touch") "@"',
  },
  {
    label: "法国批发商邮箱",
    query: '"chargeur" (grossiste OR distributeur OR importateur) France contact "@"',
  },
  {
    label: "Amazon 美国卖家品牌官网",
    query: '"as seen on amazon" "phone charger" -site:amazon.com (intitle:contact OR inurl:contact)',
  },
  {
    label: "PDF 客户名单 / 经销商列表",
    query: '"authorized distributor" "phone accessories" filetype:pdf',
  },
  {
    label: "B2B 黄页目录中的 charger 卖家",
    query: '("phone charger" OR "USB cable") (intitle:directory OR intitle:catalog) "contact"',
  },
];

/* 8 个推荐获客平台 */
window.PLATFORMS = [
  {
    name: "Apollo.io",
    type: "B2B 联系人数据库",
    badge: "首选",
    featured: true,
    url: "https://app.apollo.io/#/companies",
    desc:
      "全球最大 B2B 数据库之一。可按 行业 + 国家 + 公司规模 + 头衔 直接筛选采购决策人，导出邮箱。",
    tips: [
      "免费档每月 60 条邮箱，付费档约 50 美元/月起",
      "推荐筛选：Industry = Consumer Electronics / Wholesale，Title = Buyer / Sourcing / Procurement",
      "支持 LinkedIn 一键插件抓取",
    ],
  },
  {
    name: "ImportGenius",
    type: "美国海关进口数据",
    badge: "高精准",
    featured: true,
    url: "https://www.importgenius.com/",
    desc:
      "查询美国海关入境记录（Bill of Lading）。可以直接看到哪些公司近 6 个月从中国采购充电器/数据线。",
    tips: [
      "搜索词：USB charger / phone charger / USB cable / GaN charger",
      "按 Consignee（收货人）拿到公司名后，再用 Hunter.io 找邮箱",
      "比 Panjiva 便宜，付费 ~$199/月，可买 1 周试用",
    ],
  },
  {
    name: "Panjiva (S&P)",
    type: "全球贸易数据",
    url: "https://panjiva.com/",
    desc:
      "覆盖比 ImportGenius 更广（包含部分非美国数据）。适合查南美、印度、欧洲部分港口的买家。",
    tips: ["价格较贵，建议先用 ImportGenius", "和 Capital IQ 集成，适合大客户尽调"],
  },
  {
    name: "Hunter.io",
    type: "域名 → 邮箱",
    badge: "必备",
    featured: true,
    url: "https://hunter.io/",
    desc:
      "输入公司域名，自动列出该域所有公开邮箱及匹配的姓名 / 头衔。配合 Apollo 或 ImportGenius 拿到的公司名一起用。",
    tips: ["免费档每月 25 次", "支持邮箱送达性校验（Verifier）", "Chrome 插件：在 LinkedIn 个人页直接显示邮箱"],
  },
  {
    name: "LinkedIn Sales Navigator",
    type: "B2B 决策人社交",
    url: "https://www.linkedin.com/sales/",
    desc:
      "按头衔 / 公司 / 国家精准定位买手，发 InMail 或拿到公司名后到 Hunter 找邮箱。",
    tips: [
      "搜索词：phone accessories buyer / purchasing manager mobile accessories",
      "免费 1 个月试用",
      "推荐组合 Phantom Buster 抓取",
    ],
  },
  {
    name: "Alibaba RFQ Market",
    type: "买家询盘平台",
    url: "https://rfq.alibaba.com/",
    desc:
      "买家主动发布的采购需求，含数量、目标价、收货国家。点进去可以直接报价，已带联系方式。",
    tips: ["筛选：Buying Frequency = High，Country = US/UK/DE", "对刚起步、没获客预算的厂家性价比最高"],
  },
  {
    name: "Global Sources / Made-in-China RFQ",
    type: "买家询盘平台",
    url: "https://www.globalsources.com/",
    desc:
      "面向欧美买家的 B2B 平台，RFQ 区可以反向看到对方采购意向。",
    tips: ["Made-in-China 也有类似询盘大厅", "适合做 GaN / MFi 等中高端品类"],
  },
  {
    name: "Kompass / Europages",
    type: "欧洲企业黄页",
    url: "https://www.europages.com/",
    desc:
      "欧洲老牌 B2B 企业目录。按行业 + 国家筛选，能拿到公司名 + 网站，再去 Hunter 找邮箱。",
    tips: ["免费可看公司列表", "适合德、法、意、西的中型批发商"],
  },
];

/* AI 客户生成：国家 × 类型 × 规模 → 策略 + 4 周计划 */
window.AI_KB = {
  countries: {
    "美国 (US)": {
      buyerProfile: "全球最大单一消费电子市场。Amazon、Walmart、Best Buy 是核心渠道。FBA 卖家活跃，对 GaN / MFi / 多口快充需求旺盛。",
      certs: ["FCC ID", "DoE VI 能效", "UL 60950", "MFi（Lightning 必备）", "CPC（如卖儿童相关）"],
      payment: ["T/T 30/70", "L/C at sight", "PayPal（小订单）"],
      hot: ["GaN III 65W / 100W", "USB-C to Lightning MFi", "MagSafe 兼容磁吸"],
    },
    "英国 (UK)": {
      buyerProfile: "脱欧后独立市场，需 UKCA 标志。Currys、Argos、John Lewis 是主流连锁。",
      certs: ["UKCA", "CE", "BS 1363（英标插头）", "RoHS"],
      payment: ["T/T 30/70", "Open Account（成熟客户）"],
      hot: ["三脚英标插头快充", "PD 20W 入门款", "USB-C MFi 数据线"],
    },
    "德国 (DE)": {
      buyerProfile: "欧洲最大消费电子市场，对认证和包装环保要求最严。MediaMarkt、Saturn 是连锁巨头。",
      certs: ["CE", "RoHS", "REACH", "VerpackG（包装法）", "WEEE", "EAC（如出俄）"],
      payment: ["T/T 30/70", "Trade Insurance"],
      hot: ["Type-C PD 65W", "环保包装 / 再生塑料", "GaN 多口"],
    },
    "法国 (FR)": {
      buyerProfile: "Fnac、Boulanger、Darty 等连锁。对包装法（Triman 标志）和 ROHS 严格。",
      certs: ["CE", "RoHS", "Triman", "DEEE/WEEE"],
      payment: ["T/T 30/70"],
      hot: ["小巧便携 PD 20W", "MagSafe 配件", "Lightning MFi"],
    },
    "意大利 (IT)": {
      buyerProfile: "Unieuro、MediaWorld（MediaMarkt 子品牌）为主。家庭式批发商较多。",
      certs: ["CE", "RoHS", "WEEE"],
      payment: ["T/T 30/70", "Open Account"],
      hot: ["性价比 PD 20W", "彩色编织数据线"],
    },
    "西班牙 (ES)": {
      buyerProfile: "El Corte Inglés、PcComponentes 为主。中小批发商对价格敏感。",
      certs: ["CE", "RoHS"],
      payment: ["T/T 30/70"],
      hot: ["车充 PD", "USB-C 数据线套装"],
    },
    "荷兰 (NL)": {
      buyerProfile: "欧洲电商物流枢纽（鹿特丹），bol.com、Coolblue 主流。多家泛欧分销商总部在此。",
      certs: ["CE", "RoHS", "WEEE"],
      payment: ["T/T 30/70"],
      hot: ["PD 多口 GaN", "MagSafe", "无线充"],
    },
    "瑞典 (SE)": {
      buyerProfile: "Elgiganten、NetOnNet 主流。北欧整体设计感要求高，环保溢价大。",
      certs: ["CE", "RoHS", "Nordic Ecolabel（加分）"],
      payment: ["T/T 30/70", "Open Account"],
      hot: ["简约设计快充", "再生材料数据线"],
    },
    "加拿大 (CA)": {
      buyerProfile: "Best Buy Canada、Staples、The Source。市场紧贴美国但更小。",
      certs: ["FCC", "ISED Canada", "CSA / cUL", "MFi"],
      payment: ["T/T 30/70"],
      hot: ["GaN 65W", "Lightning MFi"],
    },
    "澳大利亚 (AU)": {
      buyerProfile: "JB Hi-Fi、Officeworks、Harvey Norman 主流。澳标插头独立。",
      certs: ["RCM (SAA)", "C-Tick", "AS/NZS 3112（澳标插头）"],
      payment: ["T/T 30/70"],
      hot: ["澳标 PD 快充", "车充", "USB-C 数据线"],
    },
  },
  types: {
    distributor: {
      label: "进口商 / 批发分销商",
      strategy: [
        "首选 ImportGenius / Panjiva 找近 6 个月有进口记录的公司",
        "切入点：稳定供货能力 + 区域独家代理 + 现货保障",
        "MOQ 1000+，PI/Sample 流程完整，强调 OEM 能力",
      ],
      sample: "MOQ 500–1000 pcs，免费样品（运费到付）",
    },
    retailer: {
      label: "3C 配件零售连锁",
      strategy: [
        "通过 LinkedIn 找 Category Manager / Buyer，准备 line sheet PDF",
        "切入点：陈列设计 + 包装本地化 + 长保修期",
        "通常需要 Vendor Compliance 文档（保险、Code of Conduct）",
      ],
      sample: "需先寄展示样品到买手办公室（FedEx 4–7 天）",
    },
    ecommerce: {
      label: "跨境电商 / Amazon FBA 卖家",
      strategy: [
        "切入点：FBA-ready 包装 + 全套测试报告 + 商标授权信",
        "在 Amazon 同类产品下找到品牌名，反查官网 + 联系人",
        "提供 BSR Top 100 同款替代方案",
      ],
      sample: "MOQ 300–500 pcs，可贴牌 + 中性包装",
    },
    oem: {
      label: "品牌 OEM / ODM 采购方",
      strategy: [
        "切入点：研发能力 + 模具 + 量产稳定性 + IP 保密",
        "重点准备：BOM 明细、安规测试视频、产线照片、专利清单",
        "LinkedIn 找 Hardware PM / Sourcing Director，约一次电话深聊",
      ],
      sample: "MOQ 5000+，签 NDA，定制周期 45–60 天",
    },
    telecom: {
      label: "运营商 / 增值零售",
      strategy: [
        "进入门槛高：要求供应商认证体系（ISO 9001/14001 + 社会责任审核）",
        "切入点：与 Verizon/Vodafone 合作过的 ODM 工厂背书",
        "建议先成为 Tier 2 供应商（卖给他们的 ODM/集成商）",
      ],
      sample: "MOQ 10000+，长账期 60–90 天",
    },
  },
  scales: {
    small: { label: "小批量探索", days: 21, focus: "通过 RFQ 平台和 Apollo 免费档先验证渠道" },
    medium: { label: "中型订单", days: 28, focus: "组合 Apollo + ImportGenius + LinkedIn 三路并进" },
    large: { label: "长期合作", days: 30, focus: "重点突破 3–5 家头部，谈年度框架协议 / 独家代理" },
  },
};
