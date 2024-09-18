import asyncio
import modal

#image_path = f"setup/sweb.eval.x86_64.astropy__astropy-12907__latest"
image_path = f"setup/sweb.eval.x86_64.django__django-11049__latest"

env_path = f"{image_path}/env.sh"
install_path = f"{image_path}/install.sh"
diff_path = f"{image_path}/diff"

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
    .copy_local_file(diff_path, "/root/diff")
    .workdir("/testbed")
    .run_commands(
        "ls /",
        "/bin/bash /root/env.sh",
        "/bin/bash /root/install.sh",
        "git apply -v /root/diff",
    )
)

app = modal.App("swebench-rpc")

@app.function(image=image)
def stuff():
    import os
    print(os.getcwd())
    print(os.listdir("/root"))
    print(os.listdir("/bin"))
    print(os.listdir("/testbed"))

    import subprocess
    print(subprocess.check_output("which python".split()))
    print(subprocess.check_output("ls /opt/miniconda3/envs/testbed/bin".split()))

@app.local_entrypoint()
def main():
    stuff.remote()

