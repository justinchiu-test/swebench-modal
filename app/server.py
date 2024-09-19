import modal
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import random


class TestSpec(BaseModel):
    repo: str
    instance_image_key: str
    env_image_key: str
    setup_env_script: str
    install_repo_script: str
    eval_script: str
    diff: str


app = modal.App("swebench-server")
volume = modal.Volume.from_name("swebench-repos", create_if_missing=True)
image = (modal.Image.from_registry("ubuntu:22.04", add_python="3.11")
    .run_commands("apt update")
    .apt_install("wget", "build-essential", "libffi-dev", "libtiff-dev", "python3", "python3-pip", "python-is-python3", "jq", "curl", "locales", "locales-all", "tzdata")
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
    .workdir("/testbed")
)


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("my-github-secret")],
    volumes={"/vol": volume}
)
@modal.web_endpoint(method="POST")
def run_tests(test_spec: TestSpec):
#def run_tests(instance_image_key, env_image_key, setup_env_script, install_repo_script, eval_script, diff):
    import subprocess
    from pathlib import Path
    import time

    start_time = time.time()

    repo = test_spec.repo
    flatrepo = repo.replace("/", "__")

    image_path = "/root"
    env_path = f"{image_path}/env.sh"
    install_path = f"{image_path}/install.sh"
    eval_path = f"{image_path}/eval.sh"
    diff_path = f"{image_path}/diff"

    Path(image_path).mkdir(exist_ok=True, parents=True)
    ghtoken = os.environ["GITHUB_TOKEN"]

    with Path(env_path).open("w") as f:
        f.write(test_spec.setup_env_script)
    with Path(install_path).open("w") as f:
        f.write(test_spec.install_repo_script.format(token=ghtoken))
    with Path(eval_path).open("w") as f:
        f.write(test_spec.eval_script)
    with Path(diff_path).open("w") as f:
        f.write(test_spec.diff)

    print("running env")
    env_output = subprocess.check_output(
        "/bin/bash /root/env.sh",
        stderr=subprocess.STDOUT,
        shell=True,
    ).decode("utf-8")
    print(env_output)
    print("running install")
    install_output = subprocess.check_output(
        "/bin/bash /root/install.sh",
        stderr=subprocess.STDOUT,
        shell=True
    ).decode("utf-8")
    print(install_output)
    time.sleep(2)
    print("running apply")
    apply_output = subprocess.check_output(
        "git apply --allow-empty -v /root/diff",
        stderr=subprocess.STDOUT,
        shell=True,
    ).decode("utf-8")
    print(apply_output)

    print("running eval")
    output = subprocess.check_output(
        "/bin/bash /root/eval.sh",
        stderr=subprocess.STDOUT,
        shell=True,
    ).decode("utf-8")
    end_time = time.time()
    return output, end_time-start_time, env_output, install_output, apply_output


def upload_repositories(volume, paths):
    with volume.batch_upload() as batch:
        for srcpath, tgtpath in paths:
            batch.put_directory(srcpath, tgtpath)

def clone_repos(repos):
    import subprocess
    action = "git clone https://{token}@github.com/{repo} repos/{flatrepo}"
    paths = []
    for repo in repos:
        flatrepo = repo.replace("/", "__")
        output = subprocess.check_output(
            action.format(
                token=os.environ["GITHUB_TOKEN"],
                repo=repo,
                flatrepo=flatrepo),
            shell=True,
        )
        paths.append((f"repos/{flatrepo}", flatrepo))
    return paths

@app.local_entrypoint()
def main():
    import datasets
    from swebench_modal.harness.test_spec import make_test_spec
    import os
    import subprocess

    data = datasets.load_dataset("princeton-nlp/SWE-bench_lite")

    repos = set(data["test"]["repo"])
    paths = clone_repos(repos)
    upload_repositories(volume, paths)
    import pdb; pdb.set_trace()


    # django__django-13315
    #example = data["test"][52]
    example = data["test"][33]
    test_spec = make_test_spec(example)
    import requests
    data = dict(
        repo=test_spec.repo,
        instance_image_key=test_spec.instance_image_key,
        env_image_key=test_spec.env_image_key,
        setup_env_script=test_spec.setup_env_script,
        install_repo_script=test_spec.install_repo_script,
        eval_script=test_spec.eval_script,
        diff="",
    )
    output = requests.post(os.getenv("SWEBENCHSERVER"), json=data, timeout=600.0)
    import pdb; pdb.set_trace()

if __name__ == "__main__":
    main()
