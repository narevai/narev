# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-08-31

### Changed

- Renamed the project from `thin-ops` to `varne` across packages, UI, API defaults, README, and contributor docs.
- Renamed backend package from `thin-ops-api` to `varne-api` and frontend/docs packages to `varne` / `varne-docs`.
- Moved Mintlify documentation from `docs/oss/thinops/` to `docs/oss/varne/` and updated nav paths, internal links, and GitHub references to `narevai/varne`.
- Updated Docker image references to `ghcr.io/narevai/varne` and container names to `varne` / `varne-demo`.
- Replaced remaining `Narev` / `NarevAI` product branding in the UI and docs with `Varne`.

### Security

- Bumped `cryptography` in the backend (48.0.1 → 50.0.0).

### Dependencies

- Updated GitHub Actions: `actions/setup-python` v6 → v7, `actions/stale` v10 → v11.

**`backend/`**

- `fastapi` 0.139.0 → 0.141.1
- `uvicorn[standard]` 0.51.0 → 0.52.4
- `sqlalchemy` 2.0.51 → 2.0.52
- `pydantic` 2.13.4 → 2.13.5
- `pydantic-settings` 2.14.2 → 2.15.0
- `dlt[sqlalchemy,postgres,filesystem,az]` 1.29.0 → 1.30.0
- `cryptography` 48.0.1 → 50.0.0
- `google-cloud-bigquery` 3.42.2 → 3.44.0
- `google-cloud-bigquery-storage` 2.39.0 → 2.41.0
- `azure-storage-blob` 12.30.0 → 12.30.1

**`frontend/`**

- Lockfile updates across the toolchain, including `react` 19.2.7 → 19.2.8, `vite` 8.1.4 → 8.2.2, `axios` 1.18.1 → 1.20.0, `react-hook-form` 7.81.0 → 7.87.0, `zod` 4.4.3 → 4.5.4, and TanStack packages.

## [0.4.0] - 2026-07-18

### Changed

- Migrated documentation from VitePress to Mintlify; content now lives under `docs/oss/thinops/` as MDX.
- CI docs job runs Mintlify broken-link checks instead of a VitePress build.
- Added root `.npmrc` with a shared pnpm store path for the dev container.

### Fixed

- Made the `.env` file optional in the dev container Docker Compose setup, so the stack starts without one.

### Security

- Bumped `pydantic-settings` in the backend (2.14.1 → 2.14.2).
- Bumped `cryptography` in the backend (46.0.7 → 48.0.1).

### Dependencies

- Updated `pnpm` to v10.34.5.
- Updated GitHub Actions: `actions/checkout` v6 → v7, `actions/setup-node` v6 → v7.

**`backend/`**

- `fastapi` 0.136.1 → 0.139.0
- `uvicorn[standard]` 0.47.0 → 0.51.0
- `sqlalchemy` 2.0.49 → 2.0.51
- `pydantic-settings` 2.14.1 → 2.14.2
- `dlt[sqlalchemy,postgres,filesystem,az]` 1.27.0 → 1.29.0
- `cryptography` 46.0.7 → 48.0.1
- `google-cloud-bigquery` 3.41.0 → 3.42.2
- `google-cloud-bigquery-storage` 2.38.0 → 2.39.0
- `azure-storage-blob` 12.29.0 → 12.30.0

**`frontend/`**

- Lockfile updates across the toolchain, including `react` 19.2.6 → 19.2.7, `vite` 8.0.13 → 8.1.4, `axios` 1.16.1 → 1.18.1, `tailwindcss` 4.3.0 → 4.3.2, `eslint` 9.39.4 → 9.39.5, Radix UI components, and TanStack packages.

**`docs/`**

- Replaced VitePress with Mintlify CLI (`mintlify@4.2.510`); removed VitePress dependencies and lockfile.


## [0.3.0] - 2026-05-22

### Changed

- Renamed the project from `narev` to `thin-ops`.


## [0.2.7] - 2026-05-19

### Changed

- Added Docker Compose setup instructions to the README

### Dependencies

- Updated frontend npm dependencies
- Updated backend Python dependencies


## [0.2.6] - 2026-05-14

### Changed

- Migrated and split Renovate configuration by package manager

### Dependencies

- Updated `pnpm` to v10.33.4
- Updated npm, Python, and GitHub Actions dependencies


## [0.2.5] - 2026-05-13

### Security

- Bumped `cryptography` in the backend (46.0.3 → 46.0.7) to stay on the latest patch line from the dependency graph.
- Added pnpm overrides in `frontend/` for `seroval`, `seroval-plugins`, and `picomatch`, pinning transitive versions that were flagged in audits so the lockfile resolves to patched releases.

### Changed

- Consolidated the dev container setup: one `Dockerfile.dev`, a single root `devcontainer.json`, and a slimmer `docker-compose` instead of separate backend, docs, and frontend devcontainer stacks.
- Refreshed `CONTRIBUTING.md` and `.vscode/settings.json` to match the unified dev environment.

### Dependencies

**`backend/`**

- `cryptography` 46.0.3 → 46.0.7

**`frontend/`**

- pnpm overrides: `seroval` ^1.4.1, `seroval-plugins` ^1.4.1, `picomatch` ^4.0.4 (with lockfile updates; e.g. `seroval-plugins` resolves to 1.5.4)
- Related lockfile deduplication for `picomatch` and the seroval toolchain

## [0.2.4] - 2026-05-12

### Security

- Bumped the Dependabot `npm_and_yarn` dependency group in `docs/` and `frontend/` to pull in current patch and minor releases across the toolchain (build, parsing, and HTTP stack), reducing exposure to known issues in older transitive versions.

### Dependencies

**`docs/`**

- `mdast-util-to-hast` 13.2.0 → 13.2.1
- `minimatch` 9.0.5 → 9.0.9
- `picomatch` 4.0.3 → 4.0.4
- `postcss` 8.5.6 → 8.5.14
- `preact` 10.26.9 → 10.29.1
- `rollup` 4.45.1 → 4.60.3
- `vite` 7.0.5 → 7.3.3

**`frontend/`**

- `axios` 1.13.2 → 1.15.2
- `vite` 7.0.8 → 7.3.2
- `flatted` 3.3.3 → 3.4.2
- `lodash` 4.17.21 → 4.18.1
- `minimatch` 3.1.2 → 3.1.5
- `tar` 7.4.3 → 7.5.15
- Transitive updates included in the same bump: `follow-redirects` 1.15.11 → 1.16.0, `picomatch` 2.3.1 → 2.3.2, `postcss` 8.5.6 → 8.5.14, `rollup` 4.52.5 → 4.60.3

### Fixed

- Adjusted CI so the pipeline passes with the updated dependency set.


## [0.2.3] - 2025-11-22

### Security
- Updated transitive `js-yaml` dependency to 4.1.1 using pnpm overrides to address CVE-2025-64718 (prototype pollution vulnerability in dev dependencies)

### Changed
- Disabled Dependabot for docs directory

### Dependencies
- Updated frontend dependencies: React, Axios, Radix UI components, Tailwind CSS, ESLint, and icon libraries
- Updated backend dependencies: FastAPI, Uvicorn, Pydantic, Google Cloud BigQuery Storage, and Cryptography
- Updated GitHub Actions: `actions/checkout` from v5 to v6


## [0.2.2] - 2025-11-02

### Added
- Zustand state management and persistent filters

### Fixed
- Show inactive providers in Connect menu


## [0.2.1] - 2025-11-01

### Added
- Support for multiple accounts per provider

### Changed
- Removed redundant port forwarding in dev container
- Removed labels from dependabot configuration

### Documentation
- Updated documentation links in README

### Dependencies
- Updated `vite` from 7.0.6 to 7.0.8 in frontend
- Updated `axios` from 1.10.0 to 1.12.0 in frontend
- Updated `prettier` from 3.6.0 to 3.6.2 in frontend
- Updated `dlt[az,filesystem,postgres,sqlalchemy]` from 1.13.0 to 1.18.1 in backend
- Updated GitHub Actions: `actions/upload-artifact` from v4 to v5
- Updated GitHub Actions: `actions/download-artifact` from v5 to v6


## [0.2.0] - 2025-10-30

### Added
- Data export pipeline with destination management
- Edit dialog for modifying entries
- Dynamic filtering on the cost dashboard

### Fixed
- Removed Dockerfile layer caching

### Dependencies
- Updated `@eslint/js` from 9.29.0 to 9.32.0
- Updated `sonner` from 2.0.5 to 2.0.6
- Updated `@vitejs/plugin-react-swc` from 3.10.2 to 3.11.0
- Updated GitHub Actions: `actions/download-artifact` from v4 to v5
- Updated GitHub Actions: `actions/checkout` from v4 to v5

## [0.1.1] - 2025-07-28

### Security
- Fixed `form-data` vulnerability (unsafe random function in boundary generation)
- Fixed `@eslint/plugin-kit` vulnerability (Regular Expression Denial of Service)

### Fixed
- Disabled ESLint warnings for functions defined inside React components
- Removed redundant dependency to prevent refresh loops
- Configured Dependabot to ignore Python 3.13 updates, keeping project on Python 3.12 (#19) for stability

### Dependencies
- Updated `vite` from 7.0.2 to 7.0.6
- Updated `prettier-plugin-tailwindcss` from 0.6.13 to 0.6.14
- Updated `actions/stale` workflow from v5 to v9 for improved GitHub Actions performance

## [0.1.0] - 2025-07-25

### Added

- **Complete analytics platform**: Full analytics API with 20+ FOCUS use cases endpoints and dashboard with comprehensive charts
- **Multi-cloud provider support**: Azure, AWS, GCP and OpenAI provider integration with multiple authentication methods
- **FOCUS 1.2 compliance**: Updated data pipeline and mappers to FOCUS 1.2 standard
- **Data export capabilities**: CSV and Excel export functionality
- **Demo mode**: Complete demo mode for testing and demonstrations
- **Frontend provider management**: UI for adding and managing cloud providers
- **Hamilton orchestration**: Integrated Hamilton for ETL pipeline management
- **OpenAPI specification**: Complete API documentation
- **Development infrastructure**: Dev containers, enhanced CI/CD, and comprehensive ETL tests
