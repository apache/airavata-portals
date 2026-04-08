#!/bin/bash
set -e
echo "Testing JS"
yarn workspaces run test
echo "All testing finished successfully!"
