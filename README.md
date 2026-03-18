# ThaiACC — โมดูลบัญชีไทยสำหรับ Odoo 19

โมดูลบัญชีไทยที่ migrate และปรับแต่งสำหรับ Odoo 19 สร้างบน [OCA/l10n-thailand](https://github.com/OCA/l10n-thailand)

## ติดตั้งด่วน

| โมดูล | สิ่งที่ได้ |
|--------|-----------|
| **thaiacc** | ทุกอย่างด้านล่างในคลิกเดียว (แนะนำ) |
| **accsumana** | เฉพาะโมดูลหลัก OCA Thai เท่านั้น |

## รายชื่อโมดูล

### Meta-packages

| โมดูล | รายละเอียด | รวมอะไรบ้าง |
|--------|-----------|------------|
| **thaiacc** | ชุดบัญชีไทยครบชุด | accsumana + โมดูลเสริมทั้งหมดด้านล่าง |
| **accsumana** | บัญชีไทยหลัก | l10n_th_account_tax, l10n_th_partner, l10n_th_mis_report ฯลฯ (10 โมดูล OCA) |

### โมดูลเสริม (รวมอยู่ใน thaiacc)

| โมดูล | รายละเอียด | Migrate จาก |
|--------|-----------|-------------|
| **l10n_th_account_tax_expense** | ใบกำกับภาษีค่าใช้จ่าย + ภาษีหัก ณ ที่จ่ายบน Expense | PR #498 (18.0) |
| **l10n_th_company_novat** | ตั้งค่าบริษัท/คู่ค้า จด/ไม่จด VAT, บล็อคภาษีสำหรับบริษัทไม่จด VAT | OCA 14.0 |
| **l10n_th_base_sequence** | เลขที่เอกสาร: พ.ศ., ไตรมาส, ช่วงวันที่ | monthop fork 19.0 |
| **l10n_th_sequence_branch** | เลขที่เอกสารตามสาขาบริษัท `%(b1-b5)s` | OCA 14.0 |
| **l10n_th_promptpay** | QR Code พร้อมเพย์บนหน้าชำระเงิน Website | OCA 16.0 |

### โมดูล OCA ที่ต้องใช้ (ดึงผ่าน gitaggregate)

ดึงจาก OCA repositories โดยใช้ `repos.yml`:

| Repo | โมดูลหลัก | Fork |
|------|----------|------|
| [l10n-thailand](https://github.com/OCA/l10n-thailand) | l10n_th_account_tax, l10n_th_partner, l10n_th_mis_report, ... | [monthop-gmail](https://github.com/monthop-gmail/l10n-thailand) |
| [partner-contact](https://github.com/OCA/partner-contact) | partner_company_type | [monthop-gmail](https://github.com/monthop-gmail/partner-contact) |
| [server-ux](https://github.com/OCA/server-ux) | base_tier_validation | [monthop-gmail](https://github.com/monthop-gmail/server-ux) |
| [mis-builder](https://github.com/OCA/mis-builder) | mis_builder | [versada](https://github.com/versada/mis-builder) |
| [reporting-engine](https://github.com/OCA/reporting-engine) | report_xlsx, report_xlsx_helper | OCA (upstream) |

## วิธีติดตั้ง

### วิธี A: Docker (แนะนำ)

ดู [accsumana-modular](https://github.com/monthop-gmail/accsumana-modular) สำหรับ Docker Compose setup

### วิธี B: ติดตั้งเองด้วย gitaggregate

```bash
# Clone repo นี้
git clone -b 19.0 https://github.com/monthop-gmail/odoo-addons.git
cd odoo-addons

# ติดตั้ง gitaggregate แล้วดึง OCA dependencies
pip install git-aggregator
gitaggregate -c repos.yml

# เพิ่มใน addons_path ใน odoo.conf:
addons_path = /path/to/odoo-addons,/path/to/odoo-addons/l10n-thailand,/path/to/odoo-addons/partner-contact,/path/to/odoo-addons/server-ux,/path/to/odoo-addons/mis-builder,/path/to/odoo-addons/reporting-engine
```

### Python Dependencies

```bash
pip install promptpay  # จำเป็นสำหรับ l10n_th_promptpay
```

## สถานะการ Migrate

### เสร็จแล้ว (อยู่ใน repo นี้)

- [x] l10n_th_account_tax_expense (Part 1: ใบกำกับภาษี + ภาษีหัก ณ ที่จ่าย)
- [x] l10n_th_company_novat
- [x] l10n_th_base_sequence
- [x] l10n_th_sequence_branch
- [x] l10n_th_promptpay
- [x] thaiacc (meta-package)

### รอดำเนินการ

- [ ] l10n_th_account_tax_expense Part 2 (สร้าง JV ภาษีหัก ณ ที่จ่ายสำหรับเคลียร์เงินทดรอง) — รอ `hr_expense_advance_clearing` บน 19.0
- [ ] l10n_th_google_fonts — มีเฉพาะ third-party ไม่อยู่ใน OCA

### ไม่ต้องทำ (รวมอยู่ในโมดูล OCA แล้ว)

- ~~l10n_th_sequence_be~~ → รวมเข้า `l10n_th_base_sequence` แล้ว
- ~~l10n_th_sequence_preview~~ → รวมเข้า `l10n_th_base_sequence` แล้ว
- ~~l10n_th_sequence_qoy~~ → รวมเข้า `l10n_th_base_sequence` แล้ว
- ~~l10n_th_sequence_range_end~~ → รวมเข้า `l10n_th_base_sequence` แล้ว
- ~~l10n_th_expense_tax_invoice~~ → รวมเข้า `l10n_th_account_tax_expense` แล้ว
- ~~l10n_th_expense_withholding_tax~~ → รวมเข้า `l10n_th_account_tax_expense` แล้ว
- ~~l10n_th_fonts~~ → ถูกแทนที่ด้วย `l10n_th_base_utils`

## สัญญาอนุญาต

- **accsumana**, **thaiacc**: [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html)
- **โมดูลอื่นทั้งหมด**: [AGPL-3](https://www.gnu.org/licenses/agpl-3.0.html)

## เครดิต

- [Ecosoft Co., Ltd](https://ecosoft.co.th/) — ผู้พัฒนาโมดูลต้นฉบับ
- ผู้ร่วมพัฒนา [OCA/l10n-thailand](https://github.com/OCA/l10n-thailand)
- [Accsumana](https://sumana.online) — migrate และจัดแพ็คเกจสำหรับ Odoo 19
