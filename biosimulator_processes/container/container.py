import json
import os
import subprocess
import tempfile
import docker










def exec_container(name: str):
    build_command = f"docker buildx build --platform linux/amd64 {name}_env ."
    subprocess.run(build_command.split())
    run_command = f"docker run --platform linux/amd64 -it -p 8888:8888 {name}_env"
    subprocess.run(run_command.split())





