#!/bin/bash

# Define the container and image names
CONTAINER_NAME=step_1_receiver
IMAGE_NAME=step_1_receiver

# Stop and remove the container if it is running
if [ $(docker ps -q -f name=$CONTAINER_NAME) ]; then
  docker container stop $CONTAINER_NAME
  echo container stopped $CONTAINER_NAME
fi

if [ $(docker ps -aq -f name=$CONTAINER_NAME) ]; then
  docker container rm $CONTAINER_NAME
  echo container removed $CONTAINER_NAME
fi

# Start a detached container
docker run -d --name $CONTAINER_NAME -v "$HOME/.aws:/root/.aws" -p 9000:8080 $IMAGE_NAME