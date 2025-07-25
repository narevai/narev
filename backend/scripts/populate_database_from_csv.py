import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

from app.config import settings

# Paths to CSV files
script_dir = Path(__file__).resolve().parent
csv_billing_data_path = script_dir / "billing_data_synthetic_12m.csv"
csv_pipeline_runs_path = script_dir / "pipeline_runs.csv"

# Only run in demo mode
if not settings.demo:
    print("❌ This script only runs in DEMO mode")
    print("Set DEMO=true in .env to populate demo database")
    sys.exit(1)

print(f"Database Type: {settings.database_type}")
print(f"Demo Database URL: {settings.demo_database_url}")
print(f"CSV Billing Data PATH: {csv_billing_data_path}")
print(f"CSV Pipeline Runs PATH: {csv_pipeline_runs_path}")

# Check if CSV files exist
if not csv_billing_data_path.exists():
    print(f"ERROR: Billing data CSV not found: {csv_billing_data_path}")
    sys.exit(1)

if not csv_pipeline_runs_path.exists():
    print(f"ERROR: Pipeline runs CSV not found: {csv_pipeline_runs_path}")
    sys.exit(1)

# Load CSV data
df_billing_data = pd.read_csv(csv_billing_data_path)
df_pipeline_runs = pd.read_csv(csv_pipeline_runs_path)

print(f"Loaded {len(df_billing_data)} billing records")
print(f"Loaded {len(df_pipeline_runs)} pipeline run records")

# Create database engine using demo database configuration
demo_database_url = settings.demo_database_url
engine = create_engine(demo_database_url)

print(f"Using demo database: {demo_database_url}")

try:
    # Create hardcoded demo providers based on billing_data.csv
    provider_data = [
        {
            "id": "16930d27-0405-4f26-a368-28ea0f88fee7",
            "name": "demo_aws",
            "provider_type": "aws",
            "display_name": "Demo Amazon Web Services",
            "is_active": True,
            "is_validated": True,
            "created_at": "2025-07-23 14:30:00",
            "updated_at": "2025-07-23 14:30:00",
        },
        {
            "id": "b8865cfb-a35f-4d8a-ac59-77f8b8b8ba11",
            "name": "demo_azure",
            "provider_type": "azure",
            "display_name": "Demo Microsoft Azure",
            "is_active": True,
            "is_validated": True,
            "created_at": "2025-07-23 14:30:00",
            "updated_at": "2025-07-23 14:30:00",
        },
        {
            "id": "11cfecab-590d-43a6-8d89-20e79bea59ea",
            "name": "demo_gcp",
            "provider_type": "gcp",
            "display_name": "Demo Google Cloud",
            "is_active": True,
            "is_validated": True,
            "created_at": "2025-07-23 14:30:00",
            "updated_at": "2025-07-23 14:30:00",
        },
        {
            "id": "61c8abe2-9881-4d71-882f-488794916ce5",
            "name": "demo_gcp_2",
            "provider_type": "gcp",
            "display_name": "Demo Google Cloud 2",
            "is_active": True,
            "is_validated": True,
            "created_at": "2025-07-23 14:30:00",
            "updated_at": "2025-07-23 14:30:00",
        },
    ]

    # Import providers first
    if provider_data:
        df_providers = pd.DataFrame(provider_data)
        try:
            df_providers.to_sql("providers", engine, if_exists="append", index=False)
            print(f"- Created {len(provider_data)} demo providers")
        except Exception as e:
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                print("- Providers already exist (skipping)")
            else:
                raise e

    # Fix data types for PostgreSQL compatibility
    if "_dlt_load_id" in df_billing_data.columns:
        df_billing_data["_dlt_load_id"] = df_billing_data["_dlt_load_id"].astype(str)

    # Import billing data and pipeline runs
    billing_rows = df_billing_data.to_sql(
        "billing_data", engine, if_exists="append", index=False
    )
    pipeline_rows = df_pipeline_runs.to_sql(
        "pipeline_runs", engine, if_exists="append", index=False
    )

    print(f"Data imported successfully to {settings.database_type} database.")
    print(f"- Imported {len(df_billing_data)} billing records")
    print(f"- Imported {len(df_pipeline_runs)} pipeline run records")

except Exception as e:
    error_msg = str(e).lower()
    if "unique constraint" in error_msg or "duplicate" in error_msg:
        print("⚠️  Data already exists in database (duplicate records detected)")
        print("Demo data is already populated - skipping import")
    else:
        print(f"ERROR importing data: {e}")
        sys.exit(1)

finally:
    engine.dispose()
