import os
import sys
import subprocess


# maximum search time in seconds
MAXIMUM_SEARCH_TIME = 120


def find_project_folder(project_path, project_name):
    """Find the actual project folder name regardless of case."""
    # Look for case-insensitive match as the module name need to be matched exactly for pynguin test generation
    for item in os.listdir(project_path):
        if item.lower() == project_name.lower() and os.path.isdir(os.path.join(project_path, item)):
            return item
    
    return None

def detect_python_files(project_path):
    python_files = []
    # Ignore common artifact and cache directories
    ignored_dir_names = {
        "build",
        "dist",
        "build.lib",
        "__pycache__",
        ".eggs",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".nox",
        ".venv",
        "venv",
        "env",
        ".env",
        ".git",
        ".idea",
        ".vscode",
    }
    

    # Find the project name and the actual project folder name
    project_name = os.path.basename(os.path.normpath(project_path))
    actual_project_folder = find_project_folder(project_path, project_name)

    # If the actual project folder is not found, scan the main directory instead
    if actual_project_folder is None:
        project_folder_status = False
        print(f"No specific project folder found inside {project_path}, scanning the main directory instead.")
        project_src_path = project_path
    else:
        # Get the actual project folder path
        project_folder_status = True
        project_src_path = os.path.join(project_path, actual_project_folder)

    for root, dirnames, files in os.walk(project_src_path):
        # Prune artifact/cache directories from traversal
        dirnames[:] = [
            d for d in dirnames
            if d not in ignored_dir_names and not d.endswith(".egg-info")
        ]
        for file in files:
            if file.endswith(".py") and not file.startswith("_") and not file.startswith("__") and not file.startswith("test") and not file.startswith("tests"):
                # Get the relative path from the project root
                rel_path = os.path.relpath(root, project_src_path)
                # Convert path to module notation
                if rel_path == ".":
                    # If the project folder is found, use the actual project folder name
                    if project_folder_status:
                        module_path = f"{actual_project_folder}.{file[:-3]}"
                    # If the project folder is not found, use the main directory
                    else:
                        module_path = file[:-3]  # Remove .py extension
                else:
                    # If the project folder is found, use the actual project folder name
                    if project_folder_status:
                        module_path = f"{actual_project_folder}.{rel_path.replace(os.sep, '.')}.{file[:-3]}"
                    # If the project folder is not found, use the main directory
                    else:
                        module_path = f"{rel_path.replace(os.sep, '.')}.{file[:-3]}"
                python_files.append(module_path)
    
    return python_files

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python pynguin_runner.py <project_path>")
        sys.exit(1)
        
    project_path = sys.argv[1]
    if not os.path.isdir(project_path):
        print("Invalid directory. Please enter a valid project path.")
        sys.exit(1)
    else:
        # Get the project name
        project_name = os.path.basename(os.path.normpath(project_path))

        # Detect the Python files in the project folder to be test generated
        python_files = detect_python_files(project_path)
            
        print(f"Detected {len(python_files)} Python files in Project {project_name}.")
        print("\nDetected Python project modules:")
        for file in python_files:
            print(file)

        print("================================================")
        
        # Run Pynguin on each module of the project
        for i, module_name in enumerate(python_files):
            print(f"Running Pynguin on {module_name} of Project {project_name}...")
            print(f"Total number of modules: {len(python_files)}; Remaining modules: {len(python_files) - i}")
            
            # Create output directory path
            output_path = os.path.join(project_path, "testgen")
            
            # Create the command to run Pynguin
            command = (
                f"pynguin --project-path {project_path} "
                f"--maximum-search-time {MAXIMUM_SEARCH_TIME} "
                f"--output-path {output_path} "
                f"--module-name {module_name} "
                f"-v --assertion-generation SIMPLE"
            )
            subprocess.run(command, shell=True)

            print("================================================")

        print("All Pynguin tests have been generated.")
        exit(0)
