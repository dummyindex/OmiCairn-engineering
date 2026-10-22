#!/bin/bash
set -e

# Source environment variables
source /app/scripts/set-dev-env-variables.sh

echo "=== Claude Code Execution Container ==="
echo "Computation ID: $COMPUTATION_ID"
echo "Node ID: $NODE_ID"
echo "Claude Model: $CLAUDE_MODEL"
echo "Max Iterations: $MAX_ITERATIONS"

# Authentication setup
if [ -n "$CLAUDE_CODE_OAUTH_TOKEN" ]; then
    export CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN"
    echo "Authentication configured from CLAUDE_CODE_OAUTH_TOKEN"
elif [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: No authentication token provided"
fi

# =============================================================================
# Phase 1: Preparation (Metadata Only - Files Loaded On-Demand)
# =============================================================================
echo ""
echo "=== Phase 1: Preparing metadata and node information ==="
python3 /app/previous_app/main.py

# =============================================================================
# Phase 2: Claude Code with Job Orchestration
# =============================================================================
echo ""
echo "=== Phase 2: Running Claude Code ==="
cd /omicairn/workspace

# Create directories
mkdir -p /omicairn/control/logs
mkdir -p /omicairn/outputs/orchestration_logs
mkdir -p /omicairn/outputs/charts

# Function to save iteration log
save_iteration_log() {
    local iter=$1
    local event=$2
    local timestamp=$(date -u +%Y%m%d_%H%M%S)
    local log_file="/omicairn/outputs/orchestration_logs/iteration_${iter}_${event}_${timestamp}.log"

    cat > "$log_file" << EOF
Iteration: $iter
Event: $event
Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Claude Exit Code: ${CLAUDE_EXIT_CODE:-N/A}
Session Started: ${SESSION_STARTED:-false}
Unexpected Exit Count: ${UNEXPECTED_EXIT_COUNT:-0}
EOF

    if [ -f "/omicairn/control/job_request.json" ]; then
        echo -e "\n=== Pending job_request.json ===" >> "$log_file"
        cat /omicairn/control/job_request.json >> "$log_file"
    fi
    echo "Log saved to: $log_file"
}

# Build prompt from plan
PLAN_STEPS=""
if [ -f "/app/auto-genie-current-plan.json" ]; then
    PLAN_STEPS=$(cat /app/auto-genie-current-plan.json | jq -r '.steps // "No steps defined"')
fi

# =============================================================================
# Check for previous node context (inputs-dict.json and summaries)
# =============================================================================
PREVIOUS_NODES_CONTEXT=""
INPUTS_DICT_PATH="/app/inputs-dict.json"

if [ -f "$INPUTS_DICT_PATH" ]; then
    echo "Found inputs-dict.json"

    # Count nodes and files for a brief summary
    NODE_COUNT=$(cat "$INPUTS_DICT_PATH" | jq 'keys | length')
    FILE_COUNT=$(cat "$INPUTS_DICT_PATH" | jq '[.[] | .files | keys | length] | add // 0')

    PREVIOUS_NODES_CONTEXT="## Previous Node Information

This session has access to files from $NODE_COUNT previous node(s) with $FILE_COUNT total file(s).

### How to Access Input Files
1. **Read the file listing**: Use Read tool to read \`/app/inputs-dict.json\`
2. **Load files on-demand**: Use ragtool to download files when needed

\`\`\`bash
# Load a specific file
file_path=\$(ragtool load_file node_1 data.h5ad)
\`\`\`"

    # Look for summary files from previous nodes
    SUMMARY_FILES=$(find /omicairn/inputs -iname "*summary*" -type f 2>/dev/null || true)

    if [ -n "$SUMMARY_FILES" ]; then
        PREVIOUS_NODES_CONTEXT="$PREVIOUS_NODES_CONTEXT

### Previous Job Summaries
"
        while IFS= read -r SUMMARY_FILE; do
            [ -z "$SUMMARY_FILE" ] && continue
            REL_PATH=$(echo "$SUMMARY_FILE" | sed 's|/omicairn/inputs/||')
            SUMMARY_CONTENT=$(cat "$SUMMARY_FILE")

            PREVIOUS_NODES_CONTEXT="$PREVIOUS_NODES_CONTEXT

#### $REL_PATH
\`\`\`markdown
$SUMMARY_CONTENT
\`\`\`"
        done <<< "$SUMMARY_FILES"
    fi

    PREVIOUS_NODES_CONTEXT="$PREVIOUS_NODES_CONTEXT

### Instructions for Continuing Previous Work
1. **Read inputs-dict.json** to understand available files from previous nodes
2. **Use ragtool load_file** to download specific files when needed
3. **Review any summary.md files** to understand what was accomplished
4. **Continue from where previous nodes left off**

"
    echo "Previous node context extracted successfully"
else
    echo "No inputs-dict.json found - this is a fresh session"
fi

cat > /tmp/claude_prompt.md << EOF
# Analysis Task

## Input Data Access
Input files are loaded ON-DEMAND using ragtool. Check /app/inputs-dict.json for available files.

$PREVIOUS_NODES_CONTEXT

## Plan to Execute
$PLAN_STEPS

## Instructions
1. This is AUTOMATED - make all decisions autonomously
2. Read /omicairn/workspace/CLAUDE.md for execution rules
3. Use ragtool to load input files on-demand (see /app/inputs-dict.json)
4. Execute the plan step by step
5. Debug and fix errors as needed
6. Save ALL figures to /omicairn/outputs/charts/
7. Create summary.md in /omicairn/outputs/ when done

## Output Organization
Organize outputs into step folders:
\`\`\`
/omicairn/outputs/
├── charts/                    # ALL figures
├── step_01_data_loading/
├── step_02_quality_control/
└── summary.md
\`\`\`

## Incremental Upload
After EACH step:
\`\`\`bash
python3 /app/scripts/upload_step.py step_XX_description
\`\`\`
EOF

echo "Created prompt file at /tmp/claude_prompt.md"

# =============================================================================
# Job Orchestration Loop
# =============================================================================
echo ""
echo "=== Starting Job Orchestration Loop ==="

ITERATION=0
MAX_LOOP_ITERATIONS=${MAX_LOOP_ITERATIONS:-50}
SESSION_STARTED=false
UNEXPECTED_EXIT_COUNT=0
MAX_UNEXPECTED_RETRIES=1
CLAUDE_EXIT_CODE=0
# Outcome passed to close_out_app: 1 = completed, 0 = failed/incomplete
PIPELINE_SUCCESS=0
PIPELINE_ERROR="Claude Code execution did not complete"

while true; do
    ITERATION=$((ITERATION + 1))
    echo ""
    echo "=== Iteration $ITERATION of $MAX_LOOP_ITERATIONS ==="

    if [ $ITERATION -gt $MAX_LOOP_ITERATIONS ]; then
        echo "ERROR: Exceeded maximum iterations"
        PIPELINE_ERROR="Exceeded maximum orchestration iterations"
        break
    fi

    # Start conversation uploader
    python3 /app/scripts/upload_conversation.py &
    UPLOADER_PID=$!

    if [ "$SESSION_STARTED" = true ]; then
        # Resume session
        echo "=== Resuming Session ==="

        TODO_CONTEXT=""
        if [ -f "/omicairn/outputs/claude_code.log" ]; then
            TODO_CONTEXT=$(python3 /app/scripts/parse_todo_progress.py --format-prompt 2>/dev/null || echo "")
        fi

        RESUME_PROMPT=""
        if [ -f "/omicairn/control/job_result.json" ]; then
            JOB_RESULT=$(cat /omicairn/control/job_result.json)
            RESUME_PROMPT="Long-running job completed:

\`\`\`json
$JOB_RESULT
\`\`\`

## Previous Progress
$TODO_CONTEXT

Restore your TodoWrite state, check job result, and continue."
            rm -f /omicairn/control/job_result.json
        else
            RESUME_PROMPT="Continuing session.

$TODO_CONTEXT

Restore TodoWrite state and continue with remaining tasks."
        fi

        {
            echo "$RESUME_PROMPT" | claude --dangerously-skip-permissions \
                --print --verbose \
                --model "${CLAUDE_MODEL:-sonnet}" \
                --max-turns "${MAX_ITERATIONS:-100}" \
                --output-format stream-json \
                --continue 2>&1
        } | tee -a /omicairn/outputs/claude_code.log
        CLAUDE_EXIT_CODE=${PIPESTATUS[0]}
    else
        # New session
        echo "=== Starting New Session ==="
        # NOTE: --dangerously-skip-permissions is only intended for this isolated,
        # ephemeral, non-root container with no host credentials mounted.
        {
            claude --dangerously-skip-permissions \
                --print --verbose \
                --model "${CLAUDE_MODEL:-sonnet}" \
                --max-turns "${MAX_ITERATIONS:-100}" \
                --output-format stream-json \
                < /tmp/claude_prompt.md 2>&1
        } | tee /omicairn/outputs/claude_code.log
        CLAUDE_EXIT_CODE=${PIPESTATUS[0]}
        SESSION_STARTED=true
    fi

    # Stop uploader
    kill $UPLOADER_PID 2>/dev/null || true

    echo "Claude exited with code: $CLAUDE_EXIT_CODE"
    save_iteration_log $ITERATION "claude_exit"

    # Check for job request
    if [ -f "/omicairn/control/job_request.json" ]; then
        echo "=== Running Long-Running Job ==="
        UNEXPECTED_EXIT_COUNT=0
        python3 /app/scripts/run_job.py || true
        save_iteration_log $ITERATION "job_complete"
        python3 /app/scripts/upload_orchestration_logs.py --iteration $ITERATION || true
        continue
    fi

    # If Claude exited cleanly (code 0), treat the session as complete
    if [ $CLAUDE_EXIT_CODE -eq 0 ]; then
        echo "=== Claude Code Completed Successfully (exit code 0) ==="
        PIPELINE_SUCCESS=1
        break
    fi

    # For non-zero exits, verify via TodoWrite state
    DONE_EXIT_CODE=0
    python3 /app/scripts/all_steps_done.py || DONE_EXIT_CODE=$?

    if [ $DONE_EXIT_CODE -eq 0 ]; then
        echo "=== All Steps Completed ==="
        PIPELINE_SUCCESS=1
        break
    elif [ $DONE_EXIT_CODE -eq 2 ]; then
        echo "=== Pipeline Failed ==="
        PIPELINE_ERROR="Pipeline reported failure (all_steps_done.py exit code 2)"
        break
    fi

    # Handle unexpected exit
    UNEXPECTED_EXIT_COUNT=$((UNEXPECTED_EXIT_COUNT + 1))
    echo "WARNING: Unexpected exit ($UNEXPECTED_EXIT_COUNT of $MAX_UNEXPECTED_RETRIES)"

    if [ $UNEXPECTED_EXIT_COUNT -gt $MAX_UNEXPECTED_RETRIES ]; then
        echo "ERROR: Too many unexpected exits"
        PIPELINE_ERROR="Too many unexpected Claude Code exits"
        break
    fi
done

echo "=== Loop ended after $ITERATION iterations ==="
save_iteration_log $ITERATION "loop_end"
python3 /app/scripts/upload_orchestration_logs.py --iteration $ITERATION || true

# =============================================================================
# Phase 3: Close out
# =============================================================================
echo ""
echo "=== Phase 3: Uploading outputs ==="
PIPELINE_SUCCESS="$PIPELINE_SUCCESS" PIPELINE_ERROR="$PIPELINE_ERROR" python3 /app/close_out_app/main.py

echo "=== Claude Code Execution Complete ==="
