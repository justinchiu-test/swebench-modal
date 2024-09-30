import subprocess
import os

# List of repositories and their corresponding names
repos = {
    "repos/astropy__astropy": "astropy__astropy",
    "repos/mwaskom__seaborn": "mwaskom__seaborn",
    "repos/pydata__xarray": "pydata__xarray",
    "repos/scikit-learn__scikit-learn": "scikit-learn__scikit-learn",
    "repos/django__django": "django__django",
    "repos/pallets__flask": "pallets__flask",
    "repos/pylint-dev__pylint": "pylint-dev__pylint",
    "repos/sphinx-doc__sphinx": "sphinx-doc__sphinx",
    "repos/matplotlib__matplotlib": "matplotlib__matplotlib",
    "repos/psf__requests": "psf__requests",
    "repos/pytest-dev__pytest": "pytest-dev__pytest",
    "repos/sympy__sympy": "sympy__sympy"
}

# Function to create a tar.gz archive of a directory
def create_tar_gz(dir_path, tar_gz_name):
    try:
        subprocess.run(["tar", "-czf", tar_gz_name, "-C", os.path.dirname(dir_path), os.path.basename(dir_path)], check=True)
        print(f"Successfully created {tar_gz_name} from {dir_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating tar.gz for {dir_path}: {e}")

# Function to upload a tar.gz file to remote volume
def upload_tar_gz(tar_gz_name, dest_name):
    try:
        subprocess.run(["uv", "run", "modal", "volume", "put", "swebench-repos", tar_gz_name, dest_name], check=True)
        print(f"Successfully uploaded {tar_gz_name} as {dest_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error uploading {tar_gz_name}: {e}")

# Main function
def main():
    os.makedirs("repo_tars", exist_ok=True)
    for repo, repo_name in repos.items():
        tar_gz_name = f"repo_tars/{repo_name}.tar.gz"
        
        # Create the tar.gz archive
        create_tar_gz(repo, tar_gz_name)
        
        # Upload the tar.gz file to the remote volume
        upload_tar_gz(tar_gz_name, f"{repo_name}.tar.gz")
        
        # Optionally, delete the local tar.gz file after upload
        # os.remove(tar_gz_name)

if __name__ == "__main__":
    main()
