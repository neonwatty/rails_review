import docker
import re
import os
import time
from tests.utilities.execute_subprocess import execute_subprocess_command


# get current directory paths
current_directory = os.getcwd()
home_dir = os.path.expanduser("~")

# Initialize Docker client
client = docker.from_env()

# controller for building lambda image locally, and running / stopping / removing container
def local_controller(STAGE: str, RECEIVER_NAME: str, DOCKER_PORT: str):
    # build image
    print("INFO: starting image building process...")
    command = ["bash", "build_image.sh", STAGE, RECEIVER_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
    print("INFO: ...complete!")
    
    # startup container
    command = [
        "docker",
        "run",
        "--env-file",
        "../.env",
        "-e", "STAGE=test",
        "-e", f"RECEIVER_NAME={RECEIVER_NAME}",
        "-d",
        "-v",
        f"{home_dir}/.aws:/root/.aws",
        "--name",
        RECEIVER_NAME,
        "-p",
        f"{DOCKER_PORT}:8080",
        RECEIVER_NAME,
    ]
    print("INFO: starting container running process...")
    stdout = execute_subprocess_command(command)
    print("INFO: ...complete!")

    # let container startup before sending post tests
    time.sleep(5)

    yield

    # stop and remove container
    command = ["docker", "stop", RECEIVER_NAME]
    print("INFO: starting container stopping process...")
    stdout = execute_subprocess_command(command)
    print("INFO: ...complete!")

    command = ["docker", "rm", RECEIVER_NAME]
    print("INFO: starting container removal process...")
    stdout = execute_subprocess_command(command)
    print("INFO: ...complete!")


def print_container_logs(container_name: str) -> None:
    # Fetch the container
    container = client.containers.get(container_name)

    # Retrieve logs from the container
    logs = container.logs(stdout=True, stderr=True, tail=100).decode('utf-8')
    
    # Define a regex pattern to match lines with timestamps
    timestamp_pattern = re.compile(r'^\d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2},\d{3}', re.MULTILINE)

    # Define patterns to exclude lines containing specific keywords
    exclude_patterns = re.compile(r'(START RequestId|END RequestId|REPORT RequestId)', re.MULTILINE)

    # Filter out lines that start with timestamps or contain specific keywords
    filtered_logs = '\n'.join(
        line for line in logs.splitlines()
        if not (timestamp_pattern.match(line) or exclude_patterns.search(line))
)
    print(filtered_logs)