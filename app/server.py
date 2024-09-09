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


data = datasets.load_dataset("princeton-nlp/SWE-bench_lite")
specs = get_test_specs_from_dataset(data["test"])

test_spec = specs[0]

image_name = test_spec.instance_image_key
env_image_name = test_spec.env_image_key

dockerfile = test_spec.instance_dockerfile
env_setup_script = test_spec.setup_env_script
image_setup_script = test_spec.install_repo_script

image_path = image_name.replace(":", "__")

dockerfile_path = f"{image_path}/dockerfile"
env_path = f"{image_path}/env.sh"
install_path = f"{image_path}/install.sh"

Path(image_path).mkdir(exist_ok=True)

with Path(dockerfile_path).open("w") as f:
with Path(env_path).open("w") as f:
    f.write(env_setup_script)
with Path(install_path).open("w") as f:
    f.write(imag_setup_script)


image = (modal.Image.from_dockerfile(dockerfile_path, add_python="3.9")
    .copy_local_file(env_setup_script, "/root/env.sh")
    .copy_local_file(image_setup_script, "/root/install.sh")
    .run_commands(
        "/bin/bash /root/env.sh",
        "/bin/bash /root/install.sh",
    )
)


