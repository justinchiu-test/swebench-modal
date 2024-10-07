import asyncio
import modal
from dataclasses import dataclass
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import numpy as np
import os
import random
import subprocess


@dataclass
class TestSpec:
    repo: str
    base_commit: str
    instance_image_key: str
    env_image_key: str
    setup_env_script: str
    install_repo_script: str
    eval_script: str
    diff: str


@dataclass
class ExecOutput:
    eval_output: str
    eval_err: str
    duration: float
    env_output: str
    env_err: str
    install_output: str
    install_err: str
    apply_output: str
    apply_err: str


def subrun(command):
    return subprocess.run(command, shell=True, text=True, capture_output=True)


app = modal.App("swebench-server")
volume = modal.Volume.from_name("swebench-repos", create_if_missing=True)
# i think the default is amd64, eg normal x86?
image = (modal.Image.from_registry("ubuntu:22.04", add_python="3.11")
    .run_commands("apt update")
    .apt_install("wget", "build-essential", "libffi-dev", "libtiff-dev", "python3", "python3-pip", "python-is-python3", "jq", "curl", "locales", "locales-all", "tzdata", "tar")
    .run_commands(
        "rm -rf /var/lib/apt/lists/*",
        "apt-get update && apt-get install software-properties-common -y",
        "add-apt-repository ppa:git-core/ppa -y",
        "apt-get update && apt-get install git -y",
    )
    .run_commands(
        # modified wget to always do x86
        "wget 'https://repo.anaconda.com/miniconda/Miniconda3-py311_23.11.0-2-Linux-x86_64.sh' -O miniconda.sh",
        "bash miniconda.sh -b -p /opt/miniconda3",
        "/opt/miniconda3/bin/conda init --all",
        "/opt/miniconda3/bin/conda config --append channels conda-forge",
        "adduser --disabled-password --gecos 'dog' nonroot",
    )
    .workdir("/root")
)


@app.function(
    image=image,
    volumes={"/vol": volume},
    concurrency_limit=100,
    timeout=3600,
    retries=4,
    cpu=1.0,
)
#@modal.web_endpoint(method="POST")
def run_tests(test_spec: TestSpec) -> ExecOutput:
#def run_tests(instance_image_key, env_image_key, setup_env_script, install_repo_script, eval_script, diff):
    import subprocess
    from pathlib import Path
    import time

    start_time = time.time()
    volume.reload()

    repo = test_spec.repo
    flatrepo = repo.replace("/", "__")
    base_commit = test_spec.base_commit

    image_path = "/root"
    env_path = f"{image_path}/env.sh"
    install_path = f"{image_path}/install.sh"
    eval_path = f"{image_path}/eval.sh"
    diff_path = f"{image_path}/diff"

    Path(image_path).mkdir(exist_ok=True, parents=True)

    with Path(env_path).open("w") as f:
        f.write(test_spec.setup_env_script)
    with Path(install_path).open("w") as f:
        f.write(test_spec.install_repo_script)
    with Path(eval_path).open("w") as f:
        f.write(test_spec.eval_script)
    with Path(diff_path).open("w") as f:
        f.write(test_spec.diff)

    print(f"running env for {repo}-{base_commit}")
    env_output = subrun("/bin/bash /root/env.sh")

    print(f"running install for {repo}-{base_commit}")
    install_output = subrun("/bin/bash /root/install.sh")

    print(f"running apply for {repo}-{base_commit}")
    apply_output = subrun("cd /testbed && git apply --allow-empty -v /root/diff")

    print(f"running eval for {repo}-{base_commit}")
    eval_output = subrun("/bin/bash /root/eval.sh")
    end_time = time.time()

    return ExecOutput(
        eval_output=eval_output.stdout,
        eval_err=eval_output.stderr,
        duration=end_time-start_time,
        env_output=env_output.stdout,
        env_err=env_output.stderr,
        install_output=install_output.stdout,
        install_err=install_output.stderr,
        apply_output=apply_output.stdout,
        apply_err=apply_output.stderr,
    )

image_arm = (modal.Image.from_registry("arm64v8/ubuntu:22.04", add_python="3.11")
    .run_commands("apt update")
    .apt_install("wget", "build-essential", "libffi-dev", "libtiff-dev", "python3", "python3-pip", "python-is-python3", "jq", "curl", "locales", "locales-all", "tzdata", "tar")
    .run_commands(
        "rm -rf /var/lib/apt/lists/*",
        "apt-get update && apt-get install software-properties-common -y",
        "add-apt-repository ppa:git-core/ppa -y",
        "apt-get update && apt-get install git -y",
    )
    .run_commands(
        "wget 'https://repo.anaconda.com/miniconda/Miniconda3-py311_23.11.0-2-Linux-aarch64.sh' -O miniconda.sh",
        "bash miniconda.sh -b -p /opt/miniconda3",
        "/opt/miniconda3/bin/conda init --all",
        "/opt/miniconda3/bin/conda config --append channels conda-forge",
        "adduser --disabled-password --gecos 'dog' nonroot",
    )
    .workdir("/root")
)


