#!/bin/bash
set -e

echo "=== ThaiACC: ดึง OCA dependencies ด้วย gitaggregate ==="
cd /workspace
gitaggregate -c repos.yml -j 4

echo "=== ThaiACC: พร้อมใช้งาน! ==="
echo ""
echo "เริ่ม Odoo:"
echo "  odoo -d thaiacc --db_host=db --db_user=odoo --db_password=odoo --http-interface=0.0.0.0 -i thaiacc"
echo ""
echo "แล้วตั้ง Port 8069 เป็น Public ใน Ports tab"
