import subprocess
import os
OMICAIRN_STORE = os.environ.get("OMICAIRN_STORE")
if OMICAIRN_STORE is None:
    raise ValueError("OMICAIRN_STORE is not set")
env_path = os.path.join(OMICAIRN_STORE, "computation_env")
PIP = os.path.join(env_path, "bin", "pip")
REQUIREMENTS = "/omicairn/code_space/requirements.txt"


def analysis_requirements():
    with open(REQUIREMENTS, "r") as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line]
        lines.reverse()
        return lines


def create_environment():
    setup_subp = subprocess.Popen(["python3", "-m", "virtualenv", env_path])
    setup_subp.wait()


def install(package):
    install_subp = subprocess.Popen([PIP, "install", package])
    install_subp.wait()


if __name__ == "__main__":

    for package in analysis_requirements():
        install(package)
