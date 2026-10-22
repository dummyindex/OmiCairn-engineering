# OmiCairn engineering release

This repository contains the source code of the **OmiCairn web platform**: the engineered, multi-user
deployment of OmiCairn, an accountable, self-learning multi-agent platform for hypothesis-driven biomedical
multi-omics analysis. It is released together with the OmiCairn publication for transparency and
reproducibility.

> **Research software, provided as-is.** The platform was developed as a hosted service and is released here
> without its deployment infrastructure. It has not been hardened for production or multi-tenant use, parts of
> the test suites are incomplete, and some features depend on services that are not included (see
> *Known limitations*). For a lighter, single-machine implementation of the OmiCairn workflow see the academic
> release (`https://github.com/dummyindex/OmiCairn`); the earliest research prototype is in
> `https://github.com/dummyindex/OmiCairn-early`.

## Components

| Directory | What it is |
|---|---|
| [`frontend/`](frontend/) | React/TypeScript (UmiJS + Ant Design) web interface: analysis graph editor, data management, visual panel, AI assistant |
| [`backend/`](backend/) | Flask API: users, analyses, nodes and edges of the analysis tree, function-block library, reports, LLM chat and workflow endpoints |
| [`worker/`](worker/) | Flask computation server: job dispatch (local Docker or AWS Batch), job feedback, LLM bug fixer, dynamic workflow generation ("Auto Genie"), visualizer, RAG stores |
| [`claude-code/`](claude-code/) | Container that runs Claude Code as an autonomous analysis agent for one node, with pause/resume for long jobs |

```
browser ──> frontend ──> gateway ──/server/──────────────> backend ──> MySQL, object storage, LLM APIs
                                 └─/computation-server/──> worker ──> local Docker jobs / AWS Batch
                                                                 └──> claude-code agent jobs
```

The gateway and its prefix mapping are described in [`frontend/README.md`](frontend/README.md#service-topology).
Each component has its own README and `.env.example` listing every configuration variable (placeholders only).

## Getting started

1. Provision MySQL, an S3-compatible object store and API keys for the LLM providers you want to use.
2. Copy each component's `.env.example` to `.env` and fill in your own values. Never commit them.
3. Start the backend and worker (see their READMEs), then the frontend (`pnpm install && pnpm dev`).
4. Put an HTTP gateway in front of the services as described in `frontend/README.md`.

## Known limitations

- The optional data-preprocessing / attached-data service used by some frontend views is not part of this
  release; dataset preprocessing, cell/gene-set browsing and saved visualization data need it.
- Authorization is incomplete in places (some backend endpoints have no ownership checks; most worker
  endpoints are unauthenticated). Run the backend and worker on a private network behind the gateway.
- Several unit tests in the backend and worker target APIs that no longer exist; treat the suites as incomplete.
- The default remote executor is AWS Batch.
- MEBOCOST reference data are not redistributed (upstream terms of use); see `worker/THIRD_PARTY_NOTICES.md`.

## Responsible use

OmiCairn executes LLM-generated code. Run it only on trusted infrastructure, never with production credentials
inside job containers, and have domain experts review every result. Outputs support hypothesis generation; they
are not clinical advice.

## License

MIT, Copyright (c) 2026 The OmiCairn Authors (see [`LICENSE`](LICENSE)). Vendored third-party code keeps its
own license (see the `THIRD_PARTY_NOTICES.md` files in `frontend/` and `worker/`).
