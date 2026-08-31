# Varne

[![GitHub last commit](https://img.shields.io/github/last-commit/narevai/varne)](https://github.com/narevai/varne/commits)
[![Latest tag](https://img.shields.io/github/v/tag/narevai/varne?label=latest)](https://github.com/narevai/varne/tags)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

## Run

```bash
docker run -d \
  --name varne \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  ghcr.io/narevai/varne:latest
```

Open http://localhost:8000.

## Docker Compose

```yaml
services:
  varne:
    image: ghcr.io/narevai/varne:latest
    container_name: varne
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

```bash
docker compose up -d
```

Open http://localhost:8000.

## License

GNU Affero General Public License v3.0. See [LICENSE](./LICENSE).
