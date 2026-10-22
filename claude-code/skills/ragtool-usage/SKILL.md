# ragtool - OmiCairn Runtime Utility Tool

## Overview

`ragtool` is a core utility in OmiCairn Python Job v2 containers for accessing upstream node data files and retrieving parent node information at runtime. It optimizes memory usage and startup time through on-demand file loading from S3.

## Core Capabilities

1. **On-Demand File Loading** - Dynamically download output files from upstream nodes from S3
2. **Parent Node Access** - Access the complete output folder of the parent node

## Command Reference

### 1. load_file - On-Demand Input File Loading

Load files from upstream nodes on-demand to a local temporary directory. This is the **recommended approach** for accessing input data.

#### Command Syntax

```bash
ragtool load_file <node_key> <relative_path>
```

**Parameters:**
- `node_key`: Node identifier in format `node_1`, `node_2`, etc.
- `relative_path`: Relative path of the file within that node

**Returns:**
- Success: Outputs absolute path of the local file (stdout)
- Failure: Outputs error message (stderr) and non-zero exit code

#### Use Cases

- ✅ When you know which specific file you need
- ✅ Handling large files, avoiding full downloads
- ✅ On-demand loading saves memory and time
- ✅ Supports caching - repeated calls won't re-download

#### Bash Examples

```bash
#!/bin/bash

# Basic usage
file_path=$(ragtool load_file node_1 processed_data.h5ad)
echo "File downloaded to: $file_path"

# Error handling
if file_path=$(ragtool load_file node_2 counts.rds 2>&1); then
    echo "Successfully loaded: $file_path"
    Rscript analysis.R "$file_path"
else
    echo "Failed to load file: $file_path"
    exit 1
fi

# Loading multiple files
data_file=$(ragtool load_file node_1 data.h5ad)
metadata_file=$(ragtool load_file node_1 metadata.csv)

python3 analysis.py --data "$data_file" --metadata "$metadata_file"
```

#### Python Examples

```python
import subprocess
import sys

# Basic usage
def load_input_file(node_key, relative_path):
    """Load file from upstream node"""
    result = subprocess.run(
        ['ragtool', 'load_file', node_key, relative_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"Error loading file: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    
    return result.stdout.strip()

# Usage example
h5ad_path = load_input_file('node_1', 'processed_data.h5ad')
print(f"File loaded at: {h5ad_path}")

# Process with scanpy
import scanpy as sc
adata = sc.read_h5ad(h5ad_path)
print(f"Loaded AnnData with {adata.n_obs} cells and {adata.n_vars} genes")

# Load multiple files
files_to_load = [
    ('node_1', 'counts.h5ad'),
    ('node_1', 'metadata.csv'),
    ('node_2', 'markers.csv')
]

for node_key, path in files_to_load:
    local_path = load_input_file(node_key, path)
    print(f"{path} -> {local_path}")
```

#### R Examples

```r
# Basic usage
load_input_file <- function(node_key, relative_path) {
  result <- system2(
    'ragtool',
    args = c('load_file', node_key, relative_path),
    stdout = TRUE,
    stderr = TRUE
  )
  
  if (!is.null(attr(result, "status")) && attr(result, "status") != 0) {
    stop("Failed to load file: ", paste(result, collapse = "\n"))
  }
  
  return(trimws(result[1]))
}

# Usage example
rds_path <- load_input_file('node_1', 'seurat_object.rds')
cat("File loaded at:", rds_path, "\n")

# Read Seurat object
library(Seurat)
seurat_obj <- readRDS(rds_path)
print(seurat_obj)

# Load multiple files
data_path <- load_input_file('node_1', 'data.rds')
markers_path <- load_input_file('node_2', 'markers.csv')

data <- readRDS(data_path)
markers <- read.csv(markers_path)
```

#### Important Notes

- ⚠️ Files are cached; repeated calls return the same local path
- ⚠️ Temporary files are stored in `/tmp` directory and lost on container restart
- ⚠️ Relative path must match the path when the file was output by upstream node
- ⚠️ Ensure sufficient disk space for downloaded files

---

### 2. get_parent_node_folder - Get Parent Node Folder

Get the complete output folder path of the direct parent node (highest index node). Downloads all files from that node to a local temporary directory.

#### Command Syntax

```bash
ragtool get_parent_node_folder
```

**Returns:**
- Outputs the local absolute path of the parent node folder

#### Use Cases

- ✅ When you need to access **all files** from the parent node
- ✅ Parent node outputs multiple related files that need to be processed together
- ❌ **Not recommended** for large datasets (downloads all files)
- 💡 Prefer using `load_file` to load specific files on-demand

