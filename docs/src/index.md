---
title: "Welcome"
---

# Welcome to NarevAI ! 👋

Open source cloud cost optimization platform. Transform your multi-cloud spending with unified analytics, real-time insights, and actionable recommendations.

## What is NarevAI?

NarevAI is a **self-hosted FinOps platform** that helps organizations:
- **Unify multi-cloud costs** across AWS, Azure, GCP, and AI services
- **Analyze spending patterns** with FOCUS-compliant data standardization  
- **Optimize costs** through intelligent recommendations and insights
- **Maintain privacy** with full data control on your infrastructure

---

## 🚀 Getting Started

#### Demo Mode (Try it now!)

Want to explore NarevAI with sample data? Start with demo mode - no setup required:

```bash
docker run -d \
  --name narev-billing-demo \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e DEMO="true" \
  ghcr.io/narevai/narev:latest
```

✅ **NarevAI is now running at: `http://localhost:8000`**

**Demo mode includes:**
- Sample billing data from AWS, Azure, and GCP
- Realistic usage patterns and cost data
- Pipeline run history
- **No encryption key needed!** Demo mode automatically generates one for you.

#### Production Setup

Ready for your real data? Deploy with your own encryption key:

First, generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Then run the container with your generated key:

```bash
docker run -d \
  --name narev-billing \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e ENCRYPTION_KEY="gAAAAABhZ_your_actual_generated_key_here" \
  -e ENVIRONMENT="production" \
  ghcr.io/narevai/narev:latest
```

#### Advanced Deployment

For production environments with Docker Compose and advanced configuration:
**[View Deployment Guide →](./getting-started/deployment.md)**

### Step 2: Connect Your Data

Now that NarevAI is running, add your cloud providers:
**[Connect Providers Guide →](./connect-providers/)**

Supported: AWS, Azure, GCP, and OpenAI

### Step 3: Import Billing Data

Sync your historical cost data for analysis:
**[Sync Providers Guide →](./getting-started/sync-providers.md)**

---

**Next:** Once your data is syncing, explore NarevAI's cost analytics and optimization features in the application.

## Need Help?

Get community support and ask questions:
**[GitHub Discussions →](https://github.com/narevai/narev/discussions)**

---

Start optimizing your cloud costs in minutes. No data leaves your infrastructure.
