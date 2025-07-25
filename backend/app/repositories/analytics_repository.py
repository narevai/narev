"""
Analytics Repository - FOCUS Use Cases Data Access Layer
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AnalyticsRepository:
    """Repository for analytics operations."""

    def __init__(self, db: Session):
        """Initialize repository."""
        self.db = db

    def get_resource_rate_data(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_name: str | None = None,
        region_name: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get data for resource rate calculation."""
        from sqlalchemy import text

        # Detect database type
        dialect_name = self.db.bind.dialect.name.lower()

        if dialect_name == "sqlite":
            # SQLite JSON functions
            json_extract_instance = (
                "JSON_EXTRACT(sku_price_details, '$.InstanceSeries')"
            )
            cast_to_int = (
                "CAST(JSON_EXTRACT(sku_price_details, '$.CoreCount') AS INTEGER)"
            )
            json_path_check = """JSON_EXTRACT(sku_price_details, '$.CoreCount') IS NOT NULL
                AND JSON_EXTRACT(sku_price_details, '$.InstanceSeries') IS NOT NULL"""
        else:
            # MySQL/PostgreSQL JSON functions
            json_extract_instance = (
                "JSON_UNQUOTE(JSON_EXTRACT(sku_price_details, '$.InstanceSeries'))"
            )
            if dialect_name == "mysql":
                cast_to_int = "CAST(JSON_UNQUOTE(JSON_EXTRACT(sku_price_details, '$.CoreCount')) AS UNSIGNED)"
            else:  # PostgreSQL
                cast_to_int = "CAST(JSON_UNQUOTE(JSON_EXTRACT(sku_price_details, '$.CoreCount')) AS INTEGER)"
            json_path_check = "JSON_CONTAINS_PATH(sku_price_details, 'all', '$.CoreCount', '$.InstanceSeries')"

        # Base SQL query with dynamic JSON functions
        sql = f"""
        SELECT
            provider_name,
            service_name,
            pricing_unit,
            region_name,
            {json_extract_instance} AS instance_series,
            SUM({cast_to_int}) AS total_core_count,
            CASE
                WHEN SUM({cast_to_int}) > 0
                THEN SUM(effective_cost) / SUM({cast_to_int})
                ELSE NULL
            END AS average_effective_core_cost
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND {json_path_check}
        """

        # Add optional filters
        params = {"start_date": start_date, "end_date": end_date}

        conditions = []
        if provider_name:
            conditions.append("AND provider_name = :provider_name")
            params["provider_name"] = provider_name

        if service_name:
            conditions.append("AND service_name LIKE :service_name")
            params["service_name"] = f"%{service_name}%"

        if region_name:
            conditions.append("AND region_name = :region_name")
            params["region_name"] = region_name

        if conditions:
            sql += " " + " ".join(conditions)

        sql += """
        GROUP BY
            provider_name,
            service_name,
            pricing_unit,
            region_name,
            instance_series
        ORDER BY average_effective_core_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "service_name": row.service_name,
                    "pricing_unit": row.pricing_unit,
                    "region_name": row.region_name,
                    "instance_series": row.instance_series,
                    "total_core_count": int(row.total_core_count or 0),
                    "average_effective_core_cost": float(
                        row.average_effective_core_cost or 0
                    ),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error calculating resource rate: {e}")
            return []

    def get_resource_usage_data(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_name: str | None = None,
        region_name: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get resource usage data."""
        from sqlalchemy import text

        # Check database type and use appropriate JSON functions
        db_dialect = self.db.bind.dialect.name

        if db_dialect == "postgresql":
            # PostgreSQL uses -> and ->> operators for JSON
            instance_series_expr = "sku_price_details->>'InstanceSeries'"
            core_count_expr = "CAST(sku_price_details->>'CoreCount' AS INTEGER)"
            json_path_check = "sku_price_details ? 'CoreCount' AND sku_price_details ? 'InstanceSeries'"
        else:
            # SQLite uses JSON_EXTRACT
            instance_series_expr = "JSON_EXTRACT(sku_price_details, '$.InstanceSeries')"
            core_count_expr = (
                "CAST(JSON_EXTRACT(sku_price_details, '$.CoreCount') AS INTEGER)"
            )
            json_path_check = "JSON_EXTRACT(sku_price_details, '$.CoreCount') IS NOT NULL AND JSON_EXTRACT(sku_price_details, '$.InstanceSeries') IS NOT NULL"

        sql = f"""
        SELECT
            provider_name,
            service_name,
            pricing_unit,
            region_name,
            {instance_series_expr} AS instance_series,
            SUM({core_count_expr}) AS total_core_count,
            COUNT(*) AS resource_count,
            AVG({core_count_expr}) AS avg_core_count,
            MIN({core_count_expr}) AS min_core_count,
            MAX({core_count_expr}) AS max_core_count
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND {json_path_check}
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if service_name:
            sql += " AND service_name LIKE :service_name"
            params["service_name"] = f"%{service_name}%"

        if region_name:
            sql += " AND region_name = :region_name"
            params["region_name"] = region_name

        sql += """
        GROUP BY
            provider_name,
            service_name,
            pricing_unit,
            region_name,
            instance_series
        ORDER BY total_core_count DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "service_name": row.service_name,
                    "pricing_unit": row.pricing_unit or "Unknown",
                    "region_name": row.region_name or "Unknown",
                    "instance_series": row.instance_series or "Unknown",
                    "total_core_count": int(row.total_core_count or 0),
                    "resource_count": int(row.resource_count or 0),
                    "avg_core_count": float(row.avg_core_count or 0),
                    "min_core_count": int(row.min_core_count or 0),
                    "max_core_count": int(row.max_core_count or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting resource usage data: {e}")
            return []

    def get_unit_economics_data(
        self,
        start_date: datetime,
        end_date: datetime,
        unit_type: str = "GB",
        charge_description_filter: str = "transfer",
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get data for unit economics calculation."""
        from sqlalchemy import text

        # Convert to snake_case and adapt for our data structure
        sql = """
        SELECT
            CAST(charge_period_start AS DATE) AS charge_period_date,
            SUM(billed_cost) / NULLIF(SUM(CAST(consumed_quantity AS DECIMAL(10, 2))), 0) AS cost_per_unit,
            SUM(billed_cost) AS total_cost,
            SUM(consumed_quantity) AS total_quantity,
            consumed_unit,
            COUNT(*) AS record_count
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND charge_description LIKE :charge_description_filter
            AND consumed_unit = :unit_type
            AND consumed_quantity > 0
        GROUP BY
            CAST(charge_period_start AS DATE),
            consumed_unit
        ORDER BY
            charge_period_date ASC
        """

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "charge_description_filter": f"%{charge_description_filter}%",
            "unit_type": unit_type,
        }

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "charge_period_date": str(row.charge_period_date),
                    "cost_per_unit": float(row.cost_per_unit or 0),
                    "total_cost": float(row.total_cost or 0),
                    "total_quantity": float(row.total_quantity or 0),
                    "consumed_unit": row.consumed_unit,
                    "record_count": int(row.record_count or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error calculating unit economics: {e}")
            return []

    def get_virtual_currency_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        pricing_currency: str | None = None,
        limit: int = 10,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get virtual currency usage data."""
        from sqlalchemy import text

        # Identify charges using non-standard currencies (virtual currencies)
        sql = """
        SELECT
            provider_name,
            publisher_name,
            service_name,
            charge_description,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            pricing_currency
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND pricing_currency IS NOT NULL
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional pricing currency filter
        if pricing_currency:
            sql += " AND pricing_currency = :pricing_currency"
            params["pricing_currency"] = pricing_currency

        sql += """
        GROUP BY
            provider_name,
            publisher_name,
            service_name,
            charge_description,
            pricing_currency
        ORDER BY total_effective_cost DESC
        LIMIT :limit
        """

        params["limit"] = limit

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "publisher_name": row.publisher_name,
                    "service_name": row.service_name,
                    "charge_description": row.charge_description,
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "pricing_currency": row.pricing_currency,
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error analyzing virtual currency usage: {e}")
            return []

    def get_costs_by_currency(
        self,
        start_date: datetime,
        end_date: datetime,
        include_exchange_rates: bool = False,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get costs grouped by currency."""
        from sqlalchemy import text

        # Break down effective cost by pricing currency
        sql = """
        SELECT
            provider_name,
            publisher_name,
            service_name,
            pricing_currency,
            SUM(effective_cost) AS total_effective_cost,
            AVG(effective_cost) AS avg_effective_cost,
            COUNT(*) AS charge_count,
            MIN(charge_period_start) AS earliest_charge,
            MAX(charge_period_end) AS latest_charge
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND pricing_currency IS NOT NULL
            AND effective_cost > 0
        GROUP BY
            provider_name,
            publisher_name,
            service_name,
            pricing_currency
        ORDER BY total_effective_cost DESC
        """

        params = {"start_date": start_date, "end_date": end_date}

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "publisher_name": row.publisher_name,
                    "service_name": row.service_name,
                    "pricing_currency": row.pricing_currency,
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "avg_effective_cost": float(row.avg_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "earliest_charge": str(row.earliest_charge)
                    if row.earliest_charge
                    else None,
                    "latest_charge": str(row.latest_charge)
                    if row.latest_charge
                    else None,
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error analyzing costs by currency: {e}")
            return []

    def get_virtual_currency_purchases(
        self,
        start_date: datetime,
        end_date: datetime,
        pricing_unit: str | None = None,
        group_by: str = "service",
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get virtual currency purchase data."""
        from sqlalchemy import text

        # Analyze virtual currency purchase patterns
        sql = """
        SELECT
            provider_name,
            publisher_name,
            charge_description,
            pricing_unit,
            billing_currency,
            SUM(pricing_quantity) AS total_pricing_quantity,
            SUM(billed_cost) AS total_billed_cost,
            COUNT(*) AS purchase_count,
            AVG(billed_cost) AS avg_purchase_cost,
            MIN(charge_period_start) AS first_purchase,
            MAX(charge_period_start) AS last_purchase
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND charge_category = 'Purchase'
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional pricing unit filter
        if pricing_unit:
            sql += " AND pricing_unit = :pricing_unit"
            params["pricing_unit"] = pricing_unit

        sql += """
        GROUP BY
            provider_name,
            publisher_name,
            charge_description,
            pricing_unit,
            billing_currency
        ORDER BY total_billed_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "publisher_name": row.publisher_name,
                    "charge_description": row.charge_description,
                    "pricing_unit": row.pricing_unit,
                    "billing_currency": row.billing_currency,
                    "total_pricing_quantity": float(row.total_pricing_quantity or 0),
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "purchase_count": int(row.purchase_count or 0),
                    "avg_purchase_cost": float(row.avg_purchase_cost or 0),
                    "first_purchase": str(row.first_purchase)
                    if row.first_purchase
                    else None,
                    "last_purchase": str(row.last_purchase)
                    if row.last_purchase
                    else None,
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error analyzing virtual currency purchases: {e}")
            return []

    def get_contracted_savings_data(
        self,
        start_date: datetime,
        end_date: datetime,
        commitment_type: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get contracted savings data."""
        from sqlalchemy import text

        # Compare contracted vs list prices to determine savings
        sql = """
        SELECT
            service_name,
            COALESCE(service_subcategory, 'Unknown') as service_subcategory,
            charge_description,
            billing_currency,
            pricing_currency,
            SUM(list_unit_price - contracted_unit_price) AS contracted_savings_in_billing_currency,
            SUM(list_cost - contracted_cost) AS total_savings_amount,
            SUM(list_cost) AS total_list_cost,
            SUM(contracted_cost) AS total_contracted_cost,
            COUNT(*) AS charge_count,
            AVG(list_unit_price - contracted_unit_price) AS avg_unit_savings,
            COALESCE(commitment_discount_type, 'Unknown') as commitment_discount_type,
            COALESCE(commitment_discount_status, 'Unknown') as commitment_discount_status
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND list_unit_price > 0
            AND contracted_unit_price > 0
            AND list_unit_price > contracted_unit_price
            AND list_cost IS NOT NULL
            AND contracted_cost IS NOT NULL
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional commitment type filter
        if commitment_type:
            sql += " AND commitment_discount_type = :commitment_type"
            params["commitment_type"] = commitment_type

        sql += """
        GROUP BY
            service_name,
            service_subcategory,
            charge_description,
            billing_currency,
            pricing_currency,
            commitment_discount_type,
            commitment_discount_status
        HAVING contracted_savings_in_billing_currency > 0
        ORDER BY total_savings_amount DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "service_name": row.service_name,
                    "service_subcategory": row.service_subcategory,
                    "charge_description": row.charge_description,
                    "billing_currency": row.billing_currency,  # Może być None
                    "pricing_currency": row.pricing_currency,  # Może być None
                    "contracted_savings_in_billing_currency": float(
                        row.contracted_savings_in_billing_currency or 0
                    ),
                    "total_savings_amount": float(row.total_savings_amount or 0),
                    "total_list_cost": float(row.total_list_cost or 0),
                    "total_contracted_cost": float(row.total_contracted_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_unit_savings": float(row.avg_unit_savings or 0),
                    "commitment_discount_type": row.commitment_discount_type,
                    "commitment_discount_status": row.commitment_discount_status,
                    "savings_percentage": round(
                        (
                            float(row.total_savings_amount or 0)
                            / float(row.total_list_cost or 1)
                        )
                        * 100,
                        2,
                    ),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error analyzing contracted savings: {e}")
            return []

    def get_tag_coverage_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        required_tags: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Get tag coverage statistics."""
        from sqlalchemy import text

        # Analyze tag coverage - what percentage of costs are tagged
        base_sql = """
        SELECT
            SUM(CASE
                WHEN tags IS NOT NULL AND tags != '' AND tags != '{}'
                THEN effective_cost
                ELSE 0
            END) AS tagged_cost,
            SUM(effective_cost) AS total_cost,
            COUNT(CASE
                WHEN tags IS NOT NULL AND tags != '' AND tags != '{}'
                THEN 1
            END) AS tagged_resources,
            COUNT(*) AS total_resources,
            provider_name
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND effective_cost > 0
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional provider filter
        if provider_name:
            base_sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        base_sql += " GROUP BY provider_name"

        try:
            result = self.db.execute(text(base_sql), params)
            coverage_by_provider = []

            for row in result:
                tagged_cost = float(row.tagged_cost or 0)
                total_cost = float(row.total_cost or 0)
                tagged_resources = int(row.tagged_resources or 0)
                total_resources = int(row.total_resources or 0)

                cost_coverage_percentage = (
                    (tagged_cost / total_cost * 100) if total_cost > 0 else 0.0
                )
                resource_coverage_percentage = (
                    (tagged_resources / total_resources * 100)
                    if total_resources > 0
                    else 0.0
                )

                coverage_by_provider.append(
                    {
                        "provider_name": row.provider_name,
                        "tagged_cost": tagged_cost,
                        "total_cost": total_cost,
                        "tagged_resources": tagged_resources,
                        "total_resources": total_resources,
                        "cost_coverage_percentage": round(cost_coverage_percentage, 2),
                        "resource_coverage_percentage": round(
                            resource_coverage_percentage, 2
                        ),
                    }
                )

            # Overall statistics
            total_tagged_cost = sum(
                item["tagged_cost"] for item in coverage_by_provider
            )
            total_cost_all = sum(item["total_cost"] for item in coverage_by_provider)
            total_tagged_resources = sum(
                item["tagged_resources"] for item in coverage_by_provider
            )
            total_resources_all = sum(
                item["total_resources"] for item in coverage_by_provider
            )

            overall_cost_coverage = (
                (total_tagged_cost / total_cost_all * 100)
                if total_cost_all > 0
                else 0.0
            )
            overall_resource_coverage = (
                (total_tagged_resources / total_resources_all * 100)
                if total_resources_all > 0
                else 0.0
            )

            # Specific tag analysis if required_tags provided
            specific_tag_analysis = []
            if required_tags:
                for tag in required_tags:
                    tag_sql = """
                    SELECT
                        SUM(CASE
                            WHEN tags LIKE :tag_pattern
                            THEN effective_cost
                            ELSE 0
                        END) AS tag_specific_cost,
                        COUNT(CASE
                            WHEN tags LIKE :tag_pattern
                            THEN 1
                        END) AS tag_specific_resources
                    FROM billing_data
                    WHERE charge_period_start >= :start_date
                        AND charge_period_end < :end_date
                        AND effective_cost > 0
                    """

                    tag_params = {
                        "start_date": start_date,
                        "end_date": end_date,
                        "tag_pattern": f'%"{tag}"%',
                    }

                    if provider_name:
                        tag_sql += " AND provider_name = :provider_name"
                        tag_params["provider_name"] = provider_name

                    tag_result = self.db.execute(text(tag_sql), tag_params).first()

                    if tag_result:
                        tag_cost = float(tag_result.tag_specific_cost or 0)
                        tag_resources = int(tag_result.tag_specific_resources or 0)

                        specific_tag_analysis.append(
                            {
                                "tag_name": tag,
                                "tagged_cost": tag_cost,
                                "tagged_resources": tag_resources,
                                "cost_coverage_percentage": (
                                    tag_cost / total_cost_all * 100
                                )
                                if total_cost_all > 0
                                else 0.0,
                                "resource_coverage_percentage": (
                                    tag_resources / total_resources_all * 100
                                )
                                if total_resources_all > 0
                                else 0.0,
                            }
                        )

            return {
                "overall_coverage": {
                    "cost_coverage_percentage": round(overall_cost_coverage, 2),
                    "resource_coverage_percentage": round(overall_resource_coverage, 2),
                    "total_tagged_cost": total_tagged_cost,
                    "total_cost": total_cost_all,
                    "total_tagged_resources": total_tagged_resources,
                    "total_resources": total_resources_all,
                },
                "coverage_by_provider": coverage_by_provider,
                "specific_tag_analysis": specific_tag_analysis,
            }

        except Exception as e:
            logger.error(f"Error analyzing tag coverage: {e}")
            return {
                "overall_coverage": {
                    "cost_coverage_percentage": 0.0,
                    "resource_coverage_percentage": 0.0,
                    "total_tagged_cost": 0.0,
                    "total_cost": 0.0,
                    "total_tagged_resources": 0,
                    "total_resources": 0,
                },
                "coverage_by_provider": [],
                "specific_tag_analysis": [],
            }

    def get_sku_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        sku_id: str | None = None,
        provider_name: str | None = None,
        limit: int = 100,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get SKU cost breakdown."""
        from sqlalchemy import text

        # Analyze SKU metered costs breakdown
        sql = """
        SELECT
            provider_name,
            charge_period_start,
            charge_period_end,
            sku_id,
            sku_price_id,
            pricing_unit,
            list_unit_price,
            SUM(pricing_quantity) AS total_pricing_quantity,
            SUM(list_cost) AS total_list_cost,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            AVG(effective_cost) AS avg_effective_cost
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND sku_id IS NOT NULL
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if sku_id:
            sql += " AND sku_id = :sku_id"
            params["sku_id"] = sku_id

        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        sql += """
        GROUP BY
            provider_name,
            charge_period_start,
            charge_period_end,
            sku_id,
            sku_price_id,
            pricing_unit,
            list_unit_price
        ORDER BY
            charge_period_start ASC,
            total_effective_cost DESC
        LIMIT :limit
        """

        params["limit"] = limit

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "charge_period_start": str(row.charge_period_start),
                    "charge_period_end": str(row.charge_period_end),
                    "sku_id": row.sku_id,
                    "sku_price_id": row.sku_price_id,
                    "pricing_unit": row.pricing_unit,
                    "list_unit_price": float(row.list_unit_price or 0),
                    "total_pricing_quantity": float(row.total_pricing_quantity or 0),
                    "total_list_cost": float(row.total_list_cost or 0),
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_effective_cost": float(row.avg_effective_cost or 0),
                    "cost_per_unit": float(row.total_effective_cost or 0)
                    / float(row.total_pricing_quantity or 1)
                    if row.total_pricing_quantity and row.total_pricing_quantity > 0
                    else 0.0,
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error analyzing SKU costs: {e}")
            return []

    def get_costs_by_service_category(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_category: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get costs grouped by service category and subcategory."""
        from sqlalchemy import text

        sql = """
        SELECT
            provider_name,
            billing_currency,
            charge_period_start,
            service_category,
            service_subcategory,
            SUM(billed_cost) AS total_billed_cost,
            COUNT(*) AS charge_count,
            AVG(billed_cost) AS avg_billed_cost
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND billed_cost > 0
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if service_category:
            sql += " AND service_category = :service_category"
            params["service_category"] = service_category

        sql += """
        GROUP BY
            provider_name,
            billing_currency,
            charge_period_start,
            service_category,
            service_subcategory
        ORDER BY total_billed_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "billing_currency": row.billing_currency,
                    "charge_period_start": str(row.charge_period_start),
                    "service_category": row.service_category or "Unknown",
                    "service_subcategory": row.service_subcategory or "Unknown",
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_billed_cost": float(row.avg_billed_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting service category costs: {e}")
            return []

    def get_capacity_reservation_data(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        billing_account_id: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get capacity reservation analysis data."""
        from sqlalchemy import text

        sql = """
        SELECT
            CASE
                WHEN commitment_discount_id IS NOT NULL AND commitment_discount_status = 'Unused'
                THEN 'Unused Capacity Reservation'
                WHEN commitment_discount_id IS NOT NULL AND commitment_discount_status = 'Used'
                THEN 'Compute using Capacity Reservation'
                ELSE 'Compute without Capacity Reservation'
            END AS status,
            provider_name,
            billing_account_id,
            SUM(billed_cost) AS total_billed_cost,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            COUNT(DISTINCT commitment_discount_id) AS unique_reservations
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND service_category = 'Compute'
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if billing_account_id:
            sql += " AND billing_account_id = :billing_account_id"
            params["billing_account_id"] = billing_account_id

        sql += """
        GROUP BY
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_status
        ORDER BY total_effective_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "status": row.status,
                    "provider_name": row.provider_name,
                    "billing_account_id": row.billing_account_id or "Unknown",
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "unique_reservations": int(row.unique_reservations or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting capacity reservation data: {e}")
            return []

    def get_unused_capacity_data(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        billing_account_id: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get unused capacity reservation data."""
        from sqlalchemy import text

        sql = """
        SELECT
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_status,
            SUM(billed_cost) AS total_billed_cost,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            MIN(charge_period_start) AS first_charge_date,
            MAX(charge_period_end) AS last_charge_date
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND commitment_discount_status = 'Unused'
            AND commitment_discount_id IS NOT NULL
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if billing_account_id:
            sql += " AND billing_account_id = :billing_account_id"
            params["billing_account_id"] = billing_account_id

        sql += """
        GROUP BY
            provider_name,
            billing_account_id,
            commitment_discount_id,
            commitment_discount_status
        ORDER BY total_effective_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "billing_account_id": row.billing_account_id or "Unknown",
                    "commitment_discount_id": row.commitment_discount_id,
                    "commitment_discount_status": row.commitment_discount_status,
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "first_charge_date": str(row.first_charge_date)
                    if row.first_charge_date
                    else None,
                    "last_charge_date": str(row.last_charge_date)
                    if row.last_charge_date
                    else None,
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting unused capacity data: {e}")
            return []

    def get_refunds_data(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        billing_account_id: str | None = None,
        service_category: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get refunds grouped by subaccount."""
        from sqlalchemy import text

        sql = """
        SELECT
            provider_name,
            billing_account_id,
            service_category,
            sub_account_id,
            sub_account_name,
            SUM(billed_cost) AS total_billed_cost,
            COUNT(*) AS refund_count,
            MIN(billing_period_start) AS earliest_refund,
            MAX(billing_period_end) AS latest_refund,
            AVG(billed_cost) AS avg_refund_amount
        FROM billing_data
        WHERE billing_period_start >= :start_date
            AND billing_period_end < :end_date
            AND charge_class = 'Correction'
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if billing_account_id:
            sql += " AND billing_account_id = :billing_account_id"
            params["billing_account_id"] = billing_account_id

        if service_category:
            sql += " AND service_category = :service_category"
            params["service_category"] = service_category

        sql += """
        GROUP BY
            provider_name,
            billing_account_id,
            sub_account_id,
            sub_account_name,
            service_category
        ORDER BY total_billed_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "billing_account_id": row.billing_account_id or "Unknown",
                    "service_category": row.service_category or "Unknown",
                    "sub_account_id": row.sub_account_id or "Unknown",
                    "sub_account_name": row.sub_account_name or "Unknown",
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "refund_count": int(row.refund_count or 0),
                    "earliest_refund": str(row.earliest_refund)
                    if row.earliest_refund
                    else None,
                    "latest_refund": str(row.latest_refund)
                    if row.latest_refund
                    else None,
                    "avg_refund_amount": float(row.avg_refund_amount or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting refunds data: {e}")
            return []

    def get_commitment_charges(
        self,
        start_date: datetime,
        end_date: datetime,
        commitment_discount_type: str | None = None,
        charge_frequency: str = "Recurring",
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get recurring commitment charges."""
        from sqlalchemy import text

        sql = """
        SELECT
            billing_period_start,
            commitment_discount_id,
            commitment_discount_name,
            commitment_discount_type,
            charge_frequency,
            SUM(billed_cost) AS total_billed_cost,
            COUNT(*) AS charge_count,
            AVG(billed_cost) AS avg_charge_amount,
            MIN(effective_cost) AS min_effective_cost,
            MAX(effective_cost) AS max_effective_cost
        FROM billing_data
        WHERE billing_period_start >= :start_date
            AND billing_period_start < :end_date
            AND charge_frequency = :charge_frequency
            AND commitment_discount_id IS NOT NULL
        """

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "charge_frequency": charge_frequency,
        }

        # Add optional commitment type filter
        if commitment_discount_type:
            sql += " AND commitment_discount_type = :commitment_discount_type"
            params["commitment_discount_type"] = commitment_discount_type

        sql += """
        GROUP BY
            billing_period_start,
            commitment_discount_id,
            commitment_discount_name,
            commitment_discount_type,
            charge_frequency
        ORDER BY billing_period_start ASC, total_billed_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "billing_period_start": str(row.billing_period_start),
                    "commitment_discount_id": row.commitment_discount_id,
                    "commitment_discount_name": row.commitment_discount_name
                    or "Unknown",
                    "commitment_discount_type": row.commitment_discount_type
                    or "Unknown",
                    "charge_frequency": row.charge_frequency,
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_charge_amount": float(row.avg_charge_amount or 0),
                    "min_effective_cost": float(row.min_effective_cost or 0),
                    "max_effective_cost": float(row.max_effective_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting commitment charges: {e}")
            return []

    def get_service_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        service_name: str,
        provider_name: str | None = None,
        sub_account_id: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get costs by service name."""
        from sqlalchemy import text

        sql = """
        SELECT
            billing_period_start,
            provider_name,
            sub_account_id,
            sub_account_name,
            service_name,
            SUM(billed_cost) AS total_billed_cost,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            AVG(effective_cost) AS avg_effective_cost,
            MIN(effective_cost) AS min_effective_cost,
            MAX(effective_cost) AS max_effective_cost
        FROM billing_data
        WHERE service_name = :service_name
            AND billing_period_start >= :start_date
            AND billing_period_start < :end_date
        """

        params = {
            "service_name": service_name,
            "start_date": start_date,
            "end_date": end_date,
        }

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if sub_account_id:
            sql += " AND sub_account_id = :sub_account_id"
            params["sub_account_id"] = sub_account_id

        sql += """
        GROUP BY
            billing_period_start,
            provider_name,
            sub_account_id,
            sub_account_name,
            service_name
        ORDER BY total_effective_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "billing_period_start": str(row.billing_period_start),
                    "provider_name": row.provider_name,
                    "sub_account_id": row.sub_account_id or "Unknown",
                    "sub_account_name": row.sub_account_name or "Unknown",
                    "service_name": row.service_name,
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_effective_cost": float(row.avg_effective_cost or 0),
                    "min_effective_cost": float(row.min_effective_cost or 0),
                    "max_effective_cost": float(row.max_effective_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting service costs: {e}")
            return []

    def get_spending_by_period(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str,
        service_category: str | None = None,
        billing_account_id: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get spending across billing periods."""
        from sqlalchemy import text

        sql = """
        SELECT
            provider_name,
            billing_account_name,
            billing_account_id,
            billing_currency,
            billing_period_start,
            service_category,
            service_name,
            SUM(billed_cost) AS total_billed_cost,
            COUNT(*) AS charge_count,
            AVG(billed_cost) AS avg_billed_cost,
            MIN(billed_cost) AS min_billed_cost,
            MAX(billed_cost) AS max_billed_cost
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND provider_name = :provider_name
        """

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "provider_name": provider_name,
        }

        # Add optional filters
        if service_category:
            sql += " AND service_category = :service_category"
            params["service_category"] = service_category

        if billing_account_id:
            sql += " AND billing_account_id = :billing_account_id"
            params["billing_account_id"] = billing_account_id

        sql += """
        GROUP BY
            provider_name,
            billing_account_name,
            billing_account_id,
            billing_currency,
            billing_period_start,
            service_category,
            service_name
        ORDER BY total_billed_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "billing_account_name": row.billing_account_name or "Unknown",
                    "billing_account_id": row.billing_account_id or "Unknown",
                    "billing_currency": row.billing_currency or "USD",
                    "billing_period_start": str(row.billing_period_start),
                    "service_category": row.service_category or "Unknown",
                    "service_name": row.service_name or "Unknown",
                    "total_billed_cost": float(row.total_billed_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_billed_cost": float(row.avg_billed_cost or 0),
                    "min_billed_cost": float(row.min_billed_cost or 0),
                    "max_billed_cost": float(row.max_billed_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting spending by period: {e}")
            return []

    def get_costs_by_region(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        region_id: str | None = None,
        service_name: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get service costs by region."""
        from sqlalchemy import text

        sql = """
        SELECT
            charge_period_start,
            provider_name,
            region_id,
            region_name,
            service_name,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            AVG(effective_cost) AS avg_effective_cost,
            MIN(effective_cost) AS min_effective_cost,
            MAX(effective_cost) AS max_effective_cost
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if region_id:
            sql += " AND region_id = :region_id"
            params["region_id"] = region_id

        if service_name:
            sql += " AND service_name = :service_name"
            params["service_name"] = service_name

        sql += """
        GROUP BY
            charge_period_start,
            provider_name,
            region_id,
            region_name,
            service_name
        ORDER BY
            charge_period_start,
            total_effective_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "charge_period_start": str(row.charge_period_start),
                    "provider_name": row.provider_name,
                    "region_id": row.region_id or "Unknown",
                    "region_name": row.region_name or "Unknown",
                    "service_name": row.service_name or "Unknown",
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_effective_cost": float(row.avg_effective_cost or 0),
                    "min_effective_cost": float(row.min_effective_cost or 0),
                    "max_effective_cost": float(row.max_effective_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting costs by region: {e}")
            return []

    def get_costs_by_subaccount(
        self,
        start_date: datetime,
        end_date: datetime,
        sub_account_id: str,
        provider_name: str,
        service_name: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get service costs by subaccount."""
        from sqlalchemy import text

        sql = """
        SELECT
            provider_name,
            service_name,
            sub_account_id,
            sub_account_name,
            charge_period_start,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            AVG(effective_cost) AS avg_effective_cost,
            MIN(effective_cost) AS min_effective_cost,
            MAX(effective_cost) AS max_effective_cost,
            MIN(billing_period_start) AS billing_period_start
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_end < :end_date
            AND sub_account_id = :sub_account_id
            AND provider_name = :provider_name
        """

        params = {
            "start_date": start_date,
            "end_date": end_date,
            "sub_account_id": sub_account_id,
            "provider_name": provider_name,
        }

        # Add optional service filter
        if service_name:
            sql += " AND service_name = :service_name"
            params["service_name"] = service_name

        sql += """
        GROUP BY
            provider_name,
            service_name,
            sub_account_id,
            sub_account_name,
            charge_period_start
        ORDER BY
            total_effective_cost DESC,
            billing_period_start DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "provider_name": row.provider_name,
                    "service_name": row.service_name or "Unknown",
                    "sub_account_id": row.sub_account_id,
                    "sub_account_name": row.sub_account_name or "Unknown",
                    "charge_period_start": str(row.charge_period_start),
                    "billing_period_start": str(row.billing_period_start)
                    if row.billing_period_start
                    else None,
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_effective_cost": float(row.avg_effective_cost or 0),
                    "min_effective_cost": float(row.min_effective_cost or 0),
                    "max_effective_cost": float(row.max_effective_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting costs by subaccount: {e}")
            return []

    def get_service_cost_trend_data(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_name: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get service cost trend data."""
        from sqlalchemy import text

        # Check database type and use appropriate date functions
        db_dialect = self.db.bind.dialect.name

        if db_dialect == "postgresql":
            # PostgreSQL uses EXTRACT
            month_expr = "EXTRACT(MONTH FROM charge_period_start)"
            year_expr = "EXTRACT(YEAR FROM charge_period_start)"
        else:
            # SQLite uses strftime
            month_expr = "CAST(strftime('%m', charge_period_start) AS INTEGER)"
            year_expr = "CAST(strftime('%Y', charge_period_start) AS INTEGER)"

        sql = f"""
        SELECT
            {month_expr} AS charge_month,
            {year_expr} AS charge_year,
            provider_name,
            service_name,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            AVG(effective_cost) AS avg_effective_cost
        FROM billing_data
        WHERE charge_period_start >= :start_date
            AND charge_period_start < :end_date
        """

        params = {"start_date": start_date, "end_date": end_date}

        # Add optional filters
        if provider_name:
            sql += " AND provider_name = :provider_name"
            params["provider_name"] = provider_name

        if service_name:
            sql += " AND service_name = :service_name"
            params["service_name"] = service_name

        sql += f"""
        GROUP BY
            {month_expr},
            {year_expr},
            provider_name,
            service_name
        ORDER BY
            charge_year,
            charge_month,
            total_effective_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "charge_month": int(row.charge_month),
                    "charge_year": int(row.charge_year),
                    "month_name": f"{int(row.charge_year)}-{int(row.charge_month):02d}",
                    "provider_name": row.provider_name,
                    "service_name": row.service_name or "Unknown",
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_effective_cost": float(row.avg_effective_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting service cost trend data: {e}")
            return []

    def get_application_cost_trend_data(
        self,
        start_date: datetime,
        end_date: datetime,
        application_tag: str,
        service_name: str | None = None,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Get application cost trend data."""
        from sqlalchemy import text

        # Check database type and use appropriate date functions
        db_dialect = self.db.bind.dialect.name

        if db_dialect == "postgresql":
            # PostgreSQL uses EXTRACT
            month_expr = "EXTRACT(MONTH FROM billing_period_start)"
            year_expr = "EXTRACT(YEAR FROM billing_period_start)"
        else:
            # SQLite uses strftime
            month_expr = "CAST(strftime('%m', billing_period_start) AS INTEGER)"
            year_expr = "CAST(strftime('%Y', billing_period_start) AS INTEGER)"

        sql = f"""
        SELECT
            {month_expr} AS billing_month,
            {year_expr} AS billing_year,
            service_name,
            SUM(effective_cost) AS total_effective_cost,
            COUNT(*) AS charge_count,
            AVG(effective_cost) AS avg_effective_cost
        FROM billing_data
        WHERE tags LIKE :application_tag
            AND charge_period_start >= :start_date
            AND charge_period_end < :end_date
        """

        params = {
            "application_tag": f'%"Application":"{application_tag}"%',
            "start_date": start_date,
            "end_date": end_date,
        }

        # Add optional service filter
        if service_name:
            sql += " AND service_name = :service_name"
            params["service_name"] = service_name

        sql += f"""
        GROUP BY
            {month_expr},
            {year_expr},
            service_name
        ORDER BY
            billing_year,
            billing_month,
            total_effective_cost DESC
        """

        try:
            result = self.db.execute(text(sql), params)
            return [
                {
                    "billing_month": int(row.billing_month),
                    "billing_year": int(row.billing_year),
                    "month_name": f"{int(row.billing_year)}-{int(row.billing_month):02d}",
                    "service_name": row.service_name or "Unknown",
                    "total_effective_cost": float(row.total_effective_cost or 0),
                    "charge_count": int(row.charge_count or 0),
                    "avg_effective_cost": float(row.avg_effective_cost or 0),
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting application cost trend data: {e}")
            return []

    def get_distinct_provider_names(self) -> list[str]:
        """Get distinct provider names from billing data for connected providers only."""
        from sqlalchemy import text

        sql = """
        SELECT DISTINCT provider_name
        FROM billing_data
        WHERE provider_name IS NOT NULL
        ORDER BY provider_name
        """

        try:
            result = self.db.execute(text(sql))
            return [row.provider_name for row in result]
        except Exception as e:
            logger.error(f"Error getting distinct provider names: {e}")
            return []

    def get_distinct_service_names(self) -> list[dict[str, Any]]:
        """Get distinct service names with provider and category info from billing data."""
        from sqlalchemy import text

        sql = """
        SELECT DISTINCT
            service_name,
            provider_name,
            service_category
        FROM billing_data
        WHERE service_name IS NOT NULL
        ORDER BY provider_name, service_name
        """

        try:
            result = self.db.execute(text(sql))
            return [
                {
                    "service_name": row.service_name,
                    "provider_name": row.provider_name,
                    "service_category": row.service_category or "Unknown",
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"Error getting distinct service names: {e}")
            return []
