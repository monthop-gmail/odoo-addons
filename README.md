# ThaiACC — Thai Accounting Addons for Odoo 19

Custom and migrated Thai localization modules for Odoo 19, built on top of [OCA/l10n-thailand](https://github.com/OCA/l10n-thailand).

## Quick Install

| Module | What you get |
|--------|-------------|
| **thaiacc** | Everything below in one click (recommended) |
| **accsumana** | Core OCA Thai modules only |

## Modules

### Meta-packages

| Module | Description | Includes |
|--------|-------------|----------|
| **thaiacc** | Thai Accounting Complete Suite | accsumana + all optional modules below |
| **accsumana** | Core Thai Accounting | l10n_th_account_tax, l10n_th_partner, l10n_th_mis_report, etc. (10 OCA modules) |

### Optional Modules (included in thaiacc)

| Module | Description | Migrated From |
|--------|-------------|---------------|
| **l10n_th_account_tax_expense** | Expense Tax Invoice + WHT on Expense | PR #498 (18.0) |
| **l10n_th_company_novat** | Company/Partner VAT/NOVAT setup, block taxes for non-VAT | OCA 14.0 |
| **l10n_th_base_sequence** | Buddhist Era, Quarter, Range End legends for sequences | monthop fork 19.0 |
| **l10n_th_sequence_branch** | Company branch legends `%(b1-b5)s` for sequences | OCA 14.0 |
| **l10n_th_promptpay** | PromptPay QR code on website checkout | OCA 16.0 |

### OCA Dependencies (via gitaggregate)

These are pulled from OCA repositories using `repos.yml`:

| Repo | Key Modules | Fork |
|------|-------------|------|
| [l10n-thailand](https://github.com/OCA/l10n-thailand) | l10n_th_account_tax, l10n_th_partner, l10n_th_mis_report, ... | [monthop-gmail](https://github.com/monthop-gmail/l10n-thailand) |
| [partner-contact](https://github.com/OCA/partner-contact) | partner_company_type | [monthop-gmail](https://github.com/monthop-gmail/partner-contact) |
| [server-ux](https://github.com/OCA/server-ux) | base_tier_validation | [monthop-gmail](https://github.com/monthop-gmail/server-ux) |
| [mis-builder](https://github.com/OCA/mis-builder) | mis_builder | [versada](https://github.com/versada/mis-builder) |
| [reporting-engine](https://github.com/OCA/reporting-engine) | report_xlsx, report_xlsx_helper | OCA (upstream) |

## Setup

### Option A: Docker (recommended)

See [accsumana-modular](https://github.com/monthop-gmail/accsumana-modular) for Docker Compose setup.

### Option B: Manual with gitaggregate

```bash
# Clone this repo
git clone -b 19.0 https://github.com/monthop-gmail/odoo-addons.git
cd odoo-addons

# Install gitaggregate and pull OCA dependencies
pip install git-aggregator
gitaggregate -c repos.yml

# Add to Odoo addons_path in odoo.conf:
addons_path = /path/to/odoo-addons,/path/to/odoo-addons/l10n-thailand,/path/to/odoo-addons/partner-contact,/path/to/odoo-addons/server-ux,/path/to/odoo-addons/mis-builder,/path/to/odoo-addons/reporting-engine
```

### Python Dependencies

```bash
pip install promptpay  # Required by l10n_th_promptpay
```

## Migration Status

### Completed (in this repo)

- [x] l10n_th_account_tax_expense (Part 1: tax invoice + WHT)
- [x] l10n_th_company_novat
- [x] l10n_th_base_sequence
- [x] l10n_th_sequence_branch
- [x] l10n_th_promptpay
- [x] thaiacc (meta-package)

### Deferred

- [ ] l10n_th_account_tax_expense Part 2 (advance clearing WHT JV) — waiting for `hr_expense_advance_clearing` on 19.0
- [ ] l10n_th_google_fonts — third-party only, not in OCA

### Not Needed (already in OCA modules)

- ~~l10n_th_sequence_be~~ → merged into `l10n_th_base_sequence`
- ~~l10n_th_sequence_preview~~ → merged into `l10n_th_base_sequence`
- ~~l10n_th_sequence_qoy~~ → merged into `l10n_th_base_sequence`
- ~~l10n_th_sequence_range_end~~ → merged into `l10n_th_base_sequence`
- ~~l10n_th_expense_tax_invoice~~ → merged into `l10n_th_account_tax_expense`
- ~~l10n_th_expense_withholding_tax~~ → merged into `l10n_th_account_tax_expense`
- ~~l10n_th_fonts~~ → replaced by `l10n_th_base_utils`

## License

- **accsumana**, **thaiacc**: [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html)
- **All other modules**: [AGPL-3](https://www.gnu.org/licenses/agpl-3.0.html)

## Credits

- [Ecosoft Co., Ltd](https://ecosoft.co.th/) — original module authors
- [OCA/l10n-thailand](https://github.com/OCA/l10n-thailand) contributors
- [Accsumana](https://sumana.online) — migration & packaging for Odoo 19
