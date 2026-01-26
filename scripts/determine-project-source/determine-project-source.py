import csv
import os
import sys

def get_script_dir():
    return os.path.dirname(os.path.abspath(__file__))

def load_source_keys(filepath):
    keys = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                owner = row.get('Owner', '').strip().lower()
                repo = row.get('Repository Name', '').strip().lower()
                if owner and repo:
                    keys.add((owner, repo))
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        sys.exit(1)
    return keys

def main():
    script_dir = get_script_dir()
    results_metadata_path = os.path.join(script_dir, 'results_metadata.csv')
    dependency_based_path = os.path.join(script_dir, 'dependency-based.csv')
    spec_based_path = os.path.join(script_dir, 'spec-based.csv')

    print("Loading source data...")
    dependency_keys = load_source_keys(dependency_based_path)
    spec_keys = load_source_keys(spec_based_path)
    
    print(f"Loaded {len(dependency_keys)} dependency-based projects.")
    print(f"Loaded {len(spec_keys)} spec-based projects.")

    updated_rows = []
    headers = []
    
    stats = {
        "Both": 0,
        "Dependency Based": 0,
        "Spec Based": 0,
        "Neither": 0
    }

    print("Processing results_metadata.csv...")
    try:
        with open(results_metadata_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if "Project Source" not in headers:
                headers.append("Project Source")
            
            for row in reader:
                owner = row.get('owner', '').strip().lower()
                repo = row.get('repo', '').strip().lower()
                
                key = (owner, repo)
                
                in_dependency = key in dependency_keys
                in_spec = key in spec_keys
                
                source = "Neither"
                if in_dependency and in_spec:
                    source = "Both"
                elif in_dependency:
                    source = "Dependency Based"
                elif in_spec:
                    source = "Spec Based"
                
                stats[source] += 1
                row["Project Source"] = source
                updated_rows.append(row)
                
    except FileNotFoundError:
        print(f"Error: File not found: {results_metadata_path}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading {results_metadata_path}: {e}")
        sys.exit(1)

    print("\nStatistics:")
    total = sum(stats.values())
    for category, count in stats.items():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {category}: {count} ({percentage:.2f}%)")
    print(f"  Total: {total}")

    print("\nWriting updated metadata...")
    try:
        with open(results_metadata_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(updated_rows)
        print("Done.")
    except Exception as e:
        print(f"Error writing updates: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
