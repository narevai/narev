"""
FOCUS 1.2 Specification Constants and Enums
"""

from enum import Enum


class ServiceCategory(str, Enum):
    """FOCUS 1.2 Service Categories"""

    AI_AND_ML = "AI and Machine Learning"
    ANALYTICS = "Analytics"
    COMPUTE = "Compute"
    DATABASES = "Databases"
    DEVELOPER_TOOLS = "Developer Tools"
    MANAGEMENT_AND_GOVERNANCE = "Management and Governance"
    NETWORKING = "Networking"
    SECURITY = "Security, Identity, and Compliance"
    STORAGE = "Storage"
    OTHER = "Other"


class ChargeCategory(str, Enum):
    """FOCUS 1.2 Charge Categories"""

    USAGE = "Usage"
    PURCHASE = "Purchase"
    TAX = "Tax"
    CREDIT = "Credit"
    ADJUSTMENT = "Adjustment"


class ChargeClass(str, Enum):
    """FOCUS 1.2 Charge Classes"""

    CORRECTION = "Correction"


class CommitmentDiscountStatus(str, Enum):
    """FOCUS 1.2 Commitment Discount Status"""

    USED = "Used"
    UNUSED = "Unused"


class ChargeFrequency(str, Enum):
    """FOCUS 1.2 Charge Frequency"""

    ONE_TIME = "One-Time"
    RECURRING = "Recurring"
    USAGE_BASED = "Usage-Based"


