-- NarevAI Billing Analyzer - SQLite Database Schema
-- FOCUS 1.2 Compliant Schema

-- Providers table
CREATE TABLE IF NOT EXISTS providers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    provider_type TEXT NOT NULL,
    display_name TEXT,
    api_endpoint TEXT,
    auth_config TEXT,
    additional_config TEXT,
    is_active INTEGER DEFAULT 1 NOT NULL,
    is_validated INTEGER DEFAULT 0,
    last_validation_at TIMESTAMP,
    validation_error TEXT,
    last_sync_at TIMESTAMP,
    last_sync_status TEXT,
    last_sync_error TEXT,
    sync_statistics TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    updated_by TEXT
);

-- Provider test results table
CREATE TABLE IF NOT EXISTS provider_test_results (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL REFERENCES providers(id),
    test_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    test_type TEXT NOT NULL,
    success INTEGER NOT NULL,
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    test_details TEXT
);

-- Raw billing data table
CREATE TABLE IF NOT EXISTS raw_billing_data (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL REFERENCES providers(id),
    provider_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    extraction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_params TEXT,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    extracted_data TEXT NOT NULL,
    record_count INTEGER DEFAULT 0,
    processed INTEGER DEFAULT 0 NOT NULL,
    processed_at TIMESTAMP,
    processing_error TEXT,
    pipeline_run_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    _dlt_load_id TEXT,
    _dlt_id TEXT
);

-- FOCUS 1.2 compliant billing data table
CREATE TABLE IF NOT EXISTS billing_data (
    id TEXT PRIMARY KEY,
    
    -- MANDATORY: Costs
    billed_cost REAL NOT NULL,
    effective_cost REAL NOT NULL,
    list_cost REAL NOT NULL,
    contracted_cost REAL NOT NULL,
    
    -- MANDATORY: Account identification
    billing_account_id TEXT NOT NULL,
    billing_account_name TEXT,
    billing_account_type TEXT NOT NULL,
    sub_account_id TEXT,
    sub_account_name TEXT,
    sub_account_type TEXT,
    
    -- MANDATORY: Time periods
    billing_period_start TIMESTAMP NOT NULL,
    billing_period_end TIMESTAMP NOT NULL,
    charge_period_start TIMESTAMP NOT NULL,
    charge_period_end TIMESTAMP NOT NULL,
    
    -- MANDATORY: Currency
    billing_currency TEXT NOT NULL,
    pricing_currency TEXT,
    
    -- MANDATORY: Services and categorization
    service_name TEXT NOT NULL,
    service_category TEXT NOT NULL CHECK (service_category IN (
        'AI and Machine Learning',
        'Analytics',
        'Compute',
        'Databases',
        'Developer Tools',
        'Management and Governance',
        'Networking',
        'Security, Identity, and Compliance',
        'Storage',
        'Other'
    )),
    provider_name TEXT NOT NULL,
    publisher_name TEXT NOT NULL,
    invoice_issuer_name TEXT NOT NULL,
    
    -- MANDATORY: Charge categorization
    charge_category TEXT NOT NULL,
    charge_class TEXT,
    charge_description TEXT NOT NULL,
    
    -- MANDATORY: Pricing and quantities
    pricing_quantity REAL,
    pricing_unit TEXT,
    
    -- CONDITIONAL: SKU and pricing
    sku_id TEXT,
    sku_price_id TEXT,
    sku_meter TEXT,
    sku_price_details TEXT,
    list_unit_price REAL,
    contracted_unit_price REAL,
    
    -- CONDITIONAL: Resources
    resource_id TEXT,
    resource_name TEXT,
    resource_type TEXT,
    
    -- CONDITIONAL: Location
    region_id TEXT,
    region_name TEXT,
    availability_zone TEXT,
    
    -- CONDITIONAL: Capacity Reservation
    capacity_reservation_id TEXT,
    capacity_reservation_status TEXT,
    
    -- CONDITIONAL: Commitment Discounts
    commitment_discount_id TEXT,
    commitment_discount_type TEXT,
    commitment_discount_category TEXT,
    commitment_discount_name TEXT,
    commitment_discount_status TEXT,
    commitment_discount_quantity REAL,
    commitment_discount_unit TEXT,
    
    -- CONDITIONAL: Usage
    consumed_quantity REAL,
    consumed_unit TEXT,
    
    -- CONDITIONAL: Tags
    tags TEXT,
    
    -- CONDITIONAL: Pricing details
    pricing_category TEXT,
    pricing_currency_contracted_unit_price REAL,
    pricing_currency_effective_cost REAL,
    pricing_currency_list_unit_price REAL,
    
    -- RECOMMENDED: Additional fields
    service_subcategory TEXT,
    charge_frequency TEXT,
    invoice_id TEXT,
    invoice_issuer TEXT,
    
    -- Provider-specific fields (x_ prefix)
    x_provider_data TEXT,
    
    -- Internal tracking (x_ prefix)
    x_raw_billing_data_id TEXT REFERENCES raw_billing_data(id),
    x_provider_id TEXT NOT NULL REFERENCES providers(id),
    x_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    x_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- DLT internal columns
    _dlt_load_id TEXT,
    _dlt_id TEXT,
    
    -- Constraints
    CONSTRAINT ck_billing_period_valid CHECK (billing_period_end > billing_period_start),
    CONSTRAINT ck_charge_period_valid CHECK (charge_period_end > charge_period_start),
    CONSTRAINT ck_costs_non_negative CHECK (
        effective_cost >= 0 AND billed_cost >= 0 AND list_cost >= 0 AND contracted_cost >= 0
    ),
    CONSTRAINT ck_pricing_quantity_non_negative CHECK (pricing_quantity IS NULL OR pricing_quantity >= 0),
    CONSTRAINT ck_consumed_quantity_non_negative CHECK (consumed_quantity IS NULL OR consumed_quantity >= 0)
);

