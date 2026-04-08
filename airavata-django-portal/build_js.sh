#!/bin/bash
set -e
echo "Running production JS builds"
yarn workspaces run build
echo "All builds finished successfully!"
