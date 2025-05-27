#!/bin/bash

# Check if exactly one repository URL is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <testing-repo-url>"
    exit 1
fi

# Assign the provided repository URL with SHA to a variable
repo_url_with_sha="$1"

# Split the input into repository URL and SHA
IFS=';' read -r TESTING_REPO_URL target_sha <<< "$repo_url_with_sha"

# Output the URL and SHA
echo "Url: $TESTING_REPO_URL"
echo "Sha: $target_sha"

# Set the temporary directory to /tmp
TMPDIR=/tmp
echo "TMPDIR: $TMPDIR"

# Define the fixed repository URL for the DyLin project
DYLIN_REPO_URL="https://github.com/AryazE/DyLin.git"

# Extract the repository name from the URL
TESTING_REPO_NAME=$(basename -s .git "$TESTING_REPO_URL")

# Extract the developer ID from the URL
DEVELOPER_ID=$(echo "$TESTING_REPO_URL" | sed -E 's|https://github.com/([^/]+)/.*|\1|')

# Create combined name with developer ID and repo name
CLONE_DIR="${DEVELOPER_ID}-${TESTING_REPO_NAME}_Dylin_Libs"

# Create the directory if it does not exist
mkdir -p "$CLONE_DIR"

# Navigate to the project directory
cd "$CLONE_DIR" || { echo "Failed to enter directory $CLONE_DIR"; exit 1; }

# ------------------------------------------------------------------------------------------------
# Install the testing repository
# ------------------------------------------------------------------------------------------------

# Clone the testing repository and checkout specific SHA if provided
if [ -n "$target_sha" ]; then
    git clone "$TESTING_REPO_URL" && cd "$(basename "$TESTING_REPO_URL" .git)" && git checkout "$target_sha" && cd .. || { echo "Failed to clone/checkout $TESTING_REPO_URL at $target_sha"; exit 1; }
else
    git clone "$TESTING_REPO_URL" || { echo "Failed to clone $TESTING_REPO_URL"; exit 1; }
fi

# Navigate to the testing project directory
cd "$TESTING_REPO_NAME" || { echo "Failed to enter directory $TESTING_REPO_NAME"; exit 1; }

# Create a virtual environment using Python's built-in venv
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies from all requirement files if they exist
for file in *.txt; do
    if [ -f "$file" ]; then
        pip install -r "$file"
    fi
done

# Install the package with test dependencies using custom install script if available
if [ -f myInstall.sh ]; then
    bash ./myInstall.sh
else
    pip install .[dev,test,tests,testing]
fi

# Install required Python packages
pip install pytest
pip install numpy
pip install matplotlib
pip install pandas
pip install memray pytest-memray

# ------------------------------------------------------------------------------------------------
# Install DyLin in the global environment and run the Instrumentation
# ------------------------------------------------------------------------------------------------

# Exit the virtual environment
deactivate

# Navigate back to the parent directory
cd ..

# Clone the DyLin repository into the current directory
git clone "$DYLIN_REPO_URL" "$(basename $DYLIN_REPO_URL .git)_global" || { echo "Failed to clone $DYLIN_REPO_URL"; exit 1; }

# Specify the source directory containing the Python DyLin files
SOURCE_DIR="$PWD/../Specs_libs/DyLin"

# Define the destination directory in the cloned DyLin repository
DESTINATION_DIR="$PWD/DyLin_global/src/dylin/analyses"

# Remove everything at the destination directory apart from base_analysis.py and __init__.py
find "$DESTINATION_DIR" -type f ! -name 'base_analysis.py' ! -name '__init__.py' -delete

