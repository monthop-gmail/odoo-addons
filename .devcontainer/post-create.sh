#!/bin/bash
set -e

echo "=== ThaiACC: ดึง OCA dependencies ด้วย gitaggregate ==="
cd /workspace
gitaggregate -c repos.yml -j 4

echo "=== ThaiACC: พร้อมใช้งาน! ==="
echo ""
echo "เริ่ม Odoo:"
echo "  odoo -d thaiacc --db_host=db --db_user=odoo --db_password=odoo -i thaiacc"
echo ""
echo "เปิด browser: http://localhost:8069"