#### Bash Examples

```bash
#!/bin/bash

# Get parent node folder
parent_folder=$(ragtool get_parent_node_folder)
echo "Parent folder: $parent_folder"

# List all files
ls -lh "$parent_folder"

# Access specific file
if [ -f "$parent_folder/output.h5ad" ]; then
    python3 process.py "$parent_folder/output.h5ad"
fi

# Batch processing
for file in "$parent_folder"/*.csv; do
    echo "Processing: $file"
    python3 analyze.py "$file"
done
```

#### Python Examples

```python
import subprocess
import os
import glob

def get_parent_folder():
    """Get parent node folder path"""
    result = subprocess.run(
        ['ragtool', 'get_parent_node_folder'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()

# Usage example
parent_folder = get_parent_folder()
print(f"Parent folder: {parent_folder}")

# List all files
files = os.listdir(parent_folder)
print(f"Available files: {files}")

# Access specific file
h5ad_file = os.path.join(parent_folder, 'output.h5ad')
if os.path.exists(h5ad_file):
    import scanpy as sc
    adata = sc.read_h5ad(h5ad_file)
    
# Batch process all CSV files
csv_files = glob.glob(os.path.join(parent_folder, '*.csv'))
for csv_file in csv_files:
    print(f"Processing: {csv_file}")
    # Processing logic...
```

#### R Examples

```r
# Get parent node folder
get_parent_folder <- function() {
  result <- system2(
    'ragtool',
    args = c('get_parent_node_folder'),
    stdout = TRUE,
    stderr = TRUE
  )
  
  if (!is.null(attr(result, "status")) && attr(result, "status") != 0) {
    stop("Failed to get parent folder: ", paste(result, collapse = "\n"))
  }
  
  return(trimws(result[1]))
}

# Usage example
parent_folder <- get_parent_folder()
cat("Parent folder:", parent_folder, "\n")

# List all files
files <- list.files(parent_folder, full.names = TRUE)
print(files)

# Access specific file
rds_file <- file.path(parent_folder, "output.rds")
if (file.exists(rds_file)) {
  data <- readRDS(rds_file)
  print(data)
}

# Batch processing
csv_files <- list.files(parent_folder, pattern = "\\.csv$", full.names = TRUE)
for (csv_file in csv_files) {
  cat("Processing:", csv_file, "\n")
  df <- read.csv(csv_file)
  # Processing logic...
}
```

#### Important Notes

- ⚠️ Downloads **all files** from parent node, may take considerable time
- ⚠️ For large datasets, prefer using `load_file` for on-demand loading
- ⚠️ Result is cached in `/app/parent-folder-path-cache`
- 💡 Parent node refers to the node with the highest index in `inputs-dict.json`

---

## Workflow Best Practices

### Recommended Workflow

```python
import subprocess
import sys

# 1. First read /app/inputs-dict.json to see available files

# 2. Load specific files on-demand
result = subprocess.run(
    ['ragtool', 'load_file', 'node_1', 'data.h5ad'],
    capture_output=True,
    text=True,
    check=True
)
file_path = result.stdout.strip()

# 3. Process file
import scanpy as sc
adata = sc.read_h5ad(file_path)

# 4. Save output to /omicairn/outputs/
adata.write('/omicairn/outputs/processed_data.h5ad')
```

### Error Handling Template

```python
import subprocess
import sys
import os

def safe_load_file(node_key, relative_path):
    """Safely load file with complete error handling"""
    try:
        result = subprocess.run(
            ['ragtool', 'load_file', node_key, relative_path],
            capture_output=True,
            text=True,
            check=True
        )
        file_path = result.stdout.strip()
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Downloaded file not found: {file_path}")
        
        return file_path
        
    except subprocess.CalledProcessError as e:
        print(f"Failed to load file {node_key}/{relative_path}", file=sys.stderr)
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)

# Usage
file_path = safe_load_file('node_1', 'data.h5ad')
```

### Multi-Language Integration Example

```bash
#!/bin/bash
# Multi-step analysis pipeline

# 1. Load R-processed data
rds_file=$(ragtool load_file node_1 seurat_object.rds)

# 2. Preprocess with R
Rscript preprocess.R "$rds_file" /tmp/preprocessed.rds

# 3. Convert to Python format and analyze
python3 convert_and_analyze.py /tmp/preprocessed.rds /omicairn/outputs/

# 4. Clean up temporary files
rm /tmp/preprocessed.rds
```

---

