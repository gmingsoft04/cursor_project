"""初始化时插入若干内置开发信模板（仅在表为空时执行）"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Template


SEED_TEMPLATES = [
    {
        "name": "首封开发信 - GaN 快充推荐",
        "subject": "Reliable supplier of GaN fast chargers for {{ company }}",
        "is_html": True,
        "description": "适合首次接触客户，主打 GaN 快充头卖点",
        "body": """\
<p>Hi {{ first_name }},</p>

<p>I'm {{ sender_name }}, a manufacturer specializing in <strong>GaN fast chargers (PD 20W~140W)</strong>
and <strong>USB-C / Lightning fast charging cables</strong>. I noticed {{ company }} works in
the consumer-electronics space and thought our products may be a fit.</p>

<p>Why customers choose us:</p>
<ul>
  <li>In-house factory, 8+ years OEM/ODM experience</li>
  <li>UL / CE / FCC / RoHS / KC / PSE certifications available</li>
  <li>MOQ from 500pcs, lead time 15-25 days</li>
  <li>Custom logo, packaging and retail-ready boxes</li>
</ul>

<p>Could you share your typical SKU and target FOB price? I'll send a tailored quotation
and free samples within 24 hours.</p>

<p>Best regards,<br>
{{ sender_name }}</p>
""",
    },
    {
        "name": "首封开发信 - 数据线/Type-C 线",
        "subject": "USB-C / Lightning charging cables - factory direct quote for {{ company }}",
        "is_html": True,
        "description": "主打数据线/快充线品类",
        "body": """\
<p>Hello {{ first_name }},</p>

<p>Hope you are doing well. We are a charging-cable factory producing
<strong>USB-C to USB-C (60W/100W/240W)</strong>, <strong>USB-C to Lightning (MFi)</strong>,
and braided fast-charging cables for retail and B2B clients worldwide.</p>

<p>Recent shipments include EU and US retailers similar to {{ company }}, with these benefits:</p>
<ul>
  <li>USB-IF / MFi / CE / FCC certified</li>
  <li>3000+ bend lifecycle, e-marker chip on 100W+</li>
  <li>Custom length, color, packaging, private label welcome</li>
</ul>

<p>If you can share the cable spec / quantity you usually source, I'll prepare a
quote with FOB Shenzhen / Yantian within one business day.</p>

<p>Looking forward to your reply.</p>

<p>Best,<br>
{{ sender_name }}</p>
""",
    },
    {
        "name": "跟进信 - 7 天未回复",
        "subject": "Quick follow-up: chargers & cables quotation for {{ company }}",
        "is_html": True,
        "description": "首封信发出 7 天未回复的礼貌跟进",
        "body": """\
<p>Hi {{ first_name }},</p>

<p>Just floating this back to the top of your inbox in case my previous email got buried.</p>

<p>I'd be happy to send a free sample of our latest <strong>65W GaN charger</strong> and
<strong>100W USB-C cable</strong> to {{ company }} so your team can evaluate the build quality first-hand.</p>

<p>Would shipping to your office work? Just let me know the address and a contact phone number.</p>

<p>Best regards,<br>
{{ sender_name }}</p>
""",
    },
    {
        "name": "节日问候 + 新品",
        "subject": "Season's greetings from your charger partner",
        "is_html": True,
        "description": "节日问候 + 顺势推新品（140W GaN / 240W EPR 线）",
        "body": """\
<p>Dear {{ first_name }},</p>

<p>Wishing you and the {{ company }} team a wonderful holiday season!</p>

<p>We've just released two new products that may interest you:</p>
<ol>
  <li><strong>140W GaN III</strong> tri-port charger - travel-ready, MacBook Pro 16" capable.</li>
  <li><strong>240W EPR USB-C cable</strong> - future-proof for the latest USB-C laptops.</li>
</ol>

<p>If you'd like specs, MOQ or sample, just reply with "send specs" and I'll forward the brochure.</p>

<p>Warm regards,<br>
{{ sender_name }}</p>
""",
    },
]


def seed_templates(db: Session) -> int:
    existing = db.execute(select(Template.id)).first()
    if existing:
        return 0
    count = 0
    for t in SEED_TEMPLATES:
        db.add(Template(**t))
        count += 1
    db.commit()
    return count
