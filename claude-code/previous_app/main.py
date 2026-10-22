from server_api_invoker import ServerAPIInvoker
from constants import COMPUTATION_ID, NODE_ID, PIPE_MESSAGE_PATH, USER_ID, BUCKET_NAME
import boto3
import os
import zipfile
import json
from log.logger_factory import logger_factory
from timepiece import TimePiece
import requests

logger = logger_factory.get_logger("PreviousApp Main")

def prepare():
    timepiece = TimePiece()
    timepiece.start_duration("previous app main")
    timepiece.start_duration("initialize server api invoker")
    server_api_invoker = ServerAPIInvoker(USER_ID)
    timepiece.end_duration("initialize server api invoker")

    # prepare node information
    timepiece.start_duration("prepare node information")
    current_node_info = server_api_invoker.get_node_information(NODE_ID)
    with open("/app/current_node_info.json", "w") as f:
        json.dump(current_node_info, f)
    timepiece.end_duration("prepare node information")


    timepiece.start_duration("prepare auto genie information")
    if current_node_info.get("dynamicGenerationId", None) is not None:
        # prepare auto genie information
        auto_genie_info = server_api_invoker.get_autogenie_task_information(current_node_info.get("dynamicGenerationId"))
        if auto_genie_info is not None and auto_genie_info.get("state") != "stopped":
            with open("/app/auto-genie-user-request", "w", encoding="utf-8") as f:
                json.dump(auto_genie_info.get("userRequest",""), f)
            auto_genie_current_plan = server_api_invoker.get_autogenie_plan(current_node_info.get("dynamicGenerationId"), NODE_ID)
            plan_url = auto_genie_current_plan.get("presigned_url", None)
            plan_response = requests.get(plan_url)
            plan_content = plan_response.text
            with open("/app/auto-genie-current-plan.json", "w", encoding="utf-8") as f:
                f.write(plan_content)
    timepiece.end_duration("prepare auto genie information")

    # prepare datas - build inputs dictionary with file metadata (no download)
    timepiece.start_duration("prepare datas")
    branch_path = server_api_invoker.get_branch_path(NODE_ID)
    branch_nodes = branch_path.get("previousNodeList", [])
    branch_edges = branch_path.get("previousEdgeList", [])
    
    # Create S3 client for listing files
    s3_client = boto3.client("s3")
    
    inputs_dict = {}
    index = 1
    last_node_key = None
    total_nodes = len(branch_nodes)

    for node_index, target_node in enumerate(branch_nodes):
        target_node_id = target_node.get("id")
        node_key = f"node_{index}"
        is_last_node = (node_index == total_nodes - 1)

        if is_last_node:
            last_node_key = node_key

        # extra files
        extra_files = server_api_invoker.get_node_extra_files(target_node_id)

        if extra_files:
            extra_files_dict = {}
            for extra_file in extra_files:
                file_key = extra_file.get("Key")
                if file_key.endswith('/'):
                    continue
                file_size = extra_file.get("Size")
                virtual_path = "attached_files/" + os.path.basename(file_key)
                extra_files_dict[virtual_path] = {
                    "object_key": file_key,
                    "size": file_size,
                    "filename": os.path.basename(file_key),
                    "last_modified": extra_file.get("LastModified")
                }
        else:
            extra_files_dict = {}

        target_computation_id = None
        
        if target_node.get("type").startswith("data node"):
            target_data_id = target_node.get("dataId")
        else:
            latest_computation_details = server_api_invoker.get_computation_details(target_node_id)
            computation_basic_info = latest_computation_details.get("computation_basic_info", {})
            target_data_id = computation_basic_info.get("resultDataId")
            target_computation_id = computation_basic_info.get("id")
        
        if target_data_id is not None:
            source_data_prefix = f"adata/{target_data_id}-general-s3-store/"
            
            # List files from S3 and build file metadata dictionary
            files_dict = {}
            paginator = s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=source_data_prefix):
                for obj in page.get("Contents", []):
                    full_key = obj["Key"]
                    # Skip directory markers
                    if full_key.endswith('/'):
                        continue

                    # Skip chart files
                    if full_key[len(source_data_prefix):].startswith("charts/"):
                        continue

                    # Remove prefix to get virtual relative path
                    virtual_path = full_key[len(source_data_prefix):].lstrip('/')
                    if virtual_path:  # Skip empty paths
                        files_dict[virtual_path] = {
                            "object_key": full_key,
                            "size": obj["Size"],
                            "filename": os.path.basename(full_key),
                            "last_modified": obj["LastModified"].isoformat()
                        }
            
            node_data = {
                "node_id": target_node_id,
                "computation_id": target_computation_id,
                "data_id": target_data_id,
                "files": files_dict | extra_files_dict
            }

            inputs_dict[node_key] = node_data
            logger.info(f"Prepared metadata for {node_key} (last node): {len(files_dict)} files")
        else:
            logger.warning(f"No data found for node {target_node_id}")
            node_data = {
                "node_id": target_node_id,
                "computation_id": target_computation_id,
                "data_id": None,
                "files": {} | extra_files_dict
            }
            inputs_dict[node_key] = node_data
        
        index += 1

    # Save last node to /app/inputs-dict.json
    with open("/app/inputs-dict.json", "w") as f:
        json.dump(inputs_dict, f, indent=2)
    logger.info(f"Saved inputs-dict.json with {len(inputs_dict)} node(s)")

    # For backward compatibility, write the last node key to parent-node
    if last_node_key:
        with open("/tmp/parent-node", "w") as f:
            f.write(last_node_key)
    
    timepiece.end_duration("prepare datas")

    timepiece.end_duration("previous app main")
    duration_reports = timepiece.get_duration_reports()

    os.makedirs("/omicairn/outputs/charts", exist_ok=True)

    with open(PIPE_MESSAGE_PATH, "w") as f:
        json.dump({
            "previous_duration_reports": duration_reports,
            "duration": timepiece.get_duration_length("previous app main").total_seconds()
        }, f)

def main():
    try:
        prepare()
    except Exception as e:
        import traceback
        logger.error(f"Error in previous app main: {str(e)}")
        with open("/tmp/error.log", "w") as f:
            json.dump({
                "error": str(e),
                "traceback": traceback.format_exc()
            }, f)
        raise e

if __name__ == "__main__":
    main()