# OmiCairn worker (computation server)

> **Early-stage research software.** This is the computation worker of the OmiCairn web platform,
> released together with the accompanying publication. It is provided as-is, has not been hardened
> for production or multi-tenant use, and parts of the test suite are incomplete (see *Known limitations*).

The worker executes the analysis graph that users build in the frontend:

- **Computation server** (`server/`, Flask): task and computation APIs, node locking, dispatch of
  function-block jobs either to a local job queue (`daemon/`, one Docker container per job, chosen by
  language and preset environment) or to AWS Batch, plus RAG vector stores (ChromaDB) for fix experience,
  code library and domain knowledge.
- **Job feedback** (`handle_job_feedback/`): runs after each computation; updates node/data state, launches
  downstream nodes, and drives the LLM bug fixer (parameter and code repair) and replanning.
- **Dynamic generation / Auto Genie** (`handle_dynamic_generation/`, `auto_genie_agent/`): LLM-planned
  multi-step workflows that add nodes and edges to the analysis graph and can launch Claude Code agent nodes
  (see `../claude-code/`).
- **Visualizer** (`handle_visualizer/`): LLM-assisted figure refinement for a node.
- **File resolver** (`file_resolver/`) and preset analysis environments (`preset-envs/`).
- **MEBOCOST** (`mebocost/`): vendored third-party tool for metabolite-mediated cell–cell communication
  (BSD-3-Clause; see `mebocost/LICENSE` and `THIRD_PARTY_NOTICES.md`). Its reference databases are not
  redistributed here because of the upstream terms of use; download them from the upstream project.

## Configuration

Copy `.env.example` to `.env` (never commit real values) or export the variables before running
`scripts/launch.sh`. `scripts/set-local-env-variables.sh` provides local defaults. The worker needs MySQL,
S3-compatible object storage, the backend (`../backend`) and an LLM workflow server reachable through the
gateway described in `../frontend/README.md` (*Service topology*).

```bash
pip install -r requirements-server.txt
bash scripts/launch.sh          # or build the image: docker build -f Dockerfile .
```

## Known limitations

- Most worker HTTP endpoints (task maintenance, RAG sync, visualizer edits, computation callbacks) do not
  authenticate callers. Run the worker on a private network and expose it only through the gateway.
- Several unit tests target APIs that no longer exist or rely on import-path tricks; treat the suite as
  incomplete rather than as coverage evidence.
- AWS Batch is the default remote executor; other schedulers would need a new launcher.

## License

See the `LICENSE` file at the repository root (MIT, The OmiCairn Authors). Vendored third-party code keeps
its own license.
