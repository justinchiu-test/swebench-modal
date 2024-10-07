import json
import datasets
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np

from swebench_modal.harness.test_spec import make_test_spec
from swebench_modal.harness.log_parsers import MAP_REPO_TO_PARSER
from swebench_modal.harness.grading import get_eval_tests_report, get_resolution_status


data = datasets.load_dataset("princeton-nlp/SWE-bench_lite", split="test")
#data = datasets.load_dataset("princeton-nlp/SWE-bench_Verified", split="test")

base_image_counts = Counter()
base_image_key_to_repos = defaultdict(set)
repo_to_env_key = defaultdict(set)
for example in data:
    test_spec = make_test_spec(example)
    base_dockerfile = test_spec.base_dockerfile
    base_image_key = test_spec.base_image_key

    env_dockerfile = test_spec.env_dockerfile
    instance_dockerfile = test_spec.instance_dockerfile

    env_script = test_spec.env_script_list
    install_script = test_spec.install_repo_script

    base_image_key_to_repos[base_image_key].add(example["repo"])
    repo_to_env_key[example["repo"]].add(test_spec.env_image_key)

    base_image_counts[test_spec.base_image_key] += 1
    if "arm" not in test_spec.base_image_key:
        print(base_dockerfile)

print(sum([len(x) for x in repo_to_env_key.values()]), "envs")
print(base_image_counts)
import pdb; pdb.set_trace()
