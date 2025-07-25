---
title: "FOCUS Specification"
order: 4
---

# FOCUS 1.2 Specification

The **FinOps Open Cost and Usage Specification (FOCUS)** is an open specification that defines a consistent format for cloud cost and usage datasets. Narev AI Billing Analyzer is fully compliant with FOCUS 1.2, ensuring standardized billing data across all cloud providers.

## What is FOCUS?

FOCUS creates a common language for cloud costs across all cloud providers, vendors, and tools. It eliminates the need for FinOps practitioners to spend time figuring out what different cost fields mean across different provider invoices.

### Key Benefits

- **Standardized terminology**: Common definitions across all providers
- **Reduced data normalization**: Less time spent on data preparation
- **Multi-vendor support**: Single schema for all cloud providers
- **Invoice reconciliation**: Direct links to provider invoices
- **Virtual currency support**: Credits and tokens tracking

## FOCUS 1.2 Features

### Enhanced Provider Support
- **SaaS and PaaS billing**: Expanded beyond traditional cloud providers
- **Multi-currency support**: Convert between national currencies
- **Virtual currencies**: Track credits, tokens, and other virtual currencies

### Invoice Integration
- **Invoice reconciliation**: Direct linkage to provider invoices
- **Billing account granularity**: Enhanced account and sub-account details
- **Charge-back optimization**: Streamlined cost allocation

## Field Categories

FOCUS 1.2 defines fields in four categories:

### Mandatory Fields
These fields must be present in every FOCUS-compliant dataset:

#### Cost Fields
- **BilledCost**: Cost as shown on the invoice
- **EffectiveCost**: Amortized cost after applying discounts and commitments
- **ListCost**: Cost at public list prices without any discounts
- **ContractedCost**: Cost at negotiated contract prices

#### Account Identification
- **BillingAccountId**: Account that receives the invoice
- **BillingAccountName**: Display name of the billing account
- **BillingAccountType**: Type of billing account (e.g., individual, enterprise)

#### Time Periods
- **BillingPeriodStart**: Start of the billing period (inclusive)
- **BillingPeriodEnd**: End of the billing period (exclusive)
- **ChargePeriodStart**: Start of the charge period (inclusive)
- **ChargePeriodEnd**: End of the charge period (exclusive)

#### Services and Providers
- **ServiceName**: Name of the service that generated the charge
- **ServiceCategory**: Standardized service category (Compute, Storage, etc.)
- **ProviderName**: Entity that provided the resources
- **PublisherName**: Entity that produced the resources
- **InvoiceIssuerName**: Entity responsible for invoicing

#### Charges and Pricing
- **ChargeCategory**: Type of charge (Usage, Purchase, Tax, Credit, Adjustment)
- **ChargeDescription**: Human-readable description of the charge
- **PricingQuantity**: Quantity used for pricing calculations
- **PricingUnit**: Unit of measurement for pricing

#### Currency
- **BillingCurrency**: Currency code for the billed amount

### Conditional Fields
These fields are required when certain conditions are met:

#### Sub-Account Information
- **SubAccountId**: Required when sub-accounts exist
- **SubAccountName**: Display name when SubAccountId is present
- **SubAccountType**: Type when SubAccountId is present

#### Resource Details
- **ResourceId**: Required for resource-based billing
- **ResourceName**: Display name when ResourceId is present
- **ResourceType**: Type when ResourceId is present

#### Location Information
- **RegionId**: Required for region-specific charges
- **RegionName**: Display name when RegionId is present
- **AvailabilityZone**: Required for AZ-specific charges

#### SKU and Pricing Details
- **SkuId**: Required for SKU-based pricing
- **SkuPriceId**: Price identifier when SKU pricing exists
- **ListUnitPrice**: Unit price when available
- **ContractedUnitPrice**: Negotiated unit price when applicable

#### Commitment Discounts
- **CommitmentDiscountId**: Required when commitment discounts apply
- **CommitmentDiscountType**: Type of commitment (Reserved Instance, Savings Plan, etc.)
- **CommitmentDiscountStatus**: Usage status (Used, Unused)
- **CommitmentDiscountQuantity**: Quantity of commitment used

#### Usage Tracking
- **ConsumedQuantity**: Actual quantity consumed
- **ConsumedUnit**: Unit of consumption measurement

### Recommended Fields
These fields should be included when available:

- **ServiceSubcategory**: More specific service classification
- **ChargeFrequency**: How often the charge occurs (One-Time, Recurring, Usage-Based)
- **InvoiceId**: Direct link to provider invoice
- **InvoiceIssuer**: Entity that issued the invoice

