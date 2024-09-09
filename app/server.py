import asyncio
import datasets
import modal
from pathlib import Path

from swebench_modal.harness.test_spec import get_test_specs_from_dataset
from swebench_modal.harness.constants import (
    BASE_IMAGE_BUILD_DIR,
    ENV_IMAGE_BUILD_DIR,
    INSTANCE_IMAGE_BUILD_DIR,
    MAP_REPO_VERSION_TO_SPECS,
)


def spawn_image(test_spec, vol):
    # dynamically setup swebench image
    image_name = test_spec.instance_image_key
    env_image_name = test_spec.env_image_key

    #dockerfile = test_spec.instance_dockerfile
    env_setup_script = test_spec.setup_env_script
    image_setup_script = test_spec.install_repo_script

    image_path = f"setup/{image_name.replace(':', '__')}"

    env_path = f"{image_path}/env.sh"
    install_path = f"{image_path}/install.sh"

    Path(image_path).mkdir(exist_ok=True, parents=True)

    with Path(env_path).open("w") as f:
        f.write(env_setup_script)
    with Path(install_path).open("w") as f:
        f.write(image_setup_script)

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
        .workdir("/testbed")
        .run_commands(
            "ls /",
            "/bin/bash /root/env.sh",
            "/bin/bash /root/install.sh",
        )
    )

    print("creating sandbox")
    sandbox = modal.Sandbox.create(
        "bash",
        "-c",
        #"while read line; do echo $line; done",
        "/opt/miniconda3/envs/testbed/bin/pytest -rA -vv -o console_output_style=classic --tb=no astropy/modeling/tests/test_separable.py::test_custom_model_separable",
        image=image,
    )
    # TODO: programatic pytest running
    return sandbox



async def main():
    data = datasets.load_dataset("princeton-nlp/SWE-bench_lite")
    specs = get_test_specs_from_dataset(data["test"])
    test_spec = specs[0]

    with modal.Volume.ephemeral() as vol:
        sb = spawn_image(test_spec, vol)
        await sb.wait.aio()
        stdout = await sb.stdout.read.aio()
        stderr = await sb.stderr.read.aio()
        print("stdout:", stdout)
        print("stderr:", stderr)

if __name__ == "__main__":
    asyncio.run(main())
