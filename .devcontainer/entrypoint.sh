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

# Start Odoo
ADDONS_PATH="/usr/lib/python3/dist-packages/odoo/addons"
for dir in /workspace/l10n-thailand /workspace/partner-contact /workspace/server-ux /workspace/mis-builder /workspace/reporting-engine /workspace; do
    if [ -d "$dir" ]; then
        ADDONS_PATH="$ADDONS_PATH,$dir"
    fi
done

echo "Starting Odoo with addons: $ADDONS_PATH"
exec odoo -d thaiacc \
    --db_host=db --db_user=odoo --db_password=odoo \
    --http-interface=0.0.0.0 \
    --addons-path="$ADDONS_PATH"
