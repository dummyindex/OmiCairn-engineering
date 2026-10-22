import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
try:
    from .server_api_invoker import ServerAPIInvoker
except ImportError:
    from server_api_invoker import ServerAPIInvoker

# Constants
WORKSPACE = "/omicairn"
INPUTS_FOLDER = "/omicairn/inputs"


class AutoGenieStatus:
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    RESPONDING = "responding"
    COMPLETED = "completed"
    FAILED = "failed"


class AutoGenieAgent:
    """Auto Genie Agent for handling automated generation interactions"""

    def __init__(self, dynamic_generation_id: str, user_id: str = None):
        self.dynamic_generation_id = dynamic_generation_id
        self.user_id = user_id
        self.api = ServerAPIInvoker(user_id=user_id)
        self.generation_info = self.api.get_dynamic_generation_info(
            dynamic_generation_id)

        if not self.generation_info:
            raise ValueError(
                f"Dynamic generation {dynamic_generation_id} not found")

    def init(self) -> bool:
        """Initialize auto genie agent - currently just pass"""
        return True

    def get_inputs_structure(self) -> Dict[str, Any]:
        """
        Get the inputs directory structure as a nested JSON.
        Returns a hierarchical structure with 'children' field representing relationships.
        Leaf nodes represent files with node_id and relative path.
        """
        # Get node_id from generation_info
        node_id = self.generation_info.get('node_id')
        if not node_id:
            print("Warning: No node_id found in generation_info, cannot fetch inputs structure")
            return {"name": "inputs", "type": "directory", "children": []}

        # Call server API to get inputs structure
        structure = self.api.get_inputs_structure(node_id)
        if structure:
            return structure
        else:
            print("Warning: Failed to get inputs structure from server API")
            return {"name": "inputs", "type": "directory", "children": []}

    def get_file_content(self, node_id: Optional[str] = None, relative_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Get file content by node_id or relative path.
        For binary files, return file attributes instead of content.

        Args:
            node_id: Optional node identifier (not used, kept for compatibility)
            relative_path: Path relative to INPUTS_FOLDER

        Returns:
            Dict with 'content' or 'info' for binary files
        """
        if not relative_path:
            return {"error": "relative_path must be provided"}

        # Get node_id from generation_info
        generation_node_id = self.generation_info.get('node_id')
        if not generation_node_id:
            return {"error": "No node_id found in generation_info"}

        # Call server API to get file content
        result = self.api.get_file_content(generation_node_id, relative_path)
        if result:
            return result
        else:
            return {"error": "Failed to get file content from server API"}

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _convert_structure_to_markdown(self, structure: Dict[str, Any], indent: int = 0) -> str:
        """
        Convert inputs structure to markdown format with indentation.
        Only show filenames for leaf nodes.
        """
        lines = []
        indent_str = "  " * indent

        if structure.get("type") == "directory":
            if indent > 0:  # Don't show root
                lines.append(
                    f"{indent_str}- {structure.get('name', 'unnamed')}/")
            for child in structure.get("children", []):
                lines.append(
                    self._convert_structure_to_markdown(child, indent + 1))
        elif structure.get("type") == "file":
            lines.append(f"{indent_str}- {structure.get('name', 'unnamed')}")

        return "\n".join(lines)

    def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Define tools available for LLM to call"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_file_content",
                    "description": "Read the content of a file from the inputs folder. Use this to examine input data files.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "relative_path": {
                                "type": "string",
                                "description": "The relative path of the file from the inputs folder (e.g., 'data/sample.csv')"
                            },
                            "node_id": {
                                "type": "string",
                                "description": "Optional node ID if known"
                            }
                        },
                        "required": ["node_id", "relative_path"]
                    }
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Handle tool calls from LLM"""
        if tool_name == "get_file_content":
            return self.get_file_content(
                node_id=arguments.get("node_id"),
                relative_path=arguments.get("relative_path")
            )
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def _get_system_message(self) -> Dict[str, str]:
        """Get system prompt for LLM"""
        # Get inputs structure
        inputs_structure = self.get_inputs_structure()
        inputs_markdown = self._convert_structure_to_markdown(inputs_structure)

        # Get plan if available
        plan = self.generation_info.get('plan', '')

        # Load FB writing guide (placeholder for now)
        fb_guide = """
## Function Block (FB) Writing Guide

### Structure
A Function Block is a directory containing:
- **REQUIRED**: `static-config.json` - Configuration file with metadata and parameters
- **REQUIRED**: `run.sh` - Executable entry point script
- **OPTIONAL**: Other files referenced using relative paths from run.sh

### File Specifications

#### static-config.json
```json
{
  "name": "FB name",
  "description": "FB description",
  "version": "1.0.0",
  "args": [
    {
      "name": "param_name",
      "type": "string|number|boolean|file",
      "required": true,
      "default": "default_value",
      "description": "parameter description"
    }
  ],
  "tag": "category_tag",
  "document_url": "doc_link",
  "source": "source_info"
}
```

#### run.sh
- Must be executable shell script
- Use relative paths for internal files
- Handle parameters via environment variables
- Return appropriate exit codes (0=success, non-0=failure)

### Rules
1. Use relative paths for all internal file references
2. Paths are relative to the directory containing run.sh
3. **STRICTLY** follow the directory structure requirements
"""

        return {
            "role": "system",
            "content": (
                "You are an AI assistant for AutoGenie, an automated bioinformatics analysis generation system. "
                "Your role is to generate Function Blocks (FB) following a step-by-step plan.\n\n"

                f"{fb_guide}\n\n"

                "## Available Input Files:\n"
                f"{inputs_markdown}\n\n"

                "## Current Plan:\n"
                f"{plan if plan else 'No plan yet - create one based on user request'}\n\n"

                "## Your Task:\n"
                "1. Follow the plan and generate the NEXT unchecked step\n"
                "2. Generate ALL necessary FB files for this step\n"
                "3. Mark the completed step with √ in the plan\n\n"

                "## Response Format:\n"
                "You MUST respond in this EXACT JSON format:\n"
                "```json\n"
                "{\n"
                '  "function_block": {\n'
                '    "run.sh": "script content here",\n'
                '    "static-config.json": "config content here",\n'
                '    "other-file1.py": "file content here",\n'
                '    "other-file2.R": "file content here"\n'
                "  },\n"
                '  "plan": "updated plan with √ marks for completed steps"\n'
                "}\n"
                "```\n\n"

                "## Important Rules:\n"
                "- Generate ONE step at a time (the first unchecked [ ] step)\n"
                "- Mark completed steps by changing [ ] to [√]\n"
                "- Include ALL files needed for the FB in function_block object\n"
                "- Use relative paths within FB files\n"
                "- MUST include both run.sh and static-config.json\n"
                "- Follow the exact JSON format above\n\n"

                "## Context:\n"
                f"Dynamic Generation ID: {self.generation_info.get('id', 'Unknown')}\n"
                f"Status: {self.generation_info.get('status', 'Unknown')}\n"
                f"User Request: {self.generation_info.get('user_request', 'No request specified')}\n"
            )
        }
