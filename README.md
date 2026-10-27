# odoo-addons

Odoo addons สาธารณะ (public) ของ monthop-gmail

## โครงสร้าง

- ใช้ **branch ต่อเวอร์ชัน Odoo** เช่น `19.0` (และ `20.0` ในภายหลัง)
- แต่ละโมดูลอยู่ที่ root ของ repo — ใช้ทั้ง repo เป็น addons path ได้ทันที
- โมดูลที่ซื้อมา หรือเป็นงานเฉพาะโปรเจกต์ ไม่ใส่ที่นี่ ให้ไปไว้ที่ repo private แทน

## โมดูล

| โมดูล | เวอร์ชัน | ที่มา |
|---|---|---|
| legal_forms | 19.0 | มาจาก lawform-odoo |
| `spare_parts_hub/` (`sph_core`) | 19.0 | PoC ศูนย์อะไหล่สหกรณ์ ย้ายมาจาก `odoo-contributions` `custom-modules/spare-parts-hub-poc` (branch `sph/poc` @ `00260a7`) พร้อม history · ไม่ใช่โมดูลที่ root: addon อยู่ที่ `spare_parts_hub/addons/sph_core` และมี harness + CI ของตัวเอง (`.github/workflows/sph-harness.yml`) · ข้อมูลสมมติเท่านั้น · MIT |