### Optional Fields
- **Tags**: Key-value pairs for resource tagging
- **x_***: Provider-specific fields (must start with `x_` prefix)

## Service Categories

FOCUS 1.2 defines standardized service categories:

| Category | Description |
|----------|-------------|
| **AI and Machine Learning** | Artificial intelligence and ML services |
| **Analytics** | Data analytics and business intelligence |
| **Compute** | Virtual machines, containers, serverless compute |
| **Databases** | Managed database services |
| **Developer Tools** | Development and deployment tools |
| **Management and Governance** | Monitoring, logging, and governance |
| **Networking** | Load balancers, CDN, VPN, networking |
| **Security, Identity, and Compliance** | Security and identity services |
| **Storage** | Object, block, and file storage |
| **Other** | Services not fitting other categories |

## Charge Categories

FOCUS defines five types of charges:

| Category | Description |
|----------|-------------|
| **Usage** | Charges based on actual resource consumption |
| **Purchase** | Upfront payments for commitments or licenses |
| **Tax** | Taxes, VAT, and other government-imposed fees |
| **Credit** | Promotional credits, refunds, and adjustments |
| **Adjustment** | Billing corrections and manual adjustments |

## Data Types

FOCUS specifies data types for each field:

- **Decimal**: All cost and quantity fields for precise financial calculations
- **String**: Text fields like names, IDs, and descriptions
- **DateTime**: Time periods in ISO 8601 format
- **Dict/JSON**: Complex data like tags and provider-specific information

## Implementation in Narev AI

Narev AI Billing Analyzer implements FOCUS 1.2 through:

### Data Models
```python
# All billing data is stored in FOCUS-compliant format
class FocusRecord(BaseModel):
    # Mandatory cost fields
    billed_cost: Decimal
    effective_cost: Decimal
    list_cost: Decimal
    contracted_cost: Decimal
    
    # Account and service information
    billing_account_id: str
    service_name: str
    service_category: str
    # ... all other FOCUS fields
```

### Validation
- **Field validation**: Ensures all mandatory fields are present
- **Data type validation**: Enforces correct data types (Decimal for costs, DateTime for periods)
- **Enum validation**: Validates service categories and charge categories
- **Conditional validation**: Ensures conditional fields are only set when required

### Data Transformation
- **Provider mapping**: Transforms provider-specific data to FOCUS format
- **Currency handling**: Supports multiple currencies as per FOCUS requirements
- **PascalCase conversion**: Outputs data in FOCUS-compliant PascalCase format

### Export Capabilities
- **FOCUS-compliant exports**: All data exports follow FOCUS 1.2 specification
- **Provider reconciliation**: Links back to original provider data
- **Audit trails**: Maintains connection to raw billing data

## Provider Support

Major cloud providers supporting FOCUS 1.2:

- **Amazon Web Services (AWS)**
- **Microsoft Azure** 
- **Google Cloud Platform (GCP)**
- **Oracle Cloud Infrastructure (OCI)**
- **Alibaba Cloud**
- **Tencent Cloud**

SaaS providers:
- **Databricks**
- **Grafana**

## Compliance Benefits

Using FOCUS 1.2 compliance provides:

### For Organizations
- **Consistent reporting**: Same fields and definitions across all providers
- **Simplified analysis**: Single SQL query or dashboard covers all spending
- **Reduced errors**: Standardized format reduces interpretation mistakes
- **Faster insights**: Less time on data preparation, more on analysis

### For Tools and Vendors
- **Interoperability**: Tools can work with any FOCUS-compliant dataset
- **Reduced development**: Single implementation works with all providers
- **Customer adoption**: Organizations prefer FOCUS-compliant solutions

## Migration and Adoption

### From Legacy Formats
Narev AI automatically handles migration from provider-specific formats to FOCUS:

1. **Data ingestion**: Imports native provider formats
2. **Field mapping**: Maps provider fields to FOCUS equivalents
3. **Validation**: Ensures FOCUS compliance
4. **Storage**: Stores in FOCUS format for consistent analysis

### Best Practices
- **Use FOCUS exports**: Always export data in FOCUS format
- **Validate regularly**: Ensure data meets FOCUS requirements
- **Document customizations**: Any x_ fields should be well documented
- **Stay updated**: Monitor FOCUS specification updates

## Future Development

FOCUS specification continues to evolve:

- **Broader SaaS support**: More SaaS providers adopting FOCUS
- **Enhanced allocation**: Deeper cost allocation capabilities
- **New service categories**: As cloud services expand
- **Regional compliance**: Support for regional billing requirements

For the latest FOCUS specification details, visit [focus.finops.org](https://focus.finops.org/).