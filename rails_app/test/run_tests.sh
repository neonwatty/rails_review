#!/bin/bash

# run model tests
echo "Running model tests..."
bin/rails test test/models/*
echo "Finished!"
echo "---------------------------"

# run integration tests
echo "Running integration tests..."
bin/rails test test/integration/*
echo "Finished!"
echo "---------------------------"

# run controller tests
echo "Running controller tests..."
for file in test/controllers/*.rb; do
  echo "Running tests in $file"
  rails test "$file"
  echo "Finished running tests in $file"
  echo "---------------------------"
done