## FAQ

### Q1: What's the difference between load_file and get_parent_node_folder?

- `load_file`: Loads a **single file** on-demand, recommended for most scenarios
- `get_parent_node_folder`: Downloads **all files** from parent node, only use when multiple files are needed

### Q2: Will files be downloaded repeatedly?

No. `load_file` caches the downloaded file path in `inputs-dict.json`, and repeated calls return the same local path.

### Q3: How do I know which files are available?

Read the `/app/inputs-dict.json` file; it lists every file of every input node.

### Q4: What if loading fails?

Check the following:
1. Is the node key correct (node_1, node_2, etc.)?
2. Is the file path correct (case-sensitive)?
3. Do you have S3 access permissions?
4. Is there sufficient disk space?

### Q5: Can I load files from multiple ancestor nodes?

Yes. `load_file` can load any file of any node listed in `/app/inputs-dict.json`.

---

## Technical Details

### File Structure

```
/app/scripts/ragtool              # Main script (symlinked to /usr/local/bin/ragtool)
/app/scripts/load_file.py         # File loading implementation
/app/scripts/load_parent_folder.py # Parent folder loading implementation
/app/inputs-dict.json             # Input node metadata
/app/parent-folder-path-cache     # Parent folder path cache
```

### Environment Variable Dependencies

- `BUCKET_NAME`: S3 bucket name
- AWS credentials and region are resolved through the standard boto3 credential chain

### Python Environments

- `load_file` and `get_parent_node_folder`: run with the container's `python3`

---

## Quick Reference

### Command Cheat Sheet

```bash
# Load file (most common)
ragtool load_file node_1 data.h5ad

# Get parent node folder (use with caution)
ragtool get_parent_node_folder

# Help information
ragtool help
```

### Python One-Liners

```python
# Load file
file_path = subprocess.run(['ragtool', 'load_file', 'node_1', 'data.h5ad'], 
                          capture_output=True, text=True, check=True).stdout.strip()

# Get parent folder
parent_folder = subprocess.run(['ragtool', 'get_parent_node_folder'], 
                              capture_output=True, text=True, check=True).stdout.strip()
```

### R One-Liners

```r
# Load file
file_path <- trimws(system2('ragtool', c('load_file', 'node_1', 'data.rds'), stdout=TRUE)[1])

# Get parent folder
parent_folder <- trimws(system2('ragtool', c('get_parent_node_folder'), stdout=TRUE)[1])
```

---

## Claude Code Agent Integration

### When to Use ragtool

As a Claude Code agent, you should use `ragtool` when:

1. **Loading Input Data**: Always use `ragtool load_file` to access files from upstream nodes
2. **Accessing Parent Outputs**: Use `ragtool get_parent_node_folder` only when you need all parent files

### Code Generation Guidelines

When generating code that needs input data:

```python
# ✅ CORRECT: Use ragtool to load input files
import subprocess

result = subprocess.run(
    ['ragtool', 'load_file', 'node_1', 'data.h5ad'],
    capture_output=True,
    text=True,
    check=True
)
input_file = result.stdout.strip()

# Process the file
import scanpy as sc
adata = sc.read_h5ad(input_file)

# ❌ INCORRECT: Don't assume files are already downloaded
# adata = sc.read_h5ad('/omicairn/inputs/data.h5ad')  # This won't work!
```

### Error Recovery Strategy

If a file load fails, help the user by:

1. Checking available files in `/app/inputs-dict.json`
2. Verifying the node key and file path are correct
3. Suggesting alternative files if the requested one doesn't exist

### Example Complete Workflow

```python
#!/usr/bin/env python3
"""
Complete workflow example for Claude Code agents
"""
import subprocess
import sys
import os

def load_file(node_key, path):
    """Helper to load files with error handling"""
    result = subprocess.run(
        ['ragtool', 'load_file', node_key, path],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()

# Load input data
print("Loading input data...")
h5ad_file = load_file('node_1', 'processed_data.h5ad')

# Process data
print(f"Processing {h5ad_file}...")
import scanpy as sc
adata = sc.read_h5ad(h5ad_file)

# Perform analysis
sc.pp.normalize_total(adata)
sc.pp.log1p(adata)
sc.pp.highly_variable_genes(adata)

# Save outputs
output_path = '/omicairn/outputs/normalized_data.h5ad'
print(f"Saving results to {output_path}...")
adata.write(output_path)

print("Analysis complete!")
```

---

**Maintainer**: The OmiCairn Authors  
**Version**: v2.0  
**Last Updated**: 2026-02-05
