#!/usr/bin/env python3
"""
load_parent_folder.py - On-demand parent folder loader from S3
Loads files from S3 based on inputs-dict.json metadata
"""

import sys
import json
import os
import boto3
import tempfile

# Get constants from environment variables
BUCKET_NAME = os.getenv("BUCKET_NAME")

def load_parent_folder():
    """Load parent folder from S3 on-demand
    Args: --

    Returns: parent folder path
    """
    if os.path.exists("/app/parent-folder-path-cache"):
        with open("/app/parent-folder-path-cache", 'r') as f:
            print(f.read().strip())
            return

    # Read inputs dictionary
    inputs_dict_path = "/app/inputs-dict.json"
    if not os.path.exists(inputs_dict_path):
        print(f"Error: {inputs_dict_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(inputs_dict_path, 'r') as f:
        inputs_dict = json.load(f)

    nodes_keys = list(inputs_dict.keys())
    if not nodes_keys:
        print("Error: No nodes found in inputs dictionary", file=sys.stderr)
        sys.exit(1)

    max_index = max(int(key.split("_")[-1]) for key in nodes_keys)
    parent_node_key = f"node_{max_index}"
    node_data = inputs_dict.get(parent_node_key, {})
    files = node_data.get("files", {})

    if not files:
        print(f"Error: No files found in parent node '{parent_node_key}'", file=sys.stderr)
        sys.exit(1)

    # Download file from S3
    s3_client = boto3.client("s3")

    temp_folder = tempfile.mkdtemp()
    for virtual_path, file_info in files.items():
        object_key = file_info["object_key"]
        local_path = os.path.join(temp_folder, virtual_path)
        local_path_dir = os.path.dirname(local_path)
        os.makedirs(local_path_dir, exist_ok=True)

        try:
            s3_client.download_file(BUCKET_NAME, object_key, local_path)
        except Exception as e:
            continue
    with open("/app/parent-folder-path-cache", 'w') as f:
        f.write(temp_folder)

    print(temp_folder)


if __name__ == "__main__":
    load_parent_folder()