import pytest
import os
from tests.utilities.execute_subprocess import execute_subprocess_command

current_directory = os.getcwd()

STAGE = os.environ.get("STAGE", "development")

receivers = ["receiver_start"]
docker_images = receivers


@pytest.mark.parametrize("IMAGE_NAME", docker_images)
def test_deploy_image(IMAGE_NAME):
    # deploy image
    command = ["bash", "deploy_image.sh", STAGE, IMAGE_NAME]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
