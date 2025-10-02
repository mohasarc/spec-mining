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

# Extract the repository name from the URL
TESTING_REPO_NAME=$(basename -s .git "$TESTING_REPO_URL")

# Create a new directory name by appending _Pyguin to the repository name
CLONE_DIR="${TESTING_REPO_NAME}_Pyguin"

# Set the PYNGUIN_DANGER_AWARE environment variable to true
export PYNGUIN_DANGER_AWARE=true

# Print the environment variable
echo "PYNGUIN_DANGER_AWARE: $PYNGUIN_DANGER_AWARE"

# Install Pynguin
pip install pynguin

# Create the directory if it does not exist
mkdir -p "$CLONE_DIR"

# Navigate to the project directory
cd "$CLONE_DIR" || { echo "Failed to enter directory $CLONE_DIR"; exit 1; }

# Clone the testing repository and checkout specific SHA if provided
if [ -n "$target_sha" ]; then
    git clone "$TESTING_REPO_URL" && cd "$(basename "$TESTING_REPO_URL" .git)" && git checkout "$target_sha" && cd .. || { echo "Failed to clone/checkout $TESTING_REPO_URL at $target_sha"; exit 1; }
else
    git clone "$TESTING_REPO_URL" || { echo "Failed to clone $TESTING_REPO_URL"; exit 1; }
fi

# Navigate to the testing project directory
cd "$TESTING_REPO_NAME" || { echo "Failed to enter directory $TESTING_REPO_NAME"; exit 1; }

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
pip install pandas

# Return to the main directory
cd ..

# Copy the pynguin_runner.py file from the parent directory to the cloned repository
cp ../pynguin_runner.py .

# Run tests with 5-hour timeout and save output
timeout -k 9 18000 python3 pynguin_runner.py "$PWD/$TESTING_REPO_NAME"

# Ensure results directory exists
mkdir -p $CLONE_DIR

# Copy test output to results directory
cp -r "${TESTING_REPO_NAME}/testgen" $CLONE_DIR/

# Archive results
zip -r "${CLONE_DIR}.zip" $CLONE_DIR
mv "${CLONE_DIR}.zip" ..

# Return to main directory
cd ..

# Clean up project directory
rm -rf "$CLONE_DIR"