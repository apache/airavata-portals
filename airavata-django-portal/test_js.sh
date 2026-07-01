
# Get the directory that this script is in
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || exit 1

echo -e "Testing JS"
npm run test --workspace=django-airavata-api || exit 1
npm run test --workspace=admin-airavata || exit 1

echo -e "All testing finished successfully!"

exit 0
