#!/bin/bash
set -e
echo "Linting JS"
yarn workspaces run lint
echo "All linting finished successfully!"
