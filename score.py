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

    test_spec = make_test_spec(example)

    eval_ref = {
        KEY_INSTANCE_ID: test_spec.instance_id,
        FAIL_TO_PASS: test_spec.FAIL_TO_PASS,
        PASS_TO_PASS: test_spec.PASS_TO_PASS,
    }
    report = get_eval_tests_report(eval_sm, eval_ref)
    status = get_resolution_status(report)
    resolved = get_resolution_status(report) == ResolvedStatus.FULL.value
    return resolved


is_resolved = []
for path in Path("reports").rglob("*"):
    is_resolved.append(check_resolved(path))

print(sum(is_resolved), len(is_resolved))
import pdb; pdb.set_trace()
