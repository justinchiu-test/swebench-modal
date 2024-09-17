import asyncio
import datasets
import modal
from pathlib import Path
import time

from swebench_modal.harness.test_spec import make_test_spec
from swebench_modal.harness.constants import (
    BASE_IMAGE_BUILD_DIR,
    ENV_IMAGE_BUILD_DIR,
    INSTANCE_IMAGE_BUILD_DIR,
    MAP_REPO_VERSION_TO_SPECS,
)


app = modal.App()

def read_stream(stream):
    return "\n".join(line for line in stream)

def run_tests(test_spec):
    # dynamically setup swebench image
    image_name = test_spec.instance_image_key
    env_image_name = test_spec.env_image_key

    #dockerfile = test_spec.instance_dockerfile
    env_setup_script = test_spec.setup_env_script
    image_setup_script = test_spec.install_repo_script
    eval_script = test_spec.eval_script

    image_path = f"setup/{image_name.replace(':', '__')}"

    env_path = f"{image_path}/env.sh"
    install_path = f"{image_path}/install.sh"
    eval_path = f"{image_path}/eval.sh"

    Path(image_path).mkdir(exist_ok=True, parents=True)

    with Path(env_path).open("w") as f:
        f.write(env_setup_script)
    with Path(install_path).open("w") as f:
        f.write(image_setup_script)
    with Path(eval_path).open("w") as f:
        f.write(eval_script)

    image = (modal.Image
        .debian_slim(python_version="3.11")
        .apt_install("wget", "git", "build-essential", "libffi-dev", "libtiff-dev", "python3", "python3-pip", "python-is-python3", "jq", "curl", "locales", "locales-all", "tzdata")
        .run_commands(
            # modified wget to always do x86
            "wget 'https://repo.anaconda.com/miniconda/Miniconda3-py311_23.11.0-2-Linux-x86_64.sh' -O miniconda.sh",
            "bash miniconda.sh -b -p /opt/miniconda3",
        )
        .workdir("/root")
        .copy_local_file(env_path, "/root/env.sh")
        .copy_local_file(install_path, "/root/install.sh")
        .copy_local_file(eval_path, "/root/eval.sh")
        .workdir("/testbed")
        .run_commands(
            "ls /",
            "/bin/bash /root/env.sh",
            "/bin/bash /root/install.sh",
        )
    )

    print("creating sandbox")
    start_time = time.time()
    sandbox = modal.Sandbox.create(
        "bash",
        "-c",
        #"while read line; do echo $line; done",
        #"/opt/miniconda3/envs/testbed/bin/pytest -rA -vv -o console_output_style=classic --tb=no astropy/modeling/tests/test_separable.py::test_custom_model_separable",
        "/bin/bash /root/eval.sh",
        image=image,
        app=app,
        timeout=600, # 10 minutes
    ) 
    sandbox.wait()
    stdout = read_stream(sandbox.stdout)
    stderr = read_stream(sandbox.stderr)
    end_time = time.time()
    return stdout, stderr, end_time-start_time


def main():
    data = datasets.load_dataset("princeton-nlp/SWE-bench_lite")
    example = data["test"][0]
    test_spec = make_test_spec(example)
    #import pdb; pdb.set_trace()

    stdout, stderr = run_tests(test_spec)
    print("stdout:", stdout)
    print("stderr:", stderr)


if __name__ == "__main__":
    main()
