#!/bin/bash

# Get the directory that this script is in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

# Ordered production build of the npm-workspaces packages. Dependencies are
# installed once at the workspace root (npm ci / npm install) by CI and the
# Docker build; this script only runs the builds. Order matters: api + common
# first (consumers import their source), and workspace-plugin-api before
# workspace (workspace depends on its built dist/).
echo -e "Running production JS builds"
npm run build --workspace=django-airavata-api || exit 1
npm run build --workspace=django-airavata-common-ui || exit 1
npm run build --workspace=admin-airavata || exit 1
npm run build --workspace=django-airavata-group-views || exit 1
npm run build --workspace=django-airavata-workspace-plugin-api || exit 1
npm run build --workspace=django-airavata-workspace-views || exit 1
npm run build --workspace=django-airavata-dataparsers-views || exit 1

echo -e "All builds finished successfully!"

exit 0