-- Pipeline runs table
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL REFERENCES providers(id),
    pipeline_name TEXT NOT NULL,
    pipeline_version TEXT,
    run_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    current_stage TEXT,
    stage_progress TEXT,
    records_extracted INTEGER DEFAULT 0,
    records_transformed INTEGER DEFAULT 0,
    records_loaded INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    memory_usage_mb INTEGER,
    error_message TEXT,
    error_details TEXT,
    failed_records TEXT,
    pipeline_config TEXT,
    date_range_start TIMESTAMP,
    date_range_end TIMESTAMP,
    dlt_load_id TEXT,
    dlt_pipeline_state TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_providers_type ON providers(provider_type);
CREATE INDEX IF NOT EXISTS idx_providers_active ON providers(is_active);

CREATE INDEX IF NOT EXISTS idx_provider_test_results_provider ON provider_test_results(provider_id);
CREATE INDEX IF NOT EXISTS idx_provider_test_results_timestamp ON provider_test_results(test_timestamp);

CREATE INDEX IF NOT EXISTS idx_raw_billing_provider_period ON raw_billing_data(provider_id, period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_raw_billing_processed ON raw_billing_data(processed);
CREATE INDEX IF NOT EXISTS idx_raw_billing_created ON raw_billing_data(created_at);
CREATE INDEX IF NOT EXISTS idx_raw_billing_source ON raw_billing_data(source_name, source_type);
CREATE INDEX IF NOT EXISTS idx_raw_billing_pipeline ON raw_billing_data(pipeline_run_id);

CREATE INDEX IF NOT EXISTS idx_billing_provider_period ON billing_data(x_provider_id, charge_period_start, charge_period_end);
CREATE INDEX IF NOT EXISTS idx_billing_service_category ON billing_data(service_category);
CREATE INDEX IF NOT EXISTS idx_billing_costs ON billing_data(effective_cost);
CREATE INDEX IF NOT EXISTS idx_billing_sku ON billing_data(sku_id);
CREATE INDEX IF NOT EXISTS idx_billing_created ON billing_data(x_created_at);
CREATE INDEX IF NOT EXISTS idx_billing_account ON billing_data(billing_account_id);
CREATE INDEX IF NOT EXISTS idx_billing_charge_period ON billing_data(charge_period_start, charge_period_end);
CREATE INDEX IF NOT EXISTS idx_billing_service_name ON billing_data(service_name);
CREATE INDEX IF NOT EXISTS idx_billing_resource ON billing_data(resource_id);
CREATE INDEX IF NOT EXISTS idx_billing_region ON billing_data(region_id);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_provider_status ON pipeline_runs(provider_id, status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started ON pipeline_runs(started_at);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_type ON pipeline_runs(run_type);
