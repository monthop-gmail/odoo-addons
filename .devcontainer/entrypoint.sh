#!/bin/bash
set -e

echo "=== ThaiACC Odoo Entrypoint ==="

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
export PGPASSWORD=odoo
until pg_isready -h db -U odoo -q; do
    sleep 1
done
echo "PostgreSQL is ready!"

# Pull OCA dependencies if not already present
if [ ! -d "/workspace/l10n-thailand" ]; then
    echo "Pulling OCA dependencies with gitaggregate..."
    cd /workspace
    gitaggregate -c repos.yml -j 4 || true
else
    echo "OCA dependencies already present."
fi

# Build addons path (only include dirs that exist)
ADDONS_PATH="/usr/lib/python3/dist-packages/odoo/addons"
for dir in /workspace/l10n-thailand /workspace/partner-contact /workspace/server-ux /workspace/mis-builder /workspace/reporting-engine /workspace; do
    if [ -d "$dir" ]; then
        ADDONS_PATH="$ADDONS_PATH,$dir"
    fi
done

# Create database if not exists
DB_EXISTS=$(psql -h db -U odoo -tAc "SELECT 1 FROM pg_database WHERE datname='thaiacc'" 2>/dev/null || echo "0")
if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating database 'thaiacc'..."
    createdb -h db -U odoo thaiacc
    echo "Installing thaiacc module with demo data..."
    exec odoo -d thaiacc \
        --db_host=db --db_user=odoo --db_password=odoo \
        --http-interface=0.0.0.0 \
        --addons-path="$ADDONS_PATH" \
        --init=thaiacc \
        --without-demo=False
fi

# Check if thaiacc module is installed
MODULE_INSTALLED=$(psql -h db -U odoo -d thaiacc -tAc \
    "SELECT 1 FROM ir_module_module WHERE name='thaiacc' AND state='installed'" 2>/dev/null || echo "0")
if [ "$MODULE_INSTALLED" != "1" ]; then
    echo "Module thaiacc not installed. Installing with demo data..."
    exec odoo -d thaiacc \
        --db_host=db --db_user=odoo --db_password=odoo \
        --http-interface=0.0.0.0 \
        --addons-path="$ADDONS_PATH" \
        --init=thaiacc \
        --without-demo=False
fi

echo "Database 'thaiacc' ready, module installed. Starting Odoo..."
exec odoo -d thaiacc \
    --db_host=db --db_user=odoo --db_password=odoo \
    --http-interface=0.0.0.0 \
    --addons-path="$ADDONS_PATH"
