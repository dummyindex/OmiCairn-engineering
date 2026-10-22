# Project Execution Rules

## Task Tracking (MANDATORY)

1. Use TodoWrite for EVERY step in the plan
2. Mark todo as "in_progress" BEFORE starting work
3. Mark as "completed" ONLY after fully finishing
4. NEVER remove incomplete tasks; NEVER mark a step as completed if only partially done

## Loading Input Files (MANDATORY)

Input files are loaded ON-DEMAND using ragtool. Check `/app/inputs-dict.json` for available files.

### Basic Usage

```bash
# Load a specific file from a node
file_path=$(ragtool load_file node_1 data.h5ad)

# Get all files from parent node
parent_folder=$(ragtool get_parent_node_folder)
```

### Python Example

```python
import subprocess

# Load file on-demand
result = subprocess.run(
    ['ragtool', 'load_file', 'node_1', 'data.h5ad'],
    capture_output=True, text=True, check=True
)
file_path = result.stdout.strip()

# Now use the file
import scanpy as sc
adata = sc.read_h5ad(file_path)
```

## Incremental Upload (MANDATORY)
### 1. Stepwise Uploads
After completing each step, upload the step's outputs to S3 by step. Use:

```bash
python3 /app/scripts/upload_step.py step_XX_description
```

Example workflow:
1. Complete step 1 analysis, save outputs to `/omicairn/outputs/step_01_data_loading/`
2. Run: `python3 /app/scripts/upload_step.py step_01_data_loading`
3. Move to step 2, save outputs to `/omicairn/outputs/step_02_quality_control/`
4. Run: `python3 /app/scripts/upload_step.py step_02_quality_control`
5. Continue for all steps...

### 2. Charts and Figures

**Save ALL figures to `/omicairn/outputs/charts/`**

```python
import matplotlib.pyplot as plt
import os

os.makedirs('/omicairn/outputs/charts', exist_ok=True)
plt.figure(figsize=(10, 6))
plt.plot(...)
plt.savefig('/omicairn/outputs/charts/descriptive_name.png', dpi=300, bbox_inches='tight')
plt.close()
```

- Supported formats: PNG, JPG, JPEG, TIFF, TIF, PDF
- Never use `plt.show()` - this is non-interactive
- Always close figures after saving

## Long-Running Jobs (>10 min)

For Cell Ranger, STAR alignment, etc., DO NOT run directly. Use the job orchestration system:

### 1. Upload current step outputs before starting the long job

```bash
python3 /app/scripts/upload_step.py step_XX_description
```

### 2. Create job request

```python
import json, uuid, subprocess
from datetime import datetime

subprocess.run(["python3", "/app/scripts/upload_step.py", "step_XX_description"], check=True)

job = {
    "request_id": str(uuid.uuid4()),
    "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
    "command": "YOUR_COMMAND_HERE",
    "working_directory": "/omicairn/outputs/step_XX_description",
    "description": "Brief description",
    "expected_outputs": ["/path/to/expected/output"]
}

with open("/omicairn/control/job_request.json", "w") as f:
    json.dump(job, f, indent=2)
print("Job submitted. Session will pause now.")
```

### 3. Exit session

The orchestrator will run the job and resume your session with the result.

### 4. On resume

Check job result, restore TodoWrite state, and continue.

## Handling Failed Steps

If a step cannot be completed:
1. Keep task in todo list, prefix with "[INCOMPLETE]:"
2. Document the reason
3. Upload partial outputs

## Available Tools

- **R**: limma, DESeq2, clusterProfiler, survival, survminer
- **Python**: numpy, pandas, scipy, scikit-learn, scanpy, matplotlib, seaborn
- Install: `pip install <pkg>` or `R -e "install.packages('<pkg>')"`
