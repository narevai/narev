import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

# Add backend to path to import app modules
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.config import settings

# Paths to CSV files
csv_billing_data_path = script_dir / "billing_data.csv"
csv_pipeline_runs_path = script_dir / "pipeline_runs.csv"

print(f"Database Type: {settings.database_type}")
print(f"Database URL: {settings.database_url}")
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

# Create database engine using app configuration
engine = create_engine(settings.database_url)

try:
    # Import data to database (works for both SQLite and PostgreSQL)
    df_billing_data.to_sql('billing_data', engine, if_exists='append', index=False)
    df_pipeline_runs.to_sql('pipeline_runs', engine, if_exists='append', index=False)
    
    print(f"Data imported successfully to {settings.database_type} database.")
    print(f"- Imported {len(df_billing_data)} billing records")
    print(f"- Imported {len(df_pipeline_runs)} pipeline run records")

except Exception as e:
    print(f"ERROR importing data: {e}")
    sys.exit(1)

finally:
    engine.dispose()
