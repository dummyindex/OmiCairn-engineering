#!/usr/bin/env python3
"""
load_file.py - On-demand file loader from S3
Loads files from S3 based on inputs-dict.json metadata
"""

import sys
import json
import os
import boto3
import tempfile
from api_client import APIClient

# Get constants from environment variables
BUCKET_NAME = os.getenv("BUCKET_NAME")

def load_file(node_key, virtual_path):
    """Load a file from S3 on-demand.
    
    Args:
        node_key: The node key (e.g., "node_1")
        virtual_path: The virtual relative path of the file
    
    Returns:
        Prints the local file path to stdout
    """
    # Read inputs dictionary
    inputs_dict_path = "/app/inputs-dict.json"

    if not os.path.exists(inputs_dict_path):
        print(f"Error: {inputs_dict_path} not found", file=sys.stderr)
        sys.exit(1)

    if os.path.exists(inputs_dict_path):
        with open(inputs_dict_path, 'r') as f:
            inputs_dict = json.load(f)
    else:
        inputs_dict = {}

    # Check if node exists
    if node_key not in inputs_dict:
        print(f"Error: Node '{node_key}' not found in inputs dictionary", file=sys.stderr)
        sys.exit(1)
    
    node_data = inputs_dict[node_key]
    files = node_data.get("files", {})
    
    # Check if file exists
    if virtual_path not in files:
        print(f"Error: File '{virtual_path}' not found in {node_key}", file=sys.stderr)
        print(f"Available files: {list(files.keys())}", file=sys.stderr)
        sys.exit(1)
    
    file_info = files[virtual_path]
    
    # Check if already cached
    if "cache_file" in file_info:
        cache_path = file_info["cache_file"]
        if os.path.exists(cache_path):
            print(cache_path)
            return
    
    # Download file from S3
    object_key = file_info["object_key"]
    filename = file_info["filename"]
    
    # Get file extension to preserve it
    _, ext = os.path.splitext(filename)
    
    # Create temporary file with same extension
    temp_fd, temp_path = tempfile.mkstemp(suffix=ext, dir="/tmp", prefix="omicairn_input_")
    os.close(temp_fd)  # Close the file descriptor
    
    # Download file from S3
    s3_client = boto3.client("s3")
    
    try:
        s3_client.download_file(BUCKET_NAME, object_key, temp_path)
    except Exception as e:
        print(f"Error downloading file from S3: {str(e)}", file=sys.stderr)
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        sys.exit(1)
    
    # Update inputs dictionary with cache path
    file_info["cache_file"] = temp_path
    
    with open(inputs_dict_path, 'w') as f:
        json.dump(inputs_dict, f, indent=2)
    
    # Print the local file path
    print(temp_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: load_file.py <node_key> <virtual_path>", file=sys.stderr)
        sys.exit(1)
    
    node_key = sys.argv[1]
    virtual_path = sys.argv[2]
    
    load_file(node_key, virtual_path)
