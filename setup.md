# Accsumana Odoo 19 Setup

## Structure

```
odoo-addons/          ← this repo (accsumana meta-module only)
├── accsumana/        ← our module
├── repos.yml         ← gitaggregate config
├── server-ux/        ← aggregated from OCA + our PRs
├── l10n-thailand/    ← aggregated from OCA + our PRs
├── partner-contact/  ← aggregated from OCA
└── mis-builder/      ← aggregated from OCA + versada PR
```

## Quick Start

```bash
# Install gitaggregate
pip install git-aggregator

# Aggregate all OCA repos with our pending PRs
gitaggregate -c repos.yml

# Add to Odoo addons_path:
# addons_path = odoo-addons,odoo-addons/server-ux,odoo-addons/l10n-thailand,odoo-addons/partner-contact,odoo-addons/mis-builder
```

## After PRs are merged

When OCA merges our PRs, remove the monthop merge lines from `repos.yml` and re-run:

```bash
gitaggregate -c repos.yml
```
