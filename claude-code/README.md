# OmiCairn Claude Code agent runner

> **Early-stage research software**, released with the OmiCairn publication and provided as-is.

This component runs Anthropic's Claude Code CLI inside a Docker container as an autonomous analysis agent for
one node of an OmiCairn analysis graph. The worker (`../worker`) launches it as a batch job.

1. **Prepare inputs** (`previous_app/`): fetch node, branch and plan metadata from the backend and build an
   on-demand index of upstream files.
2. **Run the agent** (`scripts/start_claude_code.sh`): build the analysis prompt from the plan and upstream
   context, run Claude Code in a loop that can pause for long-running jobs (`scripts/run_job.py`) and resume
   the session, and upload step outputs and logs to object storage as they are produced.
3. **Close out** (`close_out_app/`): upload final results, generate thumbnails and report the real outcome
   (success or failure) to the backend.

Design details are in `DESIGN.md`; the execution rules given to the agent are in `CLAUDE.md`, and reusable
skills are in `skills/`.

## Configuration

The container expects the backend/worker hosts, `SYSTEM_AGENT_KEY` (sent as the `X-System-Agent-Key`
header), object-storage settings and Claude Code credentials as environment variables; see
`scripts/set-dev-env-variables.sh`. Never bake credentials into the image.

```bash
bash build-image.sh            # builds the image locally (push to your own registry if needed)
```

## Known limitations

- `tests/test_integration.py` is a scaffold and is skipped; there is no meaningful automated test coverage yet.
- Generated reports are produced by an AI agent and must be reviewed by a human expert.

## License

See the `LICENSE` file at the repository root (MIT, The OmiCairn Authors).
