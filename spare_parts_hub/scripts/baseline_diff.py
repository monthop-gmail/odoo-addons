"""Flag baseline+registry co-changes since the independently reviewed tip (#172)."""
import json
import subprocess
from harness import ROOT
from upgrade_path import folder_tree

REPO = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip()

# odoo-contributions 7ca94792, as rewritten by git subtree into odoo-addons
REVIEWED = 'b6d8a4db73c37d8bedbbdf0c24d3ff08e2e960e7'
FILES = {'p0-evidence-baseline.json', 'p0-baseline-reviews.json'}


def validate_paths(paths):
    if FILES <= {path.rsplit('/', 1)[-1] for path in paths}:
        raise ValueError('baseline+registry co-change requires independent hub review')


def execute():
    if subprocess.run(['git', 'cat-file', '-e', REVIEWED + '^{commit}'], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
        # Same public read-only fetch pattern as upgrade_path; no credentials.
        subprocess.run(['git', 'fetch', '--no-tags', '--depth=1', 'origin', REVIEWED],
            cwd=ROOT, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    paths = subprocess.check_output(['git', 'diff', '--name-only', folder_tree(REVIEWED), folder_tree('HEAD'), '--',
        'p0-evidence-baseline.json', 'p0-baseline-reviews.json'], cwd=REPO, text=True).splitlines()
    result = {'reviewed_sha': REVIEWED, 'source_ref': 'dis-d3424628#172', 'changed_paths': paths,
        'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'status': 'FAIL'}
    directory = ROOT / 'evidence'; directory.mkdir(exist_ok=True)
    try:
        validate_paths(paths)
        result['status'] = 'PASS'
    except ValueError as error:
        result['reason'] = str(error)
        print(str(error), flush=True)
        raise
    finally:
        (directory / 'Baseline-diff-review.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


if __name__ == '__main__': execute()
