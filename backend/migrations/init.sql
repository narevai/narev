-- NarevAI Billing Analyzer - Database Schema
-- FOCUS 1.2 Compliant Schema

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Providers table
CREATE TABLE IF NOT EXISTS providers (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    provider_type VARCHAR(50) NOT NULL,
    display_name VARCHAR(200),
    api_endpoint VARCHAR(500),
    auth_config JSONB,
    additional_config JSON,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    is_validated BOOLEAN DEFAULT FALSE,
    last_validation_at TIMESTAMP WITH TIME ZONE,
    validation_error TEXT,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_sync_status VARCHAR(50),
    last_sync_error TEXT,
    sync_statistics JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Provider test results table
CREATE TABLE IF NOT EXISTS provider_test_results (
    id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36) NOT NULL REFERENCES providers(id),
    test_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    test_type VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    test_details JSON
);

-- Raw billing data table
CREATE TABLE IF NOT EXISTS raw_billing_data (
    id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36) NOT NULL REFERENCES providers(id),
    provider_type VARCHAR(50) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    extraction_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    extraction_params JSON,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    extracted_data JSON NOT NULL,
    record_count INTEGER DEFAULT 0,
    processed BOOLEAN DEFAULT FALSE NOT NULL,
    processed_at TIMESTAMP WITH TIME ZONE,
    processing_error TEXT,
    pipeline_run_id VARCHAR(36),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    _dlt_load_id VARCHAR(255),
    _dlt_id VARCHAR(255)
);

-- FOCUS 1.2 compliant billing data table
CREATE TABLE IF NOT EXISTS billing_data (
    id VARCHAR(36) PRIMARY KEY,
    
    -- MANDATORY: Costs
    billed_cost DECIMAL(20,10) NOT NULL,
    effective_cost DECIMAL(20,10) NOT NULL,
    list_cost DECIMAL(20,10) NOT NULL,
    contracted_cost DECIMAL(20,10) NOT NULL,
    
    -- MANDATORY: Account identification
    billing_account_id VARCHAR(255) NOT NULL,
    billing_account_name VARCHAR(500),
    billing_account_type VARCHAR(100) NOT NULL,
    sub_account_id VARCHAR(255),
    sub_account_name VARCHAR(500),
    sub_account_type VARCHAR(100),
    
    -- MANDATORY: Time periods
    billing_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    billing_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    charge_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    charge_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- MANDATORY: Currency
    billing_currency VARCHAR(10) NOT NULL,
    pricing_currency VARCHAR(10),
    
    -- MANDATORY: Services and categorization
    service_name VARCHAR(255) NOT NULL,
    service_category VARCHAR(50) NOT NULL CHECK (service_category IN (
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
    provider_name VARCHAR(100) NOT NULL,
    publisher_name VARCHAR(100) NOT NULL,
    invoice_issuer_name VARCHAR(100) NOT NULL,
    
    -- MANDATORY: Charge categorization
    charge_category VARCHAR(20) NOT NULL,
    charge_class VARCHAR(20),
    charge_description TEXT NOT NULL,
    
    -- MANDATORY: Pricing and quantities
    pricing_quantity DECIMAL(20,10),
    pricing_unit VARCHAR(100),
    
    -- CONDITIONAL: SKU and pricing
    sku_id VARCHAR(255),
    sku_price_id VARCHAR(255),
    sku_meter VARCHAR(255),
    sku_price_details TEXT,
    list_unit_price DECIMAL(20,10),
    contracted_unit_price DECIMAL(20,10),
    
    -- CONDITIONAL: Resources
    resource_id VARCHAR(500),
    resource_name VARCHAR(500),
    resource_type VARCHAR(100),
    
    -- CONDITIONAL: Location
    region_id VARCHAR(50),
    region_name VARCHAR(100),
    availability_zone VARCHAR(50),
    
    -- CONDITIONAL: Capacity Reservation
    capacity_reservation_id VARCHAR(255),
    capacity_reservation_status VARCHAR(50),
    
    -- CONDITIONAL: Commitment Discounts
    commitment_discount_id VARCHAR(255),
    commitment_discount_type VARCHAR(50),
    commitment_discount_category VARCHAR(50),
    commitment_discount_name VARCHAR(255),
    commitment_discount_status VARCHAR(50),
    commitment_discount_quantity DECIMAL(20,10),
    commitment_discount_unit VARCHAR(100),
    
    -- CONDITIONAL: Usage
    consumed_quantity DECIMAL(20,10),
    consumed_unit VARCHAR(100),
    
    -- CONDITIONAL: Tags
    tags JSON,
    
    -- CONDITIONAL: Pricing details
    pricing_category VARCHAR(100),
    pricing_currency_contracted_unit_price DECIMAL(20,10),
    pricing_currency_effective_cost DECIMAL(20,10),
    pricing_currency_list_unit_price DECIMAL(20,10),
    
    -- RECOMMENDED: Additional fields
    service_subcategory VARCHAR(100),
    charge_frequency VARCHAR(50),
    invoice_id VARCHAR(255),
    invoice_issuer VARCHAR(100),
    
    -- Provider-specific fields (x_ prefix)
    x_provider_data JSON,
    
    -- Internal tracking (x_ prefix)
    x_raw_billing_data_id VARCHAR(36) REFERENCES raw_billing_data(id),
    x_provider_id VARCHAR(36) NOT NULL REFERENCES providers(id),
    x_created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    x_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- DLT internal columns
    _dlt_load_id VARCHAR(255),
    _dlt_id VARCHAR(255),
    
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
    id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36) NOT NULL REFERENCES providers(id),
    pipeline_name VARCHAR(255) NOT NULL,
    pipeline_version VARCHAR(50),
    run_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    current_stage VARCHAR(50),
    stage_progress JSON,
    records_extracted INTEGER DEFAULT 0,
    records_transformed INTEGER DEFAULT 0,
    records_loaded INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    duration_seconds INTEGER,
    memory_usage_mb INTEGER,
    error_message TEXT,
    error_details JSON,
    failed_records JSON,
    pipeline_config JSON,
    date_range_start TIMESTAMP WITH TIME ZONE,
    date_range_end TIMESTAMP WITH TIME ZONE,
    dlt_load_id VARCHAR(255),
    dlt_pipeline_state JSON,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_providers_type ON providers(provider_type);
CREATE INDEX IF NOT EXISTS idx_providers_active ON providers(is_active);
CREATE INDEX IF NOT EXISTS idx_providers_auth_type ON providers((auth_config->>'type'));

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
