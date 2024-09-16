#!/bin/bash

# take in two variables - RUN_LAMBDAS and RUN_RAILS_APP - by default both are true
RUN_LAMBDAS=${1:-true}
RUN_RAILS_APP=${2:-true}

### Run deployers and tests for lambdas ###
if [ "$RUN_LAMBDAS" = "true" ]; then
  echo "Running lambdas tests..."

  # activate venv if it exists and are not already in it
  if [ -d "venv" ] && [ -z "$VIRTUAL_ENV" ]; then
    source venv/bin/activate
  fi

  # cd into lambdas directory
  cd lambdas

  # set PYTHONPATH to current directory
  export PYTHONPATH=.

  # run stage deploy for each stage
  for stage in test development production; do
    echo "Deploying $stage stage..."
    ./deploy_stage.sh $stage
    echo "---------------------------"
  done

  # run cloud decoupled tests
  pytest tests/cloud_decoupled/

  # cd ../
  cd ../
else
  echo "Skipping lambdas tests..."
fi





#### Run tests for rails_app ####
if [ "$RUN_RAILS_APP" = "true" ]; then
  # cd into rails_app directory 
  cd rails_app

  # export path to gem
  export PATH="/usr/bin/bundler:$PATH"

  # bundle install
  bundle install

  # reset the test db
  RAILS_ENV=test rails db:reset

  # run test server in background
  RAILS_ENV=test ./bin/dev &
  PID=$!

  # run test script
  ./test/run_tests.sh

  # kill the test server
  kill $PID
else
  echo "Skipping rails_app tests..."
fi






