
import os
from tests.utilities.execute_subprocess import execute_subprocess_command
current_directory = os.getcwd()


def deploy_receives(stage: str = "development"):
    # receiver list
    receivers = ["receiver_start", "receiver_preprocess", "receiver_process", "receiver_end"]
 
    # build and deploy image for each receiver
    for receiver_name in receivers:
        # build image
        command = ["bash", "build_image.sh", stage, receiver_name]
        stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")

        # deploy image
        command = ["bash", "deploy_image.sh", stage, receiver_name]
        stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")

    # deploy serverless config for receivers
    config = "serverless_receivers.yml"
    command = ["bash", "adjust_functions.sh", "deploy", stage, config]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas")