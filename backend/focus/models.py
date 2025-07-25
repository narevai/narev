"""
FOCUS 1.2 Data Models
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator
from pydantic.alias_generators import to_pascal


class FocusRecord(BaseModel):
    """FOCUS 1.2 compliant billing record model."""

    # Internal ID (not part of FOCUS spec)
    id: str = Field(default_factory=lambda: str(uuid4()))

    # MANDATORY: Costs
    billed_cost: Decimal = Field(..., description="Cost as shown on invoice")
    effective_cost: Decimal = Field(..., description="Amortized cost after discounts")
    list_cost: Decimal = Field(..., description="Cost at list prices")
    contracted_cost: Decimal = Field(..., description="Cost at negotiated prices")

    # MANDATORY: Account identification
    billing_account_id: str = Field(
        ..., description="Account that receives the invoice"
    )
    billing_account_name: str | None = Field(
        None, description="Display name of billing account"
    )
    billing_account_type: str = Field(
        ..., description="Type of billing account"
    )  # ADDED

    # MANDATORY: Time periods
    billing_period_start: datetime = Field(
        ..., description="Start of billing period (inclusive)"
    )
    billing_period_end: datetime = Field(
        ..., description="End of billing period (exclusive)"
    )
    charge_period_start: datetime = Field(
        ..., description="Start of charge period (inclusive)"
    )
    charge_period_end: datetime = Field(
        ..., description="End of charge period (exclusive)"
    )

    # MANDATORY: Currency
    billing_currency: str = Field(..., description="Currency of the bill")

    # MANDATORY: Services
    service_name: str = Field(..., description="Name of the service")
    service_category: str = Field(..., description="FOCUS service category")
    provider_name: str = Field(..., description="Entity that provided the resources")
    publisher_name: str = Field(..., description="Entity that produced the resources")
    invoice_issuer_name: str = Field(
        ..., description="Entity responsible for invoicing"
    )

    # MANDATORY: Charges
    charge_category: str = Field(..., description="Type of charge")
    charge_description: str = Field(..., description="Description of the charge")

    # CONDITIONAL: Sub-accounts
    sub_account_id: str | None = Field(None, description="Sub-account identifier")
    sub_account_name: str | None = Field(None, description="Sub-account name")
    sub_account_type: str | None = Field(None, description="Sub-account type")

    # CONDITIONAL: Pricing
    pricing_currency: str | None = Field(None, description="Currency for pricing")
    charge_class: str | None = Field(None, description="Class of charge")
    pricing_quantity: Decimal | None = Field(None, description="Quantity priced")
    pricing_unit: str | None = Field(None, description="Unit of pricing")

    # CONDITIONAL: Resources
    resource_id: str | None = Field(None, description="Resource identifier")
    resource_name: str | None = Field(None, description="Resource name")
    resource_type: str | None = Field(None, description="Type of resource")

    # CONDITIONAL: Location
    region_id: str | None = Field(None, description="Region identifier")
    region_name: str | None = Field(None, description="Region name")
    availability_zone: str | None = Field(None, description="Availability zone")

    # CONDITIONAL: Capacity Reservation
    capacity_reservation_id: str | None = Field(
        None, description="Capacity reservation identifier"
    )
    capacity_reservation_status: str | None = Field(
        None, description="Capacity reservation status"
    )

    # CONDITIONAL: SKU and pricing
    sku_id: str | None = Field(None, description="SKU identifier")
    sku_price_id: str | None = Field(None, description="SKU price identifier")
    sku_meter: str | None = Field(None, description="SKU meter")
    sku_price_details: str | None = Field(None, description="SKU price details")
    list_unit_price: Decimal | None = Field(None, description="List price per unit")
    contracted_unit_price: Decimal | None = Field(
        None, description="Contracted price per unit"
    )

    # CONDITIONAL: Commitment Discounts
    commitment_discount_id: str | None = Field(
        None, description="Commitment discount identifier"
    )
    commitment_discount_type: str | None = Field(
        None, description="Type of commitment discount"
    )
    commitment_discount_category: str | None = Field(
        None, description="Commitment discount category"
    )
    commitment_discount_name: str | None = Field(
        None, description="Commitment discount name"
    )
    commitment_discount_status: str | None = Field(None, description="Usage status")
    commitment_discount_quantity: Decimal | None = Field(
        None, description="Commitment quantity"
    )
    commitment_discount_unit: str | None = Field(None, description="Commitment unit")

    # CONDITIONAL: Usage
    consumed_quantity: Decimal | None = Field(None, description="Quantity consumed")
    consumed_unit: str | None = Field(None, description="Unit of consumption")

    # CONDITIONAL: Tags
    tags: dict[str, Any] | None = Field(None, description="Key-value tags")

    # CONDITIONAL: Pricing details
    pricing_category: str | None = Field(None, description="Pricing category")
    pricing_currency_contracted_unit_price: Decimal | None = Field(
        None, description="Contracted unit price in pricing currency"
    )
    pricing_currency_effective_cost: Decimal | None = Field(
        None, description="Effective cost in pricing currency"
    )
    pricing_currency_list_unit_price: Decimal | None = Field(
        None, description="List unit price in pricing currency"
    )

    # RECOMMENDED: Additional fields
    service_subcategory: str | None = Field(None, description="Service subcategory")
    charge_frequency: str | None = Field(None, description="Frequency of charge")
    invoice_id: str | None = Field(None, description="Invoice identifier")
    invoice_issuer: str | None = Field(None, description="Invoice issuer")
    sku_description: str | None = Field(None, description="SKU description")

    # Provider-specific fields (x_ prefix for custom fields)
    x_provider_id: str | None = Field(None, description="Provider ID in system")
    x_provider_data: dict[str, Any] | None = Field(
        None, description="Provider-specific data"
    )
    x_raw_billing_data_id: str | None = Field(None, description="Raw billing data ID")
    x_created_at: datetime | None = Field(None, description="Record creation time")
    x_updated_at: datetime | None = Field(None, description="Record update time")

    # Serializers for Decimal and datetime types
    @field_serializer(
        "billed_cost",
        "effective_cost",
        "list_cost",
        "contracted_cost",
        "pricing_quantity",
        "list_unit_price",
        "contracted_unit_price",
        "commitment_discount_quantity",
        "consumed_quantity",
        "pricing_currency_contracted_unit_price",
        "pricing_currency_effective_cost",
        "pricing_currency_list_unit_price",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        """Convert Decimal to float for JSON serialization."""
        return float(value) if value is not None else None

    @field_serializer(
        "billing_period_start",
        "billing_period_end",
        "charge_period_start",
        "charge_period_end",
        "x_created_at",
        "x_updated_at",
    )
    def serialize_datetime(self, value: datetime | None) -> str | None:
        """Convert datetime to ISO format string."""
        return value.isoformat() if value is not None else None

    @field_validator("billing_period_end")
    @classmethod
    def validate_billing_period(cls, v, info):
        """Ensure billing period end is after start."""
        if (
            "billing_period_start" in info.data
            and v <= info.data["billing_period_start"]
        ):
            raise ValueError("billing_period_end must be after billing_period_start")
        return v

    @field_validator("charge_period_end")
    @classmethod
    def validate_charge_period(cls, v, info):
        """Ensure charge period end is after start."""
        if "charge_period_start" in info.data and v <= info.data["charge_period_start"]:
            raise ValueError("charge_period_end must be after charge_period_start")
        return v

    @field_validator("sub_account_name")
    @classmethod
    def validate_sub_account_name(cls, v, info):
        """Ensure sub_account_name is only set when sub_account_id exists."""
        if v and not info.data.get("sub_account_id"):
            raise ValueError("sub_account_name requires sub_account_id")
        return v

    @field_validator("sub_account_type")
    @classmethod
    def validate_sub_account_type(cls, v, info):
        """Ensure sub_account_type is only set when sub_account_id exists."""
        if v and not info.data.get("sub_account_id"):
            raise ValueError("sub_account_type requires sub_account_id")
        return v

    @field_validator("pricing_unit")
    @classmethod
    def validate_pricing_unit(cls, v, info):
        """Ensure pricing_unit is only set when pricing_quantity exists."""
        if v and info.data.get("pricing_quantity") is None:
            raise ValueError("pricing_unit requires pricing_quantity")
        return v

    @field_validator("capacity_reservation_status")
    @classmethod
    def validate_capacity_reservation_status(cls, v, info):
        """Ensure capacity_reservation_status is only set when capacity_reservation_id exists."""
        if v and not info.data.get("capacity_reservation_id"):
            raise ValueError(
                "capacity_reservation_status requires capacity_reservation_id"
            )
        return v

    @field_validator("commitment_discount_name")
    @classmethod
    def validate_commitment_discount_name(cls, v, info):
        """Ensure commitment_discount_name is only set when commitment_discount_id exists."""
        if v and not info.data.get("commitment_discount_id"):
            raise ValueError("commitment_discount_name requires commitment_discount_id")
        return v

    def to_focus_dict(self) -> dict[str, Any]:
        """
        Convert to FOCUS 1.2 compliant dictionary with PascalCase field names.
        Returns ALL fields including None values.
        """
        # Use model_dump to get all fields with serializers applied
        data = self.model_dump(exclude={"id"})  # Exclude internal ID

        # Transform to FOCUS format with PascalCase
        focus_dict = {}
        for snake_key, value in data.items():
            if snake_key.startswith("x_"):
                # Keep x_ prefix and convert the rest to PascalCase
                pascal_key = "x_" + to_pascal(snake_key[2:])
            else:
                pascal_key = to_pascal(snake_key)

            focus_dict[pascal_key] = value

        return focus_dict

    def to_dlt_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for DLT loading (keeps snake_case).
        Excludes internal ID field.
        """
        return self.model_dump(exclude={"id"})
