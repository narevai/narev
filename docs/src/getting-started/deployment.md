---
title: "Getting Started"
order: 3
---

# Deployment Guide

This guide explains how to deploy the Narev AI Billing Analyzer
using the official Docker image.

## Prerequisites

- Docker installed on your server
- Docker Compose (recommended for easier management)
- A database (SQLite - currently the only supported database)

## Quick Start

The simplest way to get started is using Docker with SQLite.

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

## Environment Variables

### Required Security Settings

This **MUST** be changed from the default value in production:

#### `ENCRYPTION_KEY`

- **Purpose**: Used to encrypt sensitive data in the database using Fernet encryption
- **Example**: `ENCRYPTION_KEY=gAAAAABhZ...` (44 characters)
- **How to generate**:

  ```bash
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```

### Application Settings

#### `ENVIRONMENT`

- **Purpose**: Sets the application environment mode
- **Options**: `production`, `development`, `staging`
- **Default**: `development`
- **Production value**: `ENVIRONMENT=production`

#### `DEBUG`

- **Purpose**: Enables/disables debug mode
- **Options**: `true`, `false`
- **Default**: `true`
- **Production value**: `DEBUG=false`

### Database Configuration

#### `DATABASE_TYPE`

- **Purpose**: Selects which database system to use
- **Options**: `sqlite` (PostgreSQL support coming in future releases)
- **Default**: `sqlite`

#### For SQLite

#### `SQLITE_PATH`

- **Purpose**: Path where the SQLite database file will be stored
- **Default**: `./data/billing.db`
- **Example**: `SQLITE_PATH=/data/billing.db`

### Web Server Configuration

#### `HOST`

- **Purpose**: IP address the server binds to
- **Default**: `0.0.0.0` (listens on all interfaces)
- **Note**: Keep as `0.0.0.0` for Docker deployments

#### `PORT`

- **Purpose**: Port the application listens on inside the container
- **Default**: `8000`
- **Note**: Map this to your desired external port using Docker's `-p` flag

### Frontend Configuration

#### `VITE_API_URL`

- **Purpose**: URL where the frontend can reach the backend API
- **Default**: `http://backend:8000`
- **Production example**: `VITE_API_URL=https://billing.yourdomain.com`

#### `VITE_APP_NAME`

- **Purpose**: Application name displayed in the UI
- **Default**: `Narev AI Dashboard`
- **Example**: `VITE_APP_NAME="My Company Billing"`

#### `VITE_PORT`

- **Purpose**: Port for the Vite development server
- **Default**: `5173`

#### `VITE_HOST`

- **Purpose**: Host for the Vite development server
- **Default**: `0.0.0.0`

### Logging Configuration

#### `LOG_LEVEL`

- **Purpose**: Controls the verbosity of application logs
- **Options**: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Default**: `INFO`
- **Production recommendation**: `INFO` or `WARNING`

#### `LOG_TO_FILE`

- **Purpose**: Whether to save logs to a file
- **Options**: `true`, `false`
- **Default**: `true`

#### `LOG_FILE_PATH`

- **Purpose**: Where to save log files
- **Default**: `logs/app.log`
- **Docker note**: Mount a volume to persist logs

### DLT Configuration

#### `DLT_PROJECT_DIR`

- **Purpose**: Directory for DLT project configuration
- **Default**: `.dlt`
- **Note**: DLT (Data Load Tool) project directory for ETL operations

#### `DLT_DATA_DIR`

- **Purpose**: Directory for DLT data storage
- **Default**: `.dlt/data`
- **Note**: Where DLT stores temporary data during processing

### API Configuration

#### `API_TITLE`

- **Purpose**: Title displayed in API documentation
- **Default**: `NarevAI Billing Analyzer`

#### `API_DESCRIPTION`

- **Purpose**: Description shown in API documentation
- **Default**: `FOCUS 1.2 compliant billing data analyzer for cloud and SaaS providers`

#### `API_VERSION`

- **Purpose**: API version string
- **Default**: `1.0.0`

#### `FOCUS_VERSION`

- **Purpose**: FOCUS specification version supported
- **Default**: `1.2`
- **Note**: Version of the FinOps Open Cost and Usage Specification

### Security Settings

#### `CORS_ORIGINS`

