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
cd /workspace
AGGREGATE_FAILED=""
if [ ! -d "/workspace/l10n-thailand" ]; then
    echo "Pulling OCA dependencies with gitaggregate..."
    gitaggregate -c repos.yml -j 4 || AGGREGATE_FAILED=1
else
    echo "OCA dependencies already present."
fi

# A failed aggregate leaves repos mid-merge with conflict markers in the source.
# Odoo would only notice much later, as a SyntaxError deep in the module loader,
# and the check above would then skip re-aggregating forever because the broken
# directory exists. So verify the result here and say what actually went wrong.
UNMERGED=""
for dir in /workspace/*/; do
    [ -d "$dir.git" ] || continue
    if [ -n "$(git -C "$dir" ls-files --unmerged 2>/dev/null)" ]; then
        UNMERGED="$UNMERGED $(basename "$dir")"
    fi
done

if [ -n "$AGGREGATE_FAILED" ] || [ -n "$UNMERGED" ]; then
    echo "" >&2
    echo "!!! OCA dependency aggregation is incomplete." >&2
    if [ -n "$UNMERGED" ]; then
        echo "    Repos left mid-merge:$UNMERGED" >&2
        echo "    Fix repos.yml or the branches it merges, then re-run:" >&2
        echo "      cd /workspace && rm -rf$UNMERGED && gitaggregate -c repos.yml -j 4" >&2
    else
        echo "    gitaggregate exited non-zero — see the log above." >&2
    fi
    echo "    Refusing to start Odoo: it would fail later with a confusing error." >&2
    exit 1
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
    --addons-path="$ADDONS_PATH" \
    --max-cron-threads=0