@app.function(
    image=image_arm,
    volumes={"/vol": volume},
    concurrency_limit=100,
    timeout=3600,
    retries=4,
    cpu=1.0,
)
#@modal.web_endpoint(method="POST")
def run_tests_arm(test_spec: TestSpec) -> ExecOutput:
#def run_tests(instance_image_key, env_image_key, setup_env_script, install_repo_script, eval_script, diff):
    import subprocess
    from pathlib import Path
    import time

    start_time = time.time()
    volume.reload()

    repo = test_spec.repo
    flatrepo = repo.replace("/", "__")
    base_commit = test_spec.base_commit

    image_path = "/root"
    env_path = f"{image_path}/env.sh"
    install_path = f"{image_path}/install.sh"
    eval_path = f"{image_path}/eval.sh"
    diff_path = f"{image_path}/diff"

    Path(image_path).mkdir(exist_ok=True, parents=True)

    with Path(env_path).open("w") as f:
        f.write(test_spec.setup_env_script)
    with Path(install_path).open("w") as f:
        f.write(test_spec.install_repo_script)
    with Path(eval_path).open("w") as f:
        f.write(test_spec.eval_script)
    with Path(diff_path).open("w") as f:
        f.write(test_spec.diff)

    print(f"running env for {repo}-{base_commit}")
    env_output = subrun("/bin/bash /root/env.sh")

    print(f"running install for {repo}-{base_commit}")
    install_output = subrun("/bin/bash /root/install.sh")

    print(f"running apply for {repo}-{base_commit}")
    apply_output = subrun("cd /testbed && git apply --allow-empty -v /root/diff")

    print(f"running eval for {repo}-{base_commit}")
    eval_output = subrun("/bin/bash /root/eval.sh")
    end_time = time.time()

    return ExecOutput(
        eval_output=eval_output.stdout,
        eval_err=eval_output.stderr,
        duration=end_time-start_time,
        env_output=env_output.stdout,
        env_err=env_output.stderr,
        install_output=install_output.stdout,
        install_err=install_output.stderr,
        apply_output=apply_output.stdout,
        apply_err=apply_output.stderr,
    )


@app.local_entrypoint()
async def main():
    import datasets
    import os
    import subprocess
    import json
    from tqdm.asyncio import tqdm_asyncio

    from swebench_modal.harness.test_spec import make_test_spec
    from swebench_modal.harness.log_parsers import MAP_REPO_TO_PARSER


    data = datasets.load_dataset("princeton-nlp/SWE-bench_lite", split="test")
    """
    repos = set(data["test"]["repo"])
    paths = clone_repos(repos)
    upload_repositories(volume, paths)
    import pdb; pdb.set_trace()
    """
    print(len(data))

    futures = []
    for example in data:
        test_spec = make_test_spec(example)
        args = dict(
            repo=test_spec.repo,
            base_commit=example["base_commit"],
            instance_image_key=test_spec.instance_image_key,
            env_image_key=test_spec.env_image_key,
            setup_env_script=test_spec.setup_env_script,
            install_repo_script=test_spec.install_repo_script,
            eval_script=test_spec.eval_script,
            diff=example["patch"], # GOLD PATCH
        )
        if "x86" in test_spec.base_image_key:
            futures.append(run_tests.remote.aio(TestSpec(**args)))
        else:
            futures.append(run_tests_arm.remote.aio(TestSpec(**args)))
    outputs = await tqdm_asyncio.gather(*futures, total=len(data))

    pass_rates = []
    logs = []
    all_passed = []
    failed = []
    for example, output in zip(data, outputs):
        log_parser = MAP_REPO_TO_PARSER[example["repo"]]
        log = log_parser(output.eval_output)

        fail_rate = np.mean([result == "FAILED" for result in log.values()])
        any_fail = any([result == "FAILED" for result in log.values()])

        pass_rate = 1 - fail_rate
        all_pass = not any_fail

        logs.append(log)
        pass_rates.append(pass_rate)
        all_passed.append(all_pass)

        if not all_pass:
            failed.append((example, output, log))

        instance_id = example["instance_id"]
        with open(f"reports/{instance_id}", "w") as f:
            f.write(json.dumps((example, output.eval_output, log)))

    print("passed:", sum(all_passed), len(all_passed))


if __name__ == "__main__":
    asyncio.run(main())
