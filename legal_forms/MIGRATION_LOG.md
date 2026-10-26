# legal_forms — Migration log

## 19.0 → 20.0 (2026-10-26)

Guide: `monthop-gmail/odoo-migration-guide` → `transitions/19-to-20/`
(all 21 `detect` patterns of `migration-rules.yaml` run against `legal_forms/`).

Forward-ported first: 19.0 test fix `3274ae9` (`test_basic_replacement`
calls `doc.action_apply_merge_fields()` before asserting).

| Rule | Hit (file:line) | Fix |
|------|-----------------|-----|
| `acl-csv-renamed` | `security/ir.model.access.csv` (16 rows); `__manifest__.py:17` | Renamed to `security/ir.access.csv`; `perm_*` → `operation` (`r` / `cru` / `crud`); `model_id` = model name (`legal.case`, …); `group_id/id`; manifest data list updated |
| `report-file-field-removed` | `reports/report_form_document.xml:24,36,48,60` | Removed `report_file` from the 4 `ir.actions.report` records (`report_name` unchanged) |
| `test-tags-default-post-install` | pattern no hit (tests import `TransactionCase` directly) | Reviewed: tests need no install-time run; post-install default is fine, no change |
| other 18 rules | no hit | — |

Manifest: `19.0.1.3.0` → `20.0.1.3.0`, `installable: False` removed.
`migrations/19.0.1.2.0`, `19.0.1.3.0` kept as 19.0 history; no new migration
script (guide's rules require none for these changes). No module behaviour change.
No new migration rule discovered.

CI result: see below.
