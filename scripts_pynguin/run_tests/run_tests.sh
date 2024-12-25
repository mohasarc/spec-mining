#!/bin/bash

set -x

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "$1" ]; then
    echo "Error: No git repository provided."
    echo "Usage: ./run.sh <git_repo>"
    exit 1
fi

cd /tmp || exit

repo=$1
repo_name=$(basename "$repo" .git)

echo "Cloning the repository..."
git clone --depth 1 "$repo" 

cd "$repo_name" || exit

python3 -m venv venv
source venv/bin/activate

mkdir -p /tmp/helper

# get the repo user and repo name, separated by a -.
# e.g. github.com/mohasarc/spec-mining -> mohasarc-spec-mining
# repo_name_in_release=$(echo "$repo" | sed -E 's#.*/([^/]+)/([^/]+)#\1-\2#')

# at the moment, the repo name in the release is the same as the repo name
repo_name_in_release="$repo_name"

# Handling the .zip file for tests2_pynguin
zip_url="https://github.com/mohasarc/spec-mining/releases/download/generated-tests-2024-12-12/${repo_name_in_release}.zip"
zip_file="/tmp/helper/${repo_name}.zip"
extracted_dir="/tmp/helper/${repo_name}_extracted"

echo "Checking for zip file: $zip_url"
curl --head --silent --fail "$zip_url" > /dev/null
if [ $? -ne 0 ]; then
    echo "!!!Error: Zip file for repository ${repo_name} does not exist at $zip_url."
    exit 1
fi

echo "Downloading zip file..."
curl -L "$zip_url" -o "$zip_file"

echo "Extracting zip file..."
mkdir -p "$extracted_dir"
unzip "$zip_file" -d "$extracted_dir"

tests_dir=$(find "$extracted_dir" -type d -name "tests2_pynguin" | head -n 1)
if [ ! -d "$tests_dir" ]; then
    echo "!!!Error: tests2_pynguin directory not found in the extracted zip file."
    exit 1
fi

echo "Installing the dependencies..."

pip3 install .[dev,test,tests,testing]

# Install additional requirements if available (within root + 2 nest levels excluding env/ folder)
find . -maxdepth 3 -type d -name "env" -prune -o -type f -name "*.txt" -print | while read -r file; do
    if [ -f "$file" ]; then
        pip3 install -r "$file"
    fi
done
pip3 install pytest-json-report pytest-cov pytest-env pytest-rerunfailures pytest-socket pytest-django

echo "Dependencies installed."


destination_dir="/tmp/$repo_name/tests2_pynguin"
mkdir -p "$destination_dir"
cp -r "$tests_dir"/* "$destination_dir"

echo "Running coverage on tests2_pynguin..."
# echo $PWD
coverage run --source=. --branch -m pytest tests2_pynguin --continue-on-collection-errors --json-report --json-report-indent=2 > coverage_out_pynguin.txt
coverage json --ignore-errors --pretty-print

# /app just used in docker
# REPORT_DIR="/app"
REPORT_DIR="$HERE/"
BASEDIR=$REPORT_DIR/results/"$repo_name"
mkdir -p "$BASEDIR"
JSON_REPORT="$BASEDIR/coverage_out_pynguin.txt"
COVERAGE_REPORT="$BASEDIR/coverage_pynguin.json"

mv coverage_out_pynguin.txt "$JSON_REPORT"
mv coverage.json "$COVERAGE_REPORT"
rm .coverage

echo "********"
ls -la
echo "********"

### Run coverage without tests2_pynguin
echo "Running coverage on all Python modules..."
cd /tmp/"$repo_name" || exit
mv tests2_pynguin /tmp/helper/tests2_pynguin_disabled
coverage run --source=. --branch -m pytest --continue-on-collection-errors --json-report --json-report-indent=2 > coverage_out.txt
coverage json --ignore-errors --pretty-print

JSON_REPORT="$BASEDIR/coverage_out.txt"
COVERAGE_REPORT="$BASEDIR/coverage.json"
mv coverage_out.txt "$JSON_REPORT"
mv coverage.json "$COVERAGE_REPORT"
rm .coverage


### run coverage on tests2_pynguin and normal tests
echo "Combining coverage reports..."
mv /tmp/helper/tests2_pynguin_disabled tests2_pynguin
coverage run --source=. --branch -m pytest --continue-on-collection-errors --json-report --json-report-indent=2 > coverage_out_both.txt
coverage json --ignore-errors --pretty-print

JSON_REPORT="$BASEDIR/coverage_out_both.txt"
COVERAGE_REPORT="$BASEDIR/coverage_both.json"
mv coverage_out_both.txt "$JSON_REPORT"
mv coverage.json "$COVERAGE_REPORT"
rm .coverage

rm -rf /tmp/helper

deactivate