# Check if the source directory exists before attempting to copy files
if [ -d "$SOURCE_DIR" ]; then
    # Copy all Python files from the source directory to the destination
    cp "$SOURCE_DIR"/*.py "$DESTINATION_DIR"
else
    echo "Source directory does not exist: $SOURCE_DIR"
    exit 1
fi

# Override the select_checkers.py file with the one from the parent directory
cp "$PWD/../Specs_libs/select_checkers.py" "$PWD/DyLin_global/src/dylin/select_checkers.py"

# Navigate into the cloned DyLin repository
cd "$(basename $DYLIN_REPO_URL .git)_global"

# Install the required dependencies for DyLin and the package itself
pip install -r requirements.txt
pip install .

# Go back to the parent directory
cd ..

# Generate a unique session ID for the DynaPyt run (in order to run multiple analyses in one run)
export DYNAPYT_SESSION_ID=$(uuidgen)
echo "DynaPyt Session ID: $DYNAPYT_SESSION_ID"

# --- STEP 4: Remove DyLin files ---
echo "[INFO] Removing DyLin source files..."
rm -rf ./DyLin_global

# --- STEP 5: Select analyses ---
echo "[INFO] Selecting analyses..."
python3 -m dylin.select_checkers \
    --include="All" \
    --exclude="None" \
    --output_dir="${TMPDIR}/dynapyt_output-${DYNAPYT_SESSION_ID}" > analyses.txt

echo "[INFO] Selected analyses:"
cat analyses.txt

# --- STEP 6: Copy analyses file ---
cp analyses.txt "${TMPDIR}/dynapyt_analyses-${DYNAPYT_SESSION_ID}.txt"

# Copy the file_to_instrument_generators.py file to the temp directory
cp "$PWD/../file_to_instrument_generators.py" "$PWD/file_to_instrument_generators.py"

# Generate the file list for files to be instrumented including libraries
python3 "$PWD/file_to_instrument_generators.py" "$TESTING_REPO_NAME" "venv"

# Go back to the testing project directory
cd "$TESTING_REPO_NAME"

# Record the start time of the instrumentation process
START_TIME=$(python3 -c 'import time; print(time.time())')

# Read the analyses file and join with commas
ANALYSES=$(cat "${TMPDIR}/dynapyt_analyses-${DYNAPYT_SESSION_ID}.txt" | tr '\n' ',' | sed 's/,$//')

# Run DynaPyt instrumentation for analysis
python3 -m dynapyt.instrument.instrument --files ../files_to_instrument.txt --analysis "$ANALYSES"

# Record the end time and calculate the instrumentation duration
END_TIME=$(python3 -c 'import time; print(time.time())')
INSTRUMENTATION_TIME=$(python3 -c "print($END_TIME - $START_TIME)")

# Add debug message after instrumentation
echo "=== Instrumentation Complete (${INSTRUMENTATION_TIME}s) ==="

# ------------------------------------------------------------------------------------------------
# Install DynaPyt in the virtual environment and run the tests
# ------------------------------------------------------------------------------------------------

# Activate the virtual environment
source venv/bin/activate

# Return to the parent directory
cd ..

# Clone the DyLin repository into the current directory
git clone "$DYLIN_REPO_URL" "$(basename $DYLIN_REPO_URL .git)_virtual" || { echo "Failed to clone $DYLIN_REPO_URL"; exit 1; }

# Specify the source directory containing the Python DyLin files
SOURCE_DIR="$PWD/../Specs_libs/DyLin"

# Define the destination directory in the cloned DyLin repository
DESTINATION_DIR="$PWD/DyLin_virtual/src/dylin/analyses"

# Remove everything at the destination directory apart from base_analysis.py and __init__.py
find "$DESTINATION_DIR" -type f ! -name 'base_analysis.py' ! -name '__init__.py' -delete

# Check if the source directory exists before attempting to copy files
if [ -d "$SOURCE_DIR" ]; then
    # Copy all Python files from the source directory to the destination
    cp "$SOURCE_DIR"/*.py "$DESTINATION_DIR"
else
    echo "Source directory does not exist: $SOURCE_DIR"
    exit 1
fi

# Override the select_checkers.py file with the one from the parent directory
cp "$PWD/../Specs_libs/select_checkers.py" "$PWD/DyLin_virtual/src/dylin/select_checkers.py"

# Navigate into the cloned DyLin repository
cd "$(basename $DYLIN_REPO_URL .git)_virtual"

# Install the required dependencies for DyLin and the package itself
pip install -r requirements.txt
pip install .

# Navigate back to the root project directory
cd ..

# ------------------------------------------------------------------------------------------------
# Run the tests
# ------------------------------------------------------------------------------------------------

# Navigate to the testing project directory
cd "$TESTING_REPO_NAME"

MEMORY_DATA_DIR_NAME="memory-data-dylin-libs"

# Record test start time
TEST_START_TIME=$(python3 -c 'import time; print(time.time())')

# Run tests with 1-hour timeout and save output
timeout -k 9 3000 pytest --memray --trace-python-allocators --most-allocations=0 --memray-bin-path=./$MEMORY_DATA_DIR_NAME --continue-on-collection-errors > ${TESTING_REPO_NAME}_Output.txt
exit_code=$?

# Process test results if no timeout occurred
if [ $exit_code -ne 124 ] && [ $exit_code -ne 137 ]; then
    # Calculate test duration
    TEST_END_TIME=$(python3 -c 'import time; print(time.time())')
    TEST_TIME=$(python3 -c "print($TEST_END_TIME - $TEST_START_TIME)")

    # Show test summary
    tail -n 3 ${TESTING_REPO_NAME}_Output.txt
else
    echo "Timeout occurred"
    TEST_TIME="Timeout"
fi

# --- STEP 9: Generate findings report (no coverage) ---

echo "[INFO] Running post_run without coverage collection..."

# Record Post-Run start time
POST_RUN_START_TIME=$(python3 -c 'import time; print(time.time())')

python3 -m dynapyt.post_run \
    --coverage_dir="" \
    --output_dir="${TMPDIR}/dynapyt_output-${DYNAPYT_SESSION_ID}"

python3 -m dylin.format_output \
    --findings_path="${TMPDIR}/dynapyt_output-${DYNAPYT_SESSION_ID}/output.json" > ${TESTING_REPO_NAME}_findings.txt

# Record Post-Run end time
POST_RUN_END_TIME=$(python3 -c 'import time; print(time.time())')
POST_RUN_TIME=$(python3 -c "print($POST_RUN_END_TIME - $POST_RUN_START_TIME)")

# --- STEP 10: Store results ---
# Return to parent directory
cd ..

# Clean up virtual environment
deactivate
rm -rf venv

# Ensure results directory exists
mkdir -p $CLONE_DIR

# Save test results
RESULTS_FILE="${CLONE_DIR}/${TESTING_REPO_NAME}_results.txt"
echo "Instrumentation Time: ${INSTRUMENTATION_TIME}s" >> $RESULTS_FILE
echo "Test Time: ${TEST_TIME}s" >> $RESULTS_FILE
echo "Post-Run Time: ${POST_RUN_TIME}s" >> $RESULTS_FILE

# Copy the ${TESTING_REPO_NAME}_findings.txt file to the $CLONE_DIR directory
cp "${TESTING_REPO_NAME}/${TESTING_REPO_NAME}_findings.txt" $CLONE_DIR/

# Copy the ${TESTING_REPO_NAME}_Output.txt file to the $CLONE_DIR directory
cp "${TESTING_REPO_NAME}/${TESTING_REPO_NAME}_Output.txt" $CLONE_DIR/

# Copy the /tmp/dynapyt_output-454852b3-74be-498a-8968-c1bceaaf3293/findings.csv and output.json files to the $CLONE_DIR directory
# Rename them to temp_findings.csv and temp_output.json
cp "${TMPDIR}/dynapyt_output-${DYNAPYT_SESSION_ID}/findings.csv" $CLONE_DIR/temp_findings.csv
cp "${TMPDIR}/dynapyt_output-${DYNAPYT_SESSION_ID}/output.json" $CLONE_DIR/temp_output.json

# Copy the memory data to the results directory
cp $TESTING_REPO_NAME/$MEMORY_DATA_DIR_NAME/* $CLONE_DIR/$MEMORY_DATA_DIR_NAME/

# Archive results
zip -r "${CLONE_DIR}.zip" $CLONE_DIR
mv "${CLONE_DIR}.zip" ..

# Return to main directory
cd ..

# Clean up project directory
rm -rf "$CLONE_DIR"

echo "[INFO] All done."