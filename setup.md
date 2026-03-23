# ThaiACC Odoo 19 Setup

## Structure

```
thaiacc-odoo/                        ← this repo
├── .devcontainer/
│   ├── devcontainer.json           ← docker-in-docker config
│   ├── Dockerfile                  ← Odoo 19 + Thai fonts + gitaggregate
│   ├── entrypoint.sh              ← auto: gitaggregate → start Odoo
│   ├── setup.sh                   ← postCreateCommand
│   └── start.sh                   ← postStartCommand (docker compose up)
├── docker-compose.yml              ← Odoo + PostgreSQL services
├── thaiacc/                        ← complete suite (installs everything)
├── ocaacc/                         ← core OCA Thai modules
├── l10n_th_account_tax_expense/    ← expense tax invoice + WHT
├── l10n_th_company_novat/          ← VAT/NOVAT company setup
├── l10n_th_base_sequence/          ← sequence legends (BE, quarter, etc.)
├── l10n_th_sequence_branch/        ← sequence with company branch
├── l10n_th_promptpay/              ← PromptPay QR code
├── repos.yml                       ← gitaggregate config
├── README.md
└── setup.md                        ← this file
```

After running `gitaggregate -c repos.yml`, these directories are added:

```
├── l10n-thailand/      ← OCA + monthop migration PRs
├── server-ux/          ← OCA + monthop tier validation PRs
├── partner-contact/    ← OCA + monthop partner_company_type PR
├── mis-builder/        ← OCA + versada mis_builder PR
└── reporting-engine/   ← OCA report_xlsx, report_xlsx_helper
```

## Quick Start

```bash
# Install dependencies
pip install git-aggregator promptpay

# Aggregate all OCA repos with pending migration PRs
gitaggregate -c repos.yml

# Add to Odoo addons_path:
addons_path = thaiacc-odoo,thaiacc-odoo/l10n-thailand,thaiacc-odoo/partner-contact,thaiacc-odoo/server-ux,thaiacc-odoo/mis-builder,thaiacc-odoo/reporting-engine
```

Then install `thaiacc` from Odoo Apps menu to get everything.

## After OCA PRs are merged

When OCA merges our migration PRs upstream, update `repos.yml`:
1. Remove the `monthop` merge lines for merged PRs
2. Re-run `gitaggregate -c repos.yml`
