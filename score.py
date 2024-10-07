import json
from pathlib import Path
import numpy as np

from swebench_modal.harness.constants import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
    FAIL_TO_FAIL,
    FAIL_TO_PASS,
    KEY_INSTANCE_ID,
    PASS_TO_FAIL,
    PASS_TO_PASS,
    RESET_FAILED,
    TESTS_ERROR,
    TESTS_TIMEOUT,
    ResolvedStatus,
    TestStatus,
)
from swebench_modal.harness.test_spec import make_test_spec
from swebench_modal.harness.log_parsers import MAP_REPO_TO_PARSER
from swebench_modal.harness.grading import get_eval_tests_report, get_resolution_status


def check_resolved(path):
    with path.open("r") as f:
        example, output, eval_sm = json.loads(f.read())

    all_passed = all([v != "FAILED" for v in eval_sm.values()])

    eval_ref = {
        KEY_INSTANCE_ID: example["instance_id"],
        FAIL_TO_PASS: json.loads(example["FAIL_TO_PASS"]),
        PASS_TO_PASS: json.loads(example["PASS_TO_PASS"]),
    }
    report = get_eval_tests_report(eval_sm, eval_ref)
    status = get_resolution_status(report)
    resolved = get_resolution_status(report) == ResolvedStatus.FULL.value

    """
    gold_path = Path(f"gold_logs/{example['instance_id']}/report.json")
    with gold_path.open("r") as f:
        gold_report = json.loads(f.read())
    """
    return example["repo"], resolved, all_passed


repos = []
is_resolved = []
all_passed = []
for path in Path("reports").rglob("*"):
    repo, resolved,all_pass  = check_resolved(path)
    repos.append(repo)
    is_resolved.append(resolved)
    all_passed.append(all_pass)

print(sum(is_resolved), len(is_resolved))
import pdb; pdb.set_trace()
