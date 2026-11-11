# Frontend

React/TypeScript (UmiJS + Ant Design) web interface of the platform.

> **Status: early-stage research software.** Some screens are incomplete or experimental
> (see *Known limitations*). It is provided as-is, without warranty.

## Quickstart

```bash
pnpm install
cp .env.example .env   # set UMI_APP_API_URL_PREFIX to your backend
pnpm dev
```

Build for production with `pnpm build` (output in `dist/`).

## Configuration

All deployment-specific settings are read from environment variables at build time
(see `.env.example`):

| Variable | Purpose | Default |
|---|---|---|
| `UMI_APP_API_URL_PREFIX` | Base URL of the HTTP gateway (see below) | `http://localhost:8099/` |
| `UMI_APP_SERVICE_CLOUD` | Object-storage backend (`AWS` = S3-compatible presigned URLs) | `AWS` |
| `UMI_APP_STATIC_RESOURCE_BASE_URL` | Base URL for UI images | `/static` |
| `UMI_APP_DEMO_FUNCTION_BLOCK_URL` | Optional example function-block download | *(hidden)* |
| `UMI_APP_SERVER_TIMEZONE` | Backend timezone for function-block timestamps | `UTC` |

UI images are not bundled; see `public/static/README.md`.

### Service topology

The UI talks to one HTTP gateway (`UMI_APP_API_URL_PREFIX`) that forwards, stripping the prefix:

| Prefix | Target |
|---|---|
| `/server/` | backend (`../backend`, Flask, port 80 in its container) |
| `/computation-server/` | worker (`../worker`, Flask, port 80 in its container) |
| `/data/` | optional data-preprocessing / attached-data service (`/pretreatment/*`, `/attached-data/*`, `/visualization/*`); not part of this release, so dataset preprocessing, cell/gene-set browsing and saved visualization data are unavailable without it |

The worker and claude-code use the same gateway (`MAIN_SERVER_HOST` / `COMPUTATION_SERVER_HOST`).
Expose only the gateway; do not publish the worker port directly (most worker endpoints are unauthenticated).

## Tests

```bash
npx jest
```

Tests live in `__tests__/`.

## Known limitations

- Self-service registration is disabled; accounts are created on the backend.
- FASTQ upload is not implemented in this release.
- Some menu entries (e.g. "Data interpretation", notebook view, shared list, snapshot gallery)
  are placeholders.
- Authentication is research-grade (token in `localStorage`, guest mode flag on the client);
  authorization must be enforced by the backend.
- The login-page background is a synthetic, decorative point cloud
  (`scripts/generate_login_background.py`).

## Third-party code

See `THIRD_PARTY_NOTICES.md`.
