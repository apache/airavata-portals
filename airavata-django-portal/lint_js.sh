
# Get the directory that this script is in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

echo -e "Linting JS"
npm run lint --workspace=django-airavata-api || exit 1
npm run lint --workspace=django-airavata-common-ui || exit 1
npm run lint --workspace=django-airavata-auth-views || exit 1
npm run lint --workspace=admin-airavata || exit 1
npm run lint --workspace=django-airavata-group-views || exit 1
npm run lint --workspace=django-airavata-workspace-plugin-api || exit 1
npm run lint --workspace=django-airavata-workspace-views || exit 1
npm run lint --workspace=django-airavata-dataparsers-views || exit 1

echo -e "All linting finished successfully!"

exit 0
