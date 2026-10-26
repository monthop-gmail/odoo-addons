# odoo-addons

Odoo addons สาธารณะ (public) ของ monthop-gmail

## โครงสร้าง

- ใช้ **branch ต่อเวอร์ชัน Odoo** เช่น `19.0`, `20.0`
- แต่ละโมดูลอยู่ที่ root ของ repo — ใช้ทั้ง repo เป็น addons path ได้ทันที
- โมดูลที่ซื้อมา หรือเป็นงานเฉพาะโปรเจกต์ ไม่ใส่ที่นี่ ให้ไปไว้ที่ repo private แทน

## โมดูล

| โมดูล | เวอร์ชัน | ที่มา |
|---|---|---|
| legal_forms | 19.0 | มาจาก lawform-odoo · บน 20.0 ตั้ง `installable: False` รอ migrate |
| village_poc | 20.0 | มาจาก village-odoo-poc |
| donation_poc | 20.0 | มาจาก donation-odoo-poc |
| canteen_poc | 20.0 | มาจาก canteen-odoo-poc |

### หมายเหตุ village_poc / donation_poc / canteen_poc

- เป็น **Fast PoC** ใช้ข้อมูลสังเคราะห์ (synthetic data) เท่านั้น **ไม่ใช่ production** — การชำระเงิน, AI advisory และ external wallet (TruePoint/TrueMoney) เป็น mock/simulated
- donation_poc และ canteen_poc ต้องตั้ง System Parameter เบอร์ PromptPay ผู้รับเงินก่อนเรียก demo setup
  (`donation_poc.promptpay_mobile`, `canteen_poc.promptpay_mobile`) — ถ้าไม่ได้ตั้งระบบจะ raise `UserError` ไม่มีเบอร์ default ในโค้ด
  - Odoo 20 ไม่มี `get_param`/`set_param` แล้ว — โค้ดอ่านค่าด้วย `get_str(key, '')` และตั้งค่าในเทสต์/สคริปต์ด้วย `set_str(key, value)`
