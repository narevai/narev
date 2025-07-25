"""
NarevAI Billing Analyzer - FOCUS 1.2 compliant Billing Data Model
"""

from uuid import uuid4

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.config import get_settings
from app.database import Base

settings = get_settings()


def get_json_field():
    """Get appropriate JSON field type based on database."""
    return JSONB if settings.is_postgres else JSON


class BillingData(Base):
    """FOCUS 1.2 compliant billing data table."""

    __tablename__ = "billing_data"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # MANDATORY: Costs (Metric columns) - using Numeric for precision
    billed_cost = Column(Numeric(20, 10), nullable=False)
    effective_cost = Column(Numeric(20, 10), nullable=False)
    list_cost = Column(Numeric(20, 10), nullable=False)
    contracted_cost = Column(Numeric(20, 10), nullable=False)

    # MANDATORY: Account identification
    billing_account_id = Column(String(255), nullable=False)
    billing_account_name = Column(String(500), nullable=False)
    billing_account_type = Column(String(100), nullable=False)
    sub_account_id = Column(String(255))
    sub_account_name = Column(String(500))
    sub_account_type = Column(String(100))

    # MANDATORY: Time periods (with timezone)
    billing_period_start = Column(DateTime(timezone=True), nullable=False)
    billing_period_end = Column(DateTime(timezone=True), nullable=False)
    charge_period_start = Column(DateTime(timezone=True), nullable=False)
    charge_period_end = Column(DateTime(timezone=True), nullable=False)

    # MANDATORY: Currency
    billing_currency = Column(String(10), nullable=False)
    pricing_currency = Column(String(10))

    # MANDATORY: Services and categorization
    service_name = Column(String(255), nullable=False)
    service_category = Column(String(50), nullable=False)
    provider_name = Column(String(100), nullable=False)
    publisher_name = Column(String(100), nullable=False)
    invoice_issuer_name = Column(String(100), nullable=False)

    # MANDATORY: Charge categorization
    charge_category = Column(String(20), nullable=False)
    charge_class = Column(String(20))
    charge_description = Column(Text, nullable=False)

    # MANDATORY: Pricing and quantities
    pricing_quantity = Column(Numeric(20, 10))
    pricing_unit = Column(String(100))

    # CONDITIONAL: Resources
    resource_id = Column(String(255))
    resource_name = Column(String(500))
    resource_type = Column(String(100))

    # CONDITIONAL: Location
    region_id = Column(String(50))
    region_name = Column(String(100))
    availability_zone = Column(String(50))

    # CONDITIONAL: Capacity Reservation
    capacity_reservation_id = Column(String(255))
    capacity_reservation_status = Column(String(50))

    # CONDITIONAL: SKU and pricing
    sku_id = Column(String(255))
    sku_price_id = Column(String(255))
    sku_meter = Column(String(255))
    sku_price_details = Column(Text)
    list_unit_price = Column(Numeric(20, 10))
    contracted_unit_price = Column(Numeric(20, 10))

    # CONDITIONAL: Commitment Discounts
    commitment_discount_id = Column(String(255))
    commitment_discount_type = Column(String(100))
    commitment_discount_category = Column(String(50))
    commitment_discount_name = Column(String(255))
    commitment_discount_status = Column(String(20))
    commitment_discount_quantity = Column(Numeric(20, 10))
    commitment_discount_unit = Column(String(100))

    # CONDITIONAL: Usage
    consumed_quantity = Column(Numeric(20, 10))
    consumed_unit = Column(String(100))

    # CONDITIONAL: Tags - business logic tags
    tags = Column(get_json_field())

    # CONDITIONAL: Pricing details
    pricing_category = Column(String(100))
    pricing_currency_contracted_unit_price = Column(Numeric(20, 10))
    pricing_currency_effective_cost = Column(Numeric(20, 10))
    pricing_currency_list_unit_price = Column(Numeric(20, 10))

    # RECOMMENDED: Additional fields
    service_subcategory = Column(String(100))
    charge_frequency = Column(String(20))
    invoice_id = Column(String(255))
    invoice_issuer = Column(String(100))

    # Provider-specific fields (x_ prefix)
    x_provider_data = Column(get_json_field())

    # Internal tracking
    x_raw_billing_data_id = Column(String(36), ForeignKey("raw_billing_data.id"))
    x_provider_id = Column(String(36), ForeignKey("providers.id"), nullable=False)
    x_created_at = Column(DateTime(timezone=True), server_default=func.now())
    x_updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # DLT internal columns
    _dlt_load_id = Column(String(255))
    _dlt_id = Column(String(255))

    # Relationships
    provider = relationship("Provider", back_populates="billing_records")
    raw_billing_data = relationship("RawBillingData")

    __table_args__ = (
        CheckConstraint(
            "billing_period_end > billing_period_start", name="ck_billing_period_valid"
        ),
        CheckConstraint(
            "charge_period_end > charge_period_start", name="ck_charge_period_valid"
        ),
        CheckConstraint(
            "effective_cost >= 0 AND billed_cost >= 0 AND list_cost >= 0 AND contracted_cost >= 0",
            name="ck_costs_non_negative",
        ),
        CheckConstraint(
            "pricing_quantity IS NULL OR pricing_quantity >= 0",
            name="ck_pricing_quantity_non_negative",
        ),
        CheckConstraint(
            "consumed_quantity IS NULL OR consumed_quantity >= 0",
            name="ck_consumed_quantity_non_negative",
        ),
        CheckConstraint(
            "service_category IN ('AI and Machine Learning', 'Analytics', 'Compute', 'Databases', 'Developer Tools', 'Management and Governance', 'Networking', 'Security, Identity, and Compliance', 'Storage', 'Other')",
            name="ck_service_category_valid",
        ),
        CheckConstraint(
            "charge_category IN ('Usage', 'Purchase', 'Tax', 'Credit', 'Adjustment')",
            name="ck_charge_category_valid",
        ),
        CheckConstraint(
            "charge_class IS NULL OR charge_class = 'Correction'",
            name="ck_charge_class_valid",
        ),
        CheckConstraint(
            "commitment_discount_status IS NULL OR commitment_discount_status IN ('Used', 'Unused')",
            name="ck_commitment_discount_status_valid",
        ),
        CheckConstraint(
            "charge_frequency IS NULL OR charge_frequency IN ('One-Time', 'Recurring', 'Usage-Based')",
            name="ck_charge_frequency_valid",
        ),
        Index(
            "idx_billing_provider_period",
            "x_provider_id",
            "charge_period_start",
            "charge_period_end",
        ),
        Index("idx_billing_service_category", "service_category"),
        Index("idx_billing_costs", "effective_cost"),
        Index("idx_billing_sku", "sku_id"),
        Index("idx_billing_created", "x_created_at"),
        Index("idx_billing_account", "billing_account_id"),
        Index("idx_billing_charge_period", "charge_period_start", "charge_period_end"),
        Index("idx_billing_service_name", "service_name"),
        Index("idx_billing_resource", "resource_id"),
        Index("idx_billing_region", "region_id"),
    )

    def __repr__(self):
        return f"<BillingData(id={self.id}, service={self.service_name}, cost={self.effective_cost})>"

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "billed_cost": float(self.billed_cost),
            "effective_cost": float(self.effective_cost),
            "list_cost": float(self.list_cost),
            "contracted_cost": float(self.contracted_cost),
            "billing_account_id": self.billing_account_id,
            "billing_account_name": self.billing_account_name,
            "billing_account_type": self.billing_account_type,
            "sub_account_id": self.sub_account_id,
            "sub_account_name": self.sub_account_name,
            "sub_account_type": self.sub_account_type,
            "billing_period_start": self.billing_period_start.isoformat()
            if self.billing_period_start
            else None,
            "billing_period_end": self.billing_period_end.isoformat()
            if self.billing_period_end
            else None,
            "charge_period_start": self.charge_period_start.isoformat()
            if self.charge_period_start
            else None,
            "charge_period_end": self.charge_period_end.isoformat()
            if self.charge_period_end
            else None,
            "billing_currency": self.billing_currency,
            "pricing_currency": self.pricing_currency,
            "service_name": self.service_name,
            "service_category": self.service_category,
            "provider_name": self.provider_name,
            "publisher_name": self.publisher_name,
            "invoice_issuer_name": self.invoice_issuer_name,
            "charge_category": self.charge_category,
            "charge_class": self.charge_class,
            "charge_description": self.charge_description,
            "pricing_quantity": float(self.pricing_quantity)
            if self.pricing_quantity
            else None,
            "pricing_unit": self.pricing_unit,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "resource_type": self.resource_type,
            "region_id": self.region_id,
            "region_name": self.region_name,
            "availability_zone": self.availability_zone,
            "capacity_reservation_id": self.capacity_reservation_id,
            "capacity_reservation_status": self.capacity_reservation_status,
            "sku_id": self.sku_id,
            "sku_price_id": self.sku_price_id,
            "sku_meter": self.sku_meter,
            "sku_price_details": self.sku_price_details,
            "list_unit_price": float(self.list_unit_price)
            if self.list_unit_price
            else None,
            "contracted_unit_price": float(self.contracted_unit_price)
            if self.contracted_unit_price
            else None,
            "commitment_discount_id": self.commitment_discount_id,
            "commitment_discount_type": self.commitment_discount_type,
            "commitment_discount_category": self.commitment_discount_category,
            "commitment_discount_name": self.commitment_discount_name,
            "commitment_discount_status": self.commitment_discount_status,
            "commitment_discount_quantity": float(self.commitment_discount_quantity)
            if self.commitment_discount_quantity
            else None,
            "commitment_discount_unit": self.commitment_discount_unit,
            "consumed_quantity": float(self.consumed_quantity)
            if self.consumed_quantity
            else None,
            "consumed_unit": self.consumed_unit,
            "tags": self.tags,
            "pricing_category": self.pricing_category,
            "pricing_currency_contracted_unit_price": float(
                self.pricing_currency_contracted_unit_price
            )
            if self.pricing_currency_contracted_unit_price
            else None,
            "pricing_currency_effective_cost": float(
                self.pricing_currency_effective_cost
            )
            if self.pricing_currency_effective_cost
            else None,
            "pricing_currency_list_unit_price": float(
                self.pricing_currency_list_unit_price
            )
            if self.pricing_currency_list_unit_price
            else None,
            "service_subcategory": self.service_subcategory,
            "charge_frequency": self.charge_frequency,
            "invoice_id": self.invoice_id,
            "invoice_issuer": self.invoice_issuer,
            # Provider-specific fields
            "x_provider_data": self.x_provider_data,
            # Internal fields (system specific)
            "x_provider_id": self.x_provider_id,
            "x_raw_billing_data_id": self.x_raw_billing_data_id,
            "x_created_at": self.x_created_at.isoformat()
            if self.x_created_at
            else None,
            "x_updated_at": self.x_updated_at.isoformat()
            if self.x_updated_at
            else None,
        }

    def to_focus_record(self):
        """Convert BillingData to FocusRecord."""
        from focus.models import FocusRecord

        return FocusRecord(
            billed_cost=self.billed_cost,
            effective_cost=self.effective_cost,
            list_cost=self.list_cost,
            contracted_cost=self.contracted_cost,
            billing_account_id=self.billing_account_id,
            billing_account_name=self.billing_account_name,
            billing_account_type=self.billing_account_type,
            billing_period_start=self.billing_period_start,
            billing_period_end=self.billing_period_end,
            charge_period_start=self.charge_period_start,
            charge_period_end=self.charge_period_end,
            billing_currency=self.billing_currency,
            service_name=self.service_name,
            service_category=self.service_category,
            provider_name=self.provider_name,
            publisher_name=self.publisher_name,
            invoice_issuer_name=self.invoice_issuer_name,
            charge_category=self.charge_category,
            charge_description=self.charge_description,
            sub_account_id=self.sub_account_id,
            sub_account_name=self.sub_account_name,
            sub_account_type=self.sub_account_type,
            pricing_currency=self.pricing_currency,
            charge_class=self.charge_class,
            pricing_quantity=self.pricing_quantity,
            pricing_unit=self.pricing_unit,
            resource_id=self.resource_id,
            resource_name=self.resource_name,
            resource_type=self.resource_type,
            region_id=self.region_id,
            region_name=self.region_name,
            availability_zone=self.availability_zone,
            capacity_reservation_id=self.capacity_reservation_id,
            capacity_reservation_status=self.capacity_reservation_status,
            sku_id=self.sku_id,
            sku_price_id=self.sku_price_id,
            sku_meter=self.sku_meter,
            sku_price_details=self.sku_price_details,
            list_unit_price=self.list_unit_price,
            contracted_unit_price=self.contracted_unit_price,
            commitment_discount_id=self.commitment_discount_id,
            commitment_discount_type=self.commitment_discount_type,
            commitment_discount_category=self.commitment_discount_category,
            commitment_discount_name=self.commitment_discount_name,
            commitment_discount_status=self.commitment_discount_status,
            commitment_discount_quantity=self.commitment_discount_quantity,
            commitment_discount_unit=self.commitment_discount_unit,
            consumed_quantity=self.consumed_quantity,
            consumed_unit=self.consumed_unit,
            tags=self.tags,
            pricing_category=self.pricing_category,
            pricing_currency_contracted_unit_price=self.pricing_currency_contracted_unit_price,
            pricing_currency_effective_cost=self.pricing_currency_effective_cost,
            pricing_currency_list_unit_price=self.pricing_currency_list_unit_price,
            service_subcategory=self.service_subcategory,
            charge_frequency=self.charge_frequency,
            invoice_id=self.invoice_id,
            invoice_issuer=self.invoice_issuer,
            x_provider_data=self.x_provider_data,
            x_provider_id=self.x_provider_id,
            x_raw_billing_data_id=self.x_raw_billing_data_id,
            x_created_at=self.x_created_at.isoformat() if self.x_created_at else None,
            x_updated_at=self.x_updated_at.isoformat() if self.x_updated_at else None,
        )
