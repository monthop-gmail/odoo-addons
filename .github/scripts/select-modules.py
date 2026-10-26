#!/usr/bin/env python3
"""Split the Odoo modules of this repo into "ready" and "pending" for a series.

ready   = manifest version starts with "<series>." and installable is not False
pending = everything else, with the reason

Usage:
  select-modules.py --series 20.0 --addons-path DIR[,DIR...] \
      [--host-root PATH --container-root /workspace] [--summary]

Only addons dirs under --host-root are scanned (Odoo core addons are skipped).
Writes ready / pending / pending_installable / addons_path to $GITHUB_OUTPUT
(addons_path is mapped from --host-root to --container-root) and, with
--summary, markdown tables to $GITHUB_STEP_SUMMARY. Under GitHub Actions,
problems are also emitted as ::error / ::warning annotations.
"""
import argparse
import ast
import os
import sys


def annotate(level, title, msg):
    """GitHub annotation (::error / ::warning), escaped and kept on one line."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    msg = " ".join(str(msg).split())[:900].replace("%", "%25")
    title = title[:80].replace("%", "%25").replace(":", "%3A").replace(",", "%2C")
    print(f"::{level} title={title}::{msg}")


def read_manifest(path):
    with open(path, encoding="utf-8") as f:
        return ast.literal_eval(f.read())


def scan(dirs, series):
    ready, pending = [], []
    for d in dirs:
        for name in sorted(os.listdir(d)):
            manifest = os.path.join(d, name, "__manifest__.py")
            if not os.path.isfile(manifest):
                continue
            try:
                data = read_manifest(manifest)
            except Exception as e:  # noqa: BLE001
                pending.append((name, "?", False, f"manifest unreadable: {e}"))
                annotate("warning", f"{name} manifest unreadable", f"{name}/__manifest__.py: {e}")
                continue
            version = str(data.get("version", ""))
            installable = data.get("installable", True) is not False
            if not installable:
                pending.append((name, version, False, "installable = False"))
            elif not version.startswith(series + "."):
                pending.append((name, version, True, f"version is not {series}.*"))
            else:
                ready.append((name, version))
    return ready, pending


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--series", required=True)
    p.add_argument("--addons-path", required=True)
    p.add_argument("--host-root", default=os.getcwd())
    p.add_argument("--container-root", default="/workspace")
    p.add_argument("--core-addons", default="/usr/lib/python3/dist-packages/odoo/addons")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()

    host_root = os.path.realpath(args.host_root)
    dirs = []
    for entry in args.addons_path.split(","):
        entry = entry.strip().rstrip("/")
        if not entry or not os.path.isdir(entry):
            continue
        real = os.path.realpath(entry)
        if real == host_root or real.startswith(host_root + os.sep):
            dirs.append(real)
    if not dirs:
        msg = f"no addons dir under {host_root} in {args.addons_path!r}"
        annotate("error", "select-modules", msg)
        sys.exit(msg)

    ready, pending = scan(dirs, args.series)
    container_dirs = [args.container_root + d[len(host_root):] for d in dirs]
    outputs = {
        "ready": ",".join(m for m, _ in ready),
        "pending": ",".join(m for m, *_ in pending),
        "pending_installable": ",".join(m for m, _, inst, _ in pending if inst),
        "addons_path": ",".join([args.core_addons] + container_dirs),
    }
    for k, v in outputs.items():
        print(f"{k}={v}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            for k, v in outputs.items():
                f.write(f"{k}={v}\n")

    if args.summary and os.environ.get("GITHUB_STEP_SUMMARY"):
        lines = [f"## Modules for Odoo {args.series}", "",
                 f"Addons path: `{outputs['addons_path']}`", "",
                 f"### Ready ({len(ready)})", ""]
        if ready:
            lines += ["| Module | Version |", "|---|---|"]
            lines += [f"| `{m}` | {v} |" for m, v in ready]
        else:
            lines.append(f"_No module has a {args.series}.* manifest yet._")
        lines += ["", f"### Pending ({len(pending)})", ""]
        if pending:
            lines += ["| Module | Version | Reason |", "|---|---|---|"]
            lines += [f"| `{m}` | {v} | {r} |" for m, v, _, r in pending]
        else:
            lines.append("_None._")
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n\n")


if __name__ == "__main__":
    main()
