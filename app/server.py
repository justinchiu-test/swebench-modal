import modal
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


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


@app.function()
def run_tests(test_spec):
    import subprocess

    # dynamically setup swebench image
    image_name = test_spec.instance_image_key
    env_image_name = test_spec.env_image_key

    #dockerfile = test_spec.instance_dockerfile
    env_setup_script = test_spec.setup_env_script
    image_setup_script = test_spec.install_repo_script
    eval_script = test_spec.eval_script

    image_path = "/root"
    env_path = f"{image_path}/env.sh"
    install_path = f"{image_path}/install.sh"
    eval_path = f"{image_path}/eval.sh"

    Path(image_path).mkdir(exist_ok=True, parents=True)

    env_output = subprocess.check_output(
        "/bin/bash /root/env.sh",
        stderr=subprocess.STDOUT,
        shell=True,
    )
    install_output = subprocess.run(
        "/bin/bash /root/install.sh",
        stderr=subprocess.STDOUT,
        shell=True
    )

    output = subprocess.check_output(
        "/bin/bash /root/eval.sh",
        stderr=subprocess.STDOUT,
        shell=True,
    )
    end_time = time.time()
    return output, end_time-start_time, env_output, install_output


def main():
    data = datasets.load_dataset("princeton-nlp/SWE-bench_lite")
    example = data["test"][0]
    test_spec = make_test_spec(example)
    #import pdb; pdb.set_trace()

    out, duration, env_out, install_out = run_tests(test_spec)
    print("out:", out)

