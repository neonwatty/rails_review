
import os
import sys
import argparse
from tests.utilities.execute_subprocess import execute_subprocess_command
current_directory = os.getcwd()

stages = ["test", "test-decoupled", "development", "production"]


def deploy_receives(stage: str = "development"):
    # receiver list
    receivers = ["receiver_start", "receiver_preprocess", "receiver_process", "receiver_end", "receiver_status"]
 
    # build and deploy image for each receiver
    for receiver_name in receivers:
        # build image
        print(f"INFO: building image for receiver {receiver_name}")
        command = ["bash", "build_image.sh", stage, receiver_name]
        stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
        print("INFO: ...done!")

        # deploy image
        print(f"INFO: deploying image for receiver {receiver_name} and stage {stage}")
        command = ["bash", "deploy_image.sh", stage, receiver_name]
        stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas/build_deploy_scripts")
        print("INFO: ...done!")

    # deploy serverless config for receivers
    config = "serverless_receivers.yml"
    print(f"INFO: deploying services in {config} to stage {stage}")
    command = ["bash", "adjust_functions.sh", "deploy", stage, config]
    stdout = execute_subprocess_command(command, cwd=current_directory + "/lambdas")
    print("INFO: ...done!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument('stage', type=str, help='stage argument - development, test, or production')
    args = parser.parse_args()
    if args.stage not in stages:
        print(f"FAILURE: input stage {args.stage} - available stages are {stages}")
    deploy_receives(args.stage)