class FocusSpec:
    """FOCUS 1.2 Specification Details"""

    VERSION = "1.2"

    # Mandatory fields
    MANDATORY_FIELDS = [
        # Costs
        "BilledCost",
        "EffectiveCost",
        "ListCost",
        "ContractedCost",
        # Account identification
        "BillingAccountId",
        "BillingAccountName",
        "BillingAccountType",
        # Time periods
        "BillingPeriodStart",
        "BillingPeriodEnd",
        "ChargePeriodStart",
        "ChargePeriodEnd",
        # Currency
        "BillingCurrency",
        # Services
        "ServiceName",
        "ServiceCategory",
        "ProviderName",
        "PublisherName",
        "InvoiceIssuerName",
        # Charges
        "ChargeCategory",
        "ChargeClass",
        "ChargeDescription",
        # Pricing
        "PricingQuantity",
        "PricingUnit",
    ]

    # Conditional fields (with their conditions)
    CONDITIONAL_FIELDS = {
        "SubAccountId": "When sub-accounts exist",
        "SubAccountName": "When SubAccountId is present",
        "SubAccountType": "When SubAccountId is present",
        "PricingCurrency": "When different from BillingCurrency",
        "ResourceId": "When resource-based billing",
        "ResourceName": "When ResourceId is present",
        "ResourceType": "When ResourceId is present",
        "RegionId": "When region-specific",
        "RegionName": "When RegionId is present",
        "AvailabilityZone": "When AZ-specific",
        "CapacityReservationId": "When capacity reservations apply",
        "CapacityReservationStatus": "When CapacityReservationId present",
        "SkuId": "When SKU-based pricing",
        "SkuPriceId": "When SKU pricing exists",
        "SkuMeter": "When SKU meter exists",
        "SkuPriceDetails": "When SKU price details available",
        "ListUnitPrice": "When unit pricing available",
        "ContractedUnitPrice": "When negotiated pricing",
        "CommitmentDiscountId": "When commitment discounts apply",
        "CommitmentDiscountType": "When CommitmentDiscountId present",
        "CommitmentDiscountCategory": "When CommitmentDiscountId present",
        "CommitmentDiscountName": "When CommitmentDiscountId present",
        "CommitmentDiscountStatus": "When commitment usage",
        "CommitmentDiscountQuantity": "When commitment quantity",
        "CommitmentDiscountUnit": "When CommitmentDiscountQuantity present",
        "ConsumedQuantity": "When usage measured",
        "ConsumedUnit": "When ConsumedQuantity present",
        "Tags": "When tags exist",
        "PricingCategory": "When pricing categorization available",
        "PricingCurrencyContractedUnitPrice": "When contracted pricing in different currency",
        "PricingCurrencyEffectiveCost": "When effective cost in different currency",
        "PricingCurrencyListUnitPrice": "When list pricing in different currency",
    }

    # Recommended fields
    RECOMMENDED_FIELDS = [
        "ServiceSubcategory",
        "ChargeFrequency",
        "InvoiceId",
        "InvoiceIssuer",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "x_*",  # Provider-specific fields must start with x_
    ]

    # Field data types
    FIELD_TYPES = {
        # Costs (Decimal)
        "BilledCost": "Decimal",
        "EffectiveCost": "Decimal",
        "ListCost": "Decimal",
        "ContractedCost": "Decimal",
        "ListUnitPrice": "Decimal",
        "ContractedUnitPrice": "Decimal",
        "PricingQuantity": "Decimal",
        "CommitmentDiscountQuantity": "Decimal",
        "ConsumedQuantity": "Decimal",
        "PricingCurrencyContractedUnitPrice": "Decimal",
        "PricingCurrencyEffectiveCost": "Decimal",
        "PricingCurrencyListUnitPrice": "Decimal",
        # Strings
        "BillingAccountId": "String",
        "BillingAccountName": "String",
        "BillingAccountType": "String",
        "SubAccountId": "String",
        "SubAccountName": "String",
        "SubAccountType": "String",
        "ServiceName": "String",
        "ServiceCategory": "String",
        "ServiceSubcategory": "String",
        "ProviderName": "String",
        "PublisherName": "String",
        "InvoiceIssuerName": "String",
        "ChargeCategory": "String",
        "ChargeClass": "String",
        "ChargeDescription": "String",
        "ChargeFrequency": "String",
        "BillingCurrency": "String",
        "PricingCurrency": "String",
        "PricingUnit": "String",
        "PricingCategory": "String",
        "ResourceId": "String",
        "ResourceName": "String",
        "ResourceType": "String",
        "RegionId": "String",
        "RegionName": "String",
        "AvailabilityZone": "String",
        "CapacityReservationId": "String",
        "CapacityReservationStatus": "String",
        "SkuId": "String",
        "SkuPriceId": "String",
        "SkuMeter": "String",
        "SkuPriceDetails": "String",
        "CommitmentDiscountId": "String",
        "CommitmentDiscountType": "String",
        "CommitmentDiscountCategory": "String",
        "CommitmentDiscountName": "String",
        "CommitmentDiscountStatus": "String",
        "CommitmentDiscountUnit": "String",
        "ConsumedUnit": "String",
        "InvoiceId": "String",
        "InvoiceIssuer": "String",
        # DateTimes
        "BillingPeriodStart": "DateTime",
        "BillingPeriodEnd": "DateTime",
        "ChargePeriodStart": "DateTime",
        "ChargePeriodEnd": "DateTime",
        # JSON/Dict
        "Tags": "Dict",
    }

    @classmethod
    def get_all_fields(cls) -> list[str]:
        """Get all FOCUS fields."""
        fields = cls.MANDATORY_FIELDS.copy()
        fields.extend(cls.CONDITIONAL_FIELDS.keys())
        fields.extend(cls.RECOMMENDED_FIELDS)
        return fields

    @classmethod
    def is_valid_service_category(cls, category: str) -> bool:
        """Check if service category is valid."""
        return category in [e.value for e in ServiceCategory]

    @classmethod
    def is_valid_charge_category(cls, category: str) -> bool:
        """Check if charge category is valid."""
        return category in [e.value for e in ChargeCategory]

    @classmethod
    def is_valid_charge_class(cls, charge_class: str) -> bool:
        """Check if charge class is valid."""
        return charge_class is None or charge_class == ChargeClass.CORRECTION.value

    @classmethod
    def is_valid_commitment_discount_status(cls, status: str) -> bool:
        """Check if commitment discount status is valid."""
        return status is None or status in [e.value for e in CommitmentDiscountStatus]

    @classmethod
    def is_valid_charge_frequency(cls, frequency: str) -> bool:
        """Check if charge frequency is valid."""
        return frequency is None or frequency in [e.value for e in ChargeFrequency]

    @classmethod
    def get_field_type(cls, field_name: str) -> str:
        """Get the data type for a field."""
        return cls.FIELD_TYPES.get(field_name, "String")

    @classmethod
    def is_mandatory_field(cls, field_name: str) -> bool:
        """Check if field is mandatory."""
        return field_name in cls.MANDATORY_FIELDS

    @classmethod
    def is_conditional_field(cls, field_name: str) -> bool:
        """Check if field is conditional."""
        return field_name in cls.CONDITIONAL_FIELDS

    @classmethod
    def is_recommended_field(cls, field_name: str) -> bool:
        """Check if field is recommended."""
        return field_name in cls.RECOMMENDED_FIELDS

    @classmethod
    def is_provider_specific_field(cls, field_name: str) -> bool:
        """Check if field is provider-specific (starts with x_)."""
        return field_name.startswith("x_")
