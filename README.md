# NarevAI Billing Analyzer

**Master the AI and cloud cost-speed-quality tradeoff with unified analytics.**

[![GitHub last commit](https://img.shields.io/github/last-commit/narevai/narev)](https://github.com/narevai/narev/commits)
[![GitHub repo size](https://img.shields.io/github/repo-size/narevai/narev)](https://github.com/narevai/narev)
[![Image size](https://ghcr-badge.egpl.dev/narevai/narev/size)](https://github.com/narevai/narev/pkgs/container/narev)
[![Latest version](https://ghcr-badge.egpl.dev/narevai/narev/latest_tag?trim=major&label=latest)](https://github.com/narevai/narev/pkgs/container/narev)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

NarevAI is an open source, self-hosted FinOps platform for analyzing and optimizing your AI and cloud spend. It unifies cost and usage data from AWS, Azure, GCP, and OpenAI, providing real-time dashboards, FOCUS-compliant analytics, and actionable recommendations—all while keeping your data private and under your control.

---

## Features

- **Multi-Cloud & AI Support:** Analyze costs across AWS, Azure, GCP, and OpenAI.
- **FOCUS-Compliant:** Standardizes data using the FinOps Open Cost and Usage Specification.
- **Self-Hosted:** Your data, your infrastructure—no third-party sharing.
- **Real-Time Insights:** Live dashboards, usage breakdowns, and actionable recommendations.

## Quick Start

**Demo Mode (with sample data):**
```bash
docker run -d \
  --name narev-billing-demo \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DEMO="true" \
  ghcr.io/narevai/narev:latest
open http://localhost:8000
```

**Production:**
```bash
docker run -p 8000:8000 ghcr.io/narevai/narev:latest
open http://localhost:8000
```

- Try [Demo Mode](https://www.narev.ai/docs/) with sample data—no setup required.
- For production, see the [Deployment Guide](https://www.narev.ai/docs/getting-started/deployment.html).

---

## License

Apache 2.0

---

## Acknowledgments

Thanks to [@satnaing](https://github.com/satnaing) for the excellent [front end starter](https://github.com/satnaing/shadcn-admin/tree/main)
