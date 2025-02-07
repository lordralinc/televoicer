
PROJECT_NAME=$(awk -F' *= *' '/\[project\]/,/^$/ {if ($1 == "name") {gsub(/["\047]/, "", $2); print $2}}' pyproject.toml)
PROJECT_VERSION=$(awk -F' *= *' '/\[project\]/,/^$/ {if ($1 == "version") {gsub(/["\047]/, "", $2); print $2}}' pyproject.toml)
AUTHOR_NAME=$(grep -A2 'authors' pyproject.toml | grep 'name' | head -n1 | awk -F'"' '{print $2}')

echo "name=${PROJECT_NAME} v=${PROJECT_VERSION} author=${AUTHOR_NAME}"


if [[ $1 == "extract" ]]; then
    pybabel extract --input-dirs=. -o locales/messages.pot --sort-by-file --copyright-holder="${AUTHOR_NAME}" --project="${PROJECT_NAME}" --version "${PROJECT_VERSION}"
fi
if [[ $1 == "update" ]]; then
    pybabel update -d locales -D messages -i locales/messages.pot
fi
if [[ $1 == "compile" ]]; then
    pybabel compile -d locales -D messages
fi