- **Purpose**: Which domains can access the API from browsers
- **Format**: JSON array of URLs
- **Default**: `["http://localhost:8000","http://localhost:3000"]`
- **Production example**: `CORS_ORIGINS=["https://billing.yourdomain.com"]`

### Demo Mode

#### `DEMO`

- **Purpose**: Populates database with sample billing data and pipeline runs on startup for demonstration purposes
- **Options**: `true`, `false`
- **Default**: `false`
- **When to use**: 
  - Testing the application with realistic data
  - Demonstrations and presentations
  - Development when you need sample data
- **Note**: When enabled, the application will automatically import sample billing records and pipeline run history from CSV files on first startup. Provider configurations must still be set up manually through the application interface.

## Deployment Examples

### Production Deployment with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: "3.8"

services:
  app:
    image: ghcr.io/narevai/narev:latest
    container_name: narev-billing
    ports:
      - "8000:8000"
    environment:
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
      ENVIRONMENT: production
      DATABASE_TYPE: sqlite
      SQLITE_PATH: /data/billing.db
      VITE_API_URL: https://billing.yourdomain.com
      VITE_APP_NAME: "Company Billing Analyzer"
      LOG_LEVEL: INFO
      LOG_TO_FILE: true
      CORS_ORIGINS: '["https://billing.yourdomain.com"]'
      DEMO: false
    volumes:
      - billing_data:/data
      - billing_logs:/app/logs
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  billing_data:
  billing_logs:
```

Create an `.env` file (never commit this to version control!):

```bash
# Security Key (generate new one!)
ENCRYPTION_KEY=your-generated-fernet-key-here
```

Deploy:

```bash
docker-compose up -d
```

## Demo Mode

The application includes a demo mode that automatically populates the database with sample data for testing and demonstration purposes.

### Enabling Demo Mode

To enable demo mode, set the `DEMO` environment variable to `true`:

```bash
# In your .env file or environment
DEMO=true
```

### What Demo Mode Includes

When demo mode is enabled, the application will automatically populate the database with:

- **Sample billing data**: Realistic cloud billing records with various services and usage patterns imported from CSV
- **Pipeline run history**: Sample ETL pipeline execution records showing data processing history

**Note**: Demo mode does not create provider configurations - these must be set up manually through the application interface.

### Use Cases

- **Product demonstrations**: Quickly show the application's capabilities without real data
- **Development testing**: Work with realistic data during development
- **Training and onboarding**: Help new users understand the application's features
- **CI/CD testing**: Automated testing with consistent sample data

### Important Notes

- Demo data is imported only on the first startup when the database is empty
- Demo mode should **never** be enabled in production environments
- The sample data is anonymized and contains no real billing information
- Demo data comes from pre-generated CSV files in the scripts directory
- Demo data can be cleared by resetting the database
- Provider configurations are not included in demo mode and must be configured manually

## Security Checklist

Before deploying to production:

### Required Security Configuration

- **Generate a new `ENCRYPTION_KEY`**  
  Use: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

- **Set `ENVIRONMENT=production`**  
  Enables production optimizations and security settings

- **Debug mode is disabled by default**  
  No need to explicitly set `DEBUG=false` - it's already the default

- **Set `DEMO=false`**  
  Ensures demo mode is disabled in production

### Network Security

- **Configure `CORS_ORIGINS`**  
  Set to your actual domain(s) only: `["https://yourdomain.com"]`

- **Use HTTPS for all external URLs**  
  Ensure all `VITE_API_URL` and other URLs use HTTPS

### Database Security

- **Set up regular database backups**  
  Configure automated backups for your SQLite database file

- **Secure file permissions**  
  Ensure proper access controls on the SQLite database file

### Operational Security

- **Configure log rotation**  
  Prevent log files from consuming excessive disk space

- **Review and secure file permissions**  
  Ensure proper access controls on data directories

## Updating

To update to a newer version:

```bash
# Pull the latest image
docker pull ghcr.io/narevai/narev:latest

# Restart the container
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Check Application Logs

```bash
docker logs narev-billing
```

### Verify Health Status

```bash
curl http://localhost:8000/health
```

### Access Container Shell

```bash
docker exec -it narev-billing /bin/bash
```
