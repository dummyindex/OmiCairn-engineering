#!/usr/bin/env python3
"""
Parse claude_code.log to extract the most recent TodoWrite tool use.

This script is used by the orchestration loop to:
1. Determine if all tasks are completed (for all_steps_done.py)
2. Provide task context when resuming Claude sessions (for start_claude_code.sh)

Exit codes (when using --check-done):
    0 - All todos completed
    1 - Todos remaining or not found
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

DEFAULT_LOG_PATH = Path("/omicairn/outputs/claude_code.log")


def reverse_readline(filepath: Path, buf_size: int = 8192):
    """
    Read file line-by-line in reverse order, memory-efficient.

    This is crucial for large log files - we only need the most recent
    TodoWrite entry, so reading from the end is much faster.
    """
    with open(filepath, "rb") as f:
        f.seek(0, 2)  # Go to end
        file_size = remaining = f.tell()
        segment = None
        offset = 0

        while remaining > 0:
            offset = min(file_size, offset + buf_size)
            f.seek(file_size - offset)
            buffer = f.read(min(remaining, buf_size))
            remaining -= buf_size
            lines = buffer.decode("utf-8", errors="replace").split("\n")

            if segment is not None:
                # Handle partial line from previous iteration
                lines[-1] += segment
            segment = lines[0]

            for line in reversed(lines[1:]):
                if line.strip():
                    yield line

        if segment and segment.strip():
            yield segment


def find_last_todowrite(log_path: Path) -> list | None:
    """
    Find the most recent TodoWrite tool use in the log.

    Searches backwards through the NDJSON log file for the first
    (most recent) TodoWrite entry.

    Returns:
        list: The todos array from the most recent TodoWrite, or None if not found
    """
    if not log_path.exists():
        return None

    for line in reverse_readline(log_path):
        try:
            entry = json.loads(line)
            if entry.get("type") == "assistant":
                message = entry.get("message", {})
                content = message.get("content", [])
                for item in content:
                    if (
                        item.get("type") == "tool_use"
                        and item.get("name") == "TodoWrite"
                    ):
                        return item.get("input", {}).get("todos", [])
        except json.JSONDecodeError:
            continue  # Skip malformed lines
        except Exception:
            continue  # Skip any other errors

    return None


def check_all_completed(todos: list) -> bool:
    """
    Check if all todos have status 'completed'.

    Returns:
        bool: True only if todos exist AND all have status 'completed'
    """
    if not todos:
        return False  # No todos = not done (be conservative)
    return all(todo.get("status") == "completed" for todo in todos)


def format_for_prompt(todos: list) -> str:
    """
    Format todos as readable text for resume prompt.

    This output is included in the resume prompt to help Claude
    restore its task state after a long-running job completes.
    """
    if not todos:
        return "No previous task progress found."

    lines = ["The following tasks were being tracked:"]
    for i, todo in enumerate(todos, 1):
        status = todo.get("status", "unknown")
        content = todo.get("content", "Unknown task")
        symbol = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}.get(
            status, "[?]"
        )
        lines.append(f"  {i}. {symbol} {content}")

    # Add summary
    completed = sum(1 for t in todos if t.get("status") == "completed")
    in_progress = sum(1 for t in todos if t.get("status") == "in_progress")
    pending = sum(1 for t in todos if t.get("status") == "pending")
    total = len(todos)
    lines.append(f"\nProgress: {completed}/{total} tasks completed")
    if in_progress > 0:
        lines.append(f"Currently in progress: {in_progress} task(s)")
    if pending > 0:
        lines.append(f"Remaining: {pending} task(s)")

    return "\n".join(lines)


def save_todos_snapshot(todos: list, output_path: Path) -> bool:
    """
    Save extracted todos to a JSON file for persistence/audit.

    Args:
        todos: The todos array to save
        output_path: Path to save the JSON file

    Returns:
        bool: True if saved successfully
    """
    try:
        snapshot = {
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "todos": todos,
            "completed_count": sum(1 for t in todos if t.get("status") == "completed"),
            "total_count": len(todos),
            "all_completed": check_all_completed(todos),
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(snapshot, f, indent=2)
        return True
    except Exception as e:
        print(f"Warning: Could not save todos snapshot: {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Parse todo progress from claude_code.log"
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Path to claude_code.log file",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )
    parser.add_argument(
        "--check-done",
        action="store_true",
        help="Exit 0 if all todos completed, 1 otherwise",
    )
    parser.add_argument(
        "--format-prompt",
        action="store_true",
        help="Format todos for resume prompt",
    )
    parser.add_argument(
        "--save-snapshot",
        type=Path,
        metavar="PATH",
        help="Save todos to a JSON file at the specified path",
    )
    args = parser.parse_args()

    # Find the most recent TodoWrite
    todos = find_last_todowrite(args.log)

    # Optionally save snapshot
    if args.save_snapshot and todos:
        save_todos_snapshot(todos, args.save_snapshot)

    # Handle different output modes
    if args.check_done:
        # Exit 0 if all done, 1 otherwise
        sys.exit(0 if check_all_completed(todos) else 1)

    elif args.json:
        # Output JSON format
        result = {
            "todos": todos,
            "all_completed": check_all_completed(todos),
            "completed_count": sum(1 for t in (todos or []) if t.get("status") == "completed"),
            "total_count": len(todos or []),
        }
        print(json.dumps(result, indent=2))

    elif args.format_prompt:
        # Output formatted text for resume prompt
        print(format_for_prompt(todos))

    else:
        # Default: print summary
        if todos:
            completed = sum(1 for t in todos if t.get("status") == "completed")
            in_progress = sum(1 for t in todos if t.get("status") == "in_progress")
            pending = sum(1 for t in todos if t.get("status") == "pending")
            total = len(todos)
            print(f"Found {total} todos in log")
            print(f"  Completed: {completed}")
            print(f"  In Progress: {in_progress}")
            print(f"  Pending: {pending}")
            print(f"All completed: {check_all_completed(todos)}")
        else:
            print("No TodoWrite entries found in log")

    return 0


if __name__ == "__main__":
    sys.exit(main())
