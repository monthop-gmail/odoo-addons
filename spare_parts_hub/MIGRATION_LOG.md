# sph_core / spare_parts_hub — migration log 19.0 → 20.0

Source: `monthop-gmail/odoo-contributions` `custom-modules/spare-parts-hub-poc`
(`sph/poc` @ `00260a7`), moved here with history (git subtree, 2026-10-27).
Result: `sph_core` 20.0.0.1.0 on pinned `odoo:20.0-20261015`. All gates of the
harness CI green: 130 module tests (128 bound in `expected-tests.json` + 2), live
G1 HTTP / G2 race (4 rounds, lock contention every round) / G3 authority
(deny 140 / allow 22 = reviewed baseline) / Flow A / Flow B, demo, dashboard,
empty and retained-SYNTHETIC upgrade, P0 report.

## Pins (reviewed update, README "Pins and drift checks")

| Pin | 19.0 | 20.0 |
|---|---|---|
| image | `odoo:19.0-20260926@sha256:22bd89f3…` | `odoo:20.0-20261015@sha256:fc098344…` (linux/amd64) |
| deb / sha1 | 19.0.20260926 / `cb9d8767…` | 20.0.20261015 / `ae908bc0…` |
| odoo/docker ref | `8e31a777…` | `bf04b8fe…` |
| python | 3.12.3 | 3.12.3 |
| runtime-python.lock | 80 dists | 81: +h11 0.14.0, +pypdf 4.0.2, −pypdf2, odoo 20 |

Digest and inventory came from a one-off CI job (`docker buildx imagetools
inspect` + `runtime_inventory.py` in the image), removed in the same PR; deb
version/sha1/build ref from `odoo/docker` `20.0/Dockerfile`.

## Module changes

| 20.0 change | Effect on SPH | Fix |
|---|---|---|
| `ir.model.access` + `ir.rule` → `ir.access` | install fails | `security/ir.access.csv`: ACL rows → permissions; the 12 global rules → restriction rows (no group), same xmlids |
| `ir.rule._compute_domain` gone | incident reference on POs | `restriction_domain()` = AND of the user's restriction rows (rule scope without the ACL grant, as before) |
| `stock.scrap` removed (scrap = `stock.move` with `is_scrap`) | install fails | authority on `stock.move.action_scrap` / `_action_scrap` / `write(state=done)` of scrap moves |
| product `tracking` `'none'` removed (False) | fixtures, reservation guard | `False` / `not product.tracking` |
| `registry.clear_cache()` / `signal_changes()` removed | membership change kept stale access domains | `env.transaction.invalidate_ormcache()` before commit (signalled at commit) |
| `purchase.order._prepare_picking` removed | receipts had no center → hidden from center users | `stock.move._get_new_picking_values` sets the PO's `sph_center_id` |
| every regular group implies `base.group_user_regular` | "grant implies nothing" checks | that tier marker (implies nothing itself, asserted) is excluded |

## Harness / scripts

- `odoo.http.root` removed → `odoo.http.session.session_store()` (all live workers).
- Public `read_group` is the aggregate API in 20.0 → G1 uses `formatted_read_group`.
- G2: in `odoo shell` on 20.0 the worker's REPEATABLE READ snapshot did not
  include rows the HTTP workers committed meanwhile → commit before reading
  them (round start, native unreserve, after the expiry reservation).
- G3: `do_scrap` (public in 19.0) → `write(state=done)` on the scrap move
  (`_action_scrap` is private over RPC); same count, baseline unchanged.
- Scrap moves start confirmed/assigned, not draft: denied = state unchanged and not done.
- `stock.move` `product_uom` → `uom_id` (G2 native picking).
- Upgrade tests: 19.0 code cannot install on the 20.0 image, so both upgrades
  (empty and retained) start from `7b6b6ab`, the first commit that installs on
  20.0. The B7→B8 grant change predates it: both phases carry `picking_hub`.
  Requires merge commits (SHA kept); a squash merge must update the SHA.
- CI: failures surface as annotations (log lines, failing JSON checks, live
  cases with location); P0 report records `error_message` for every failure.

## Open (unchanged, owner decisions)

DN-B8-1 / DN-B / DN-C, OD6 (War Room link), staging/RPO/RTO. Synthetic data only; NOT pilot-ready.
