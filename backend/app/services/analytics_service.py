"""
Analytics Service Layer - FOCUS Use Cases Implementation
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.repositories.analytics_repository import AnalyticsRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service layer for analytics operations."""

    def __init__(self, db: Session):
        """Initialize analytics service."""
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)

    def calculate_resource_rate(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_name: str | None = None,
        region_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Calculate average rate of a component resource."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_resource_rate_data(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                service_name=service_name,
                region_name=region_name,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_resources": 0,
                        "total_core_count": 0,
                        "average_cost_per_core": 0.0,
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "service_name": service_name,
                        "region_name": region_name,
                    },
                }

            # Calculate summary statistics
            total_resources = len(data)
            total_core_count = sum(item["total_core_count"] for item in data)
            total_cost = sum(
                item["average_effective_core_cost"] * item["total_core_count"]
                for item in data
                if item["average_effective_core_cost"]
            )
            overall_average = (
                total_cost / total_core_count if total_core_count > 0 else 0.0
            )

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_resources": total_resources,
                    "total_core_count": total_core_count,
                    "average_cost_per_core": round(overall_average, 4),
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "service_name": service_name,
                    "region_name": region_name,
                },
            }

        except Exception as e:
            logger.error(f"Error in calculate_resource_rate: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def quantify_resource_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_name: str | None = None,
        region_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Quantify usage of a component resource."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_resource_usage_data(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                service_name=service_name,
                region_name=region_name,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_core_count": 0,
                        "total_resources": 0,
                        "unique_instance_series": 0,
                        "unique_services": 0,
                        "unique_regions": 0,
                        "avg_cores_per_resource": 0.0,
                        "instance_series_breakdown": [],
                        "region_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "service_name": service_name,
                        "region_name": region_name,
                    },
                }

            # Calculate summary statistics
            total_core_count = sum(item["total_core_count"] for item in data)
            total_resources = sum(item["resource_count"] for item in data)
            unique_instance_series = len({item["instance_series"] for item in data})
            unique_services = len({item["service_name"] for item in data})
            unique_regions = len({item["region_name"] for item in data})
            avg_cores_per_resource = (
                total_core_count / total_resources if total_resources > 0 else 0.0
            )

            # Instance series breakdown
            series_totals = {}
            for item in data:
                series = item["instance_series"]
                if series not in series_totals:
                    series_totals[series] = {
                        "total_cores": 0,
                        "resource_count": 0,
                        "regions": set(),
                        "services": set(),
                    }
                series_totals[series]["total_cores"] += item["total_core_count"]
                series_totals[series]["resource_count"] += item["resource_count"]
                series_totals[series]["regions"].add(item["region_name"])
                series_totals[series]["services"].add(item["service_name"])

            instance_series_breakdown = [
                {
                    "instance_series": series,
                    "total_cores": stats["total_cores"],
                    "resource_count": stats["resource_count"],
                    "unique_regions": len(stats["regions"]),
                    "unique_services": len(stats["services"]),
                    "avg_cores_per_resource": round(
                        stats["total_cores"] / stats["resource_count"]
                        if stats["resource_count"] > 0
                        else 0.0,
                        2,
                    ),
                    "core_percentage": round(
                        (stats["total_cores"] / total_core_count * 100)
                        if total_core_count > 0
                        else 0.0,
                        2,
                    ),
                }
                for series, stats in sorted(
                    series_totals.items(),
                    key=lambda x: x[1]["total_cores"],
                    reverse=True,
                )
            ]

            # Region breakdown
            region_totals = {}
            for item in data:
                region = item["region_name"]
                if region not in region_totals:
                    region_totals[region] = {
                        "total_cores": 0,
                        "resource_count": 0,
                        "instance_series": set(),
                        "services": set(),
                    }
                region_totals[region]["total_cores"] += item["total_core_count"]
                region_totals[region]["resource_count"] += item["resource_count"]
                region_totals[region]["instance_series"].add(item["instance_series"])
                region_totals[region]["services"].add(item["service_name"])

            region_breakdown = [
                {
                    "region_name": region,
                    "total_cores": stats["total_cores"],
                    "resource_count": stats["resource_count"],
                    "unique_instance_series": len(stats["instance_series"]),
                    "unique_services": len(stats["services"]),
                    "avg_cores_per_resource": round(
                        stats["total_cores"] / stats["resource_count"]
                        if stats["resource_count"] > 0
                        else 0.0,
                        2,
                    ),
                    "core_percentage": round(
                        (stats["total_cores"] / total_core_count * 100)
                        if total_core_count > 0
                        else 0.0,
                        2,
                    ),
                }
                for region, stats in sorted(
                    region_totals.items(),
                    key=lambda x: x[1]["total_cores"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_core_count": total_core_count,
                    "total_resources": total_resources,
                    "unique_instance_series": unique_instance_series,
                    "unique_services": unique_services,
                    "unique_regions": unique_regions,
                    "avg_cores_per_resource": round(avg_cores_per_resource, 2),
                    "instance_series_breakdown": instance_series_breakdown,
                    "region_breakdown": region_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "service_name": service_name,
                    "region_name": region_name,
                },
            }

        except Exception as e:
            logger.error(f"Error in quantify_resource_usage: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def calculate_unit_economics(
        self,
        start_date: datetime,
        end_date: datetime,
        unit_type: str = "GB",
        charge_description_filter: str = "transfer",
        **kwargs,
    ) -> dict[str, Any]:
        """Calculate unit economics."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_unit_economics_data(
                start_date=start_date,
                end_date=end_date,
                unit_type=unit_type,
                charge_description_filter=charge_description_filter,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_days": 0,
                        "total_cost": 0.0,
                        "total_quantity": 0.0,
                        "average_cost_per_unit": 0.0,
                        "unit_type": unit_type,
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "unit_type": unit_type,
                        "charge_description_filter": charge_description_filter,
                    },
                }

            # Calculate summary statistics
            total_days = len(data)
            total_cost = sum(item["total_cost"] for item in data)
            total_quantity = sum(item["total_quantity"] for item in data)
            average_cost_per_unit = (
                total_cost / total_quantity if total_quantity > 0 else 0.0
            )

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_days": total_days,
                    "total_cost": round(total_cost, 4),
                    "total_quantity": round(total_quantity, 2),
                    "average_cost_per_unit": round(average_cost_per_unit, 6),
                    "unit_type": unit_type,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "unit_type": unit_type,
                    "charge_description_filter": charge_description_filter,
                },
            }

        except Exception as e:
            logger.error(f"Error in calculate_unit_economics: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_virtual_currency_target(
        self,
        start_date: datetime,
        end_date: datetime,
        pricing_currency: str | None = None,
        limit: int = 10,
        **kwargs,
    ) -> dict[str, Any]:
        """Determine target of virtual currency usage."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_virtual_currency_usage(
                start_date=start_date,
                end_date=end_date,
                pricing_currency=pricing_currency,
                limit=limit,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_charges": 0,
                        "total_cost": 0.0,
                        "unique_services": 0,
                        "top_currency": None,
                        "currencies_found": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "pricing_currency": pricing_currency,
                        "limit": limit,
                    },
                }

            # Calculate summary statistics
            total_charges = sum(item["charge_count"] for item in data)
            total_cost = sum(item["total_effective_cost"] for item in data)
            unique_services = len({item["service_name"] for item in data})
            currencies_found = list({item["pricing_currency"] for item in data})
            top_currency = (
                max(data, key=lambda x: x["total_effective_cost"])["pricing_currency"]
                if data
                else None
            )

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_charges": total_charges,
                    "total_cost": round(total_cost, 4),
                    "unique_services": unique_services,
                    "top_currency": top_currency,
                    "currencies_found": sorted(currencies_found),
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "pricing_currency": pricing_currency,
                    "limit": limit,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_virtual_currency_target: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_effective_cost_by_currency(
        self,
        start_date: datetime,
        end_date: datetime,
        include_exchange_rates: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze effective cost by pricing currency."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_costs_by_currency(
                start_date=start_date,
                end_date=end_date,
                include_exchange_rates=include_exchange_rates,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_cost": 0.0,
                        "total_charges": 0,
                        "unique_currencies": 0,
                        "unique_services": 0,
                        "currency_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "include_exchange_rates": include_exchange_rates,
                    },
                }

            # Calculate summary statistics
            total_cost = sum(item["total_effective_cost"] for item in data)
            total_charges = sum(item["charge_count"] for item in data)
            unique_currencies = len({item["pricing_currency"] for item in data})
            unique_services = len({item["service_name"] for item in data})

            # Currency breakdown
            currency_totals = {}
            for item in data:
                currency = item["pricing_currency"]
                if currency not in currency_totals:
                    currency_totals[currency] = 0
                currency_totals[currency] += item["total_effective_cost"]

            currency_breakdown = [
                {"currency": currency, "total_cost": round(cost, 4)}
                for currency, cost in sorted(
                    currency_totals.items(), key=lambda x: x[1], reverse=True
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_cost": round(total_cost, 4),
                    "total_charges": total_charges,
                    "unique_currencies": unique_currencies,
                    "unique_services": unique_services,
                    "currency_breakdown": currency_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "include_exchange_rates": include_exchange_rates,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_effective_cost_by_currency: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_virtual_currency_purchases(
        self,
        start_date: datetime,
        end_date: datetime,
        pricing_unit: str | None = None,
        group_by: str = "service",
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze purchase of virtual currency."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_virtual_currency_purchases(
                start_date=start_date,
                end_date=end_date,
                pricing_unit=pricing_unit,
                group_by=group_by,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_purchases": 0,
                        "total_cost": 0.0,
                        "total_quantity": 0.0,
                        "unique_units": 0,
                        "avg_purchase_cost": 0.0,
                        "unit_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "pricing_unit": pricing_unit,
                        "group_by": group_by,
                    },
                }

            # Calculate summary statistics
            total_purchases = sum(item["purchase_count"] for item in data)
            total_cost = sum(item["total_billed_cost"] for item in data)
            total_quantity = sum(item["total_pricing_quantity"] for item in data)
            unique_units = len(
                {item["pricing_unit"] for item in data if item["pricing_unit"]}
            )
            avg_purchase_cost = (
                total_cost / total_purchases if total_purchases > 0 else 0.0
            )

            # Unit breakdown
            unit_totals = {}
            for item in data:
                unit = item["pricing_unit"] or "Unknown"
                if unit not in unit_totals:
                    unit_totals[unit] = {"cost": 0.0, "quantity": 0.0, "count": 0}
                unit_totals[unit]["cost"] += item["total_billed_cost"]
                unit_totals[unit]["quantity"] += item["total_pricing_quantity"]
                unit_totals[unit]["count"] += item["purchase_count"]

            unit_breakdown = [
                {
                    "pricing_unit": unit,
                    "total_cost": round(stats["cost"], 4),
                    "total_quantity": round(stats["quantity"], 2),
                    "purchase_count": stats["count"],
                }
                for unit, stats in sorted(
                    unit_totals.items(), key=lambda x: x[1]["cost"], reverse=True
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_purchases": total_purchases,
                    "total_cost": round(total_cost, 4),
                    "total_quantity": round(total_quantity, 2),
                    "unique_units": unique_units,
                    "avg_purchase_cost": round(avg_purchase_cost, 4),
                    "unit_breakdown": unit_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "pricing_unit": pricing_unit,
                    "group_by": group_by,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_virtual_currency_purchases: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_contracted_savings(
        self,
        start_date: datetime,
        end_date: datetime,
        commitment_type: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Determine contracted savings by virtual currency."""
        logger.debug("service analyze_contracted_savings called")
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_contracted_savings_data(
                start_date=start_date,
                end_date=end_date,
                commitment_type=commitment_type,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_savings": 0.0,
                        "total_list_cost": 0.0,
                        "total_contracted_cost": 0.0,
                        "overall_savings_percentage": 0.0,
                        "total_charges": 0,
                        "commitment_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "commitment_type": commitment_type,
                    },
                }

            # Calculate summary statistics
            total_savings = sum(item["total_savings_amount"] for item in data)
            total_list_cost = sum(item["total_list_cost"] for item in data)
            total_contracted_cost = sum(item["total_contracted_cost"] for item in data)
            total_charges = sum(item["charge_count"] for item in data)
            overall_savings_percentage = (
                (total_savings / total_list_cost * 100) if total_list_cost > 0 else 0.0
            )

            # Commitment type breakdown
            commitment_totals = {}
            for item in data:
                commitment = item["commitment_discount_type"]
                if commitment not in commitment_totals:
                    commitment_totals[commitment] = {
                        "savings": 0.0,
                        "list_cost": 0.0,
                        "charges": 0,
                    }
                commitment_totals[commitment]["savings"] += item["total_savings_amount"]
                commitment_totals[commitment]["list_cost"] += item["total_list_cost"]
                commitment_totals[commitment]["charges"] += item["charge_count"]

            commitment_breakdown = [
                {
                    "commitment_type": commitment,
                    "total_savings": round(stats["savings"], 4),
                    "total_list_cost": round(stats["list_cost"], 4),
                    "charge_count": stats["charges"],
                    "savings_percentage": round(
                        (stats["savings"] / stats["list_cost"] * 100)
                        if stats["list_cost"] > 0
                        else 0.0,
                        2,
                    ),
                }
                for commitment, stats in sorted(
                    commitment_totals.items(),
                    key=lambda x: x[1]["savings"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_savings": round(total_savings, 4),
                    "total_list_cost": round(total_list_cost, 4),
                    "total_contracted_cost": round(total_contracted_cost, 4),
                    "overall_savings_percentage": round(overall_savings_percentage, 2),
                    "total_charges": total_charges,
                    "commitment_breakdown": commitment_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "commitment_type": commitment_type,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_contracted_savings: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_tag_coverage(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        required_tags: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze tag coverage."""
        try:
            # Get tag coverage statistics from repository
            stats = self.analytics_repo.get_tag_coverage_stats(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                required_tags=required_tags,
                **kwargs,
            )

            return {
                "status": "success",
                "data": stats,
                "summary": {
                    "overall_cost_coverage": stats["overall_coverage"][
                        "cost_coverage_percentage"
                    ],
                    "overall_resource_coverage": stats["overall_coverage"][
                        "resource_coverage_percentage"
                    ],
                    "total_providers": len(stats["coverage_by_provider"]),
                    "tags_analyzed": len(stats["specific_tag_analysis"]),
                    "untagged_cost": stats["overall_coverage"]["total_cost"]
                    - stats["overall_coverage"]["total_tagged_cost"],
                    "untagged_resources": stats["overall_coverage"]["total_resources"]
                    - stats["overall_coverage"]["total_tagged_resources"],
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "required_tags": required_tags or [],
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_tag_coverage: {e}")
            return {
                "status": "error",
                "message": str(e),
                "data": {
                    "overall_coverage": {},
                    "coverage_by_provider": [],
                    "specific_tag_analysis": [],
                },
            }

    def analyze_sku_metered_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        sku_id: str | None = None,
        provider_name: str | None = None,
        limit: int = 100,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze the different metered costs for a particular SKU."""
        try:
            # Get SKU cost breakdown from repository
            data = self.analytics_repo.get_sku_costs(
                start_date=start_date,
                end_date=end_date,
                sku_id=sku_id,
                provider_name=provider_name,
                limit=limit,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_skus": 0,
                        "total_cost": 0.0,
                        "total_quantity": 0.0,
                        "unique_pricing_units": 0,
                        "date_range_days": (end_date - start_date).days,
                        "pricing_unit_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "sku_id": sku_id,
                        "provider_name": provider_name,
                        "limit": limit,
                    },
                }

            # Calculate summary statistics
            total_skus = len({item["sku_id"] for item in data})
            total_cost = sum(item["total_effective_cost"] for item in data)
            total_quantity = sum(item["total_pricing_quantity"] for item in data)
            unique_pricing_units = len(
                {item["pricing_unit"] for item in data if item["pricing_unit"]}
            )
            date_range_days = (end_date - start_date).days

            # Pricing unit breakdown
            unit_breakdown = {}
            for item in data:
                unit = item["pricing_unit"] or "Unknown"
                if unit not in unit_breakdown:
                    unit_breakdown[unit] = {
                        "total_cost": 0.0,
                        "total_quantity": 0.0,
                        "charge_count": 0,
                        "skus_count": set(),
                    }
                unit_breakdown[unit]["total_cost"] += item["total_effective_cost"]
                unit_breakdown[unit]["total_quantity"] += item["total_pricing_quantity"]
                unit_breakdown[unit]["charge_count"] += item["charge_count"]
                unit_breakdown[unit]["skus_count"].add(item["sku_id"])

            pricing_unit_breakdown = [
                {
                    "pricing_unit": unit,
                    "total_cost": round(stats["total_cost"], 4),
                    "total_quantity": round(stats["total_quantity"], 2),
                    "charge_count": stats["charge_count"],
                    "unique_skus": len(stats["skus_count"]),
                    "avg_cost_per_unit": round(
                        stats["total_cost"] / stats["total_quantity"]
                        if stats["total_quantity"] > 0
                        else 0.0,
                        6,
                    ),
                }
                for unit, stats in sorted(
                    unit_breakdown.items(),
                    key=lambda x: x[1]["total_cost"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_skus": total_skus,
                    "total_cost": round(total_cost, 4),
                    "total_quantity": round(total_quantity, 2),
                    "unique_pricing_units": unique_pricing_units,
                    "date_range_days": date_range_days,
                    "pricing_unit_breakdown": pricing_unit_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "sku_id": sku_id,
                    "provider_name": provider_name,
                    "limit": limit,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_sku_metered_costs: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_service_category_breakdown(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_category: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Report costs by service category and subcategory."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_costs_by_service_category(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                service_category=service_category,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_cost": 0.0,
                        "total_charges": 0,
                        "unique_categories": 0,
                        "unique_subcategories": 0,
                        "unique_providers": 0,
                        "category_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "service_category": service_category,
                    },
                }

            # Calculate summary statistics
            total_cost = sum(item["total_billed_cost"] for item in data)
            total_charges = sum(item["charge_count"] for item in data)
            unique_categories = len({item["service_category"] for item in data})
            unique_subcategories = len({item["service_subcategory"] for item in data})
            unique_providers = len({item["provider_name"] for item in data})

            # Category breakdown
            category_totals = {}
            for item in data:
                category = item["service_category"]
                if category not in category_totals:
                    category_totals[category] = {
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "subcategories": set(),
                    }
                category_totals[category]["total_cost"] += item["total_billed_cost"]
                category_totals[category]["charge_count"] += item["charge_count"]
                category_totals[category]["subcategories"].add(
                    item["service_subcategory"]
                )

            category_breakdown = [
                {
                    "service_category": category,
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "unique_subcategories": len(stats["subcategories"]),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_cost * 100)
                        if total_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for category, stats in sorted(
                    category_totals.items(),
                    key=lambda x: x[1]["total_cost"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_cost": round(total_cost, 4),
                    "total_charges": total_charges,
                    "unique_categories": unique_categories,
                    "unique_subcategories": unique_subcategories,
                    "unique_providers": unique_providers,
                    "category_breakdown": category_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "service_category": service_category,
                },
            }

        except Exception as e:
            logger.error(f"Error in get_service_category_breakdown: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_capacity_reservations(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        billing_account_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze capacity reservations on compute costs."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_capacity_reservation_data(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                billing_account_id=billing_account_id,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_compute_cost": 0.0,
                        "total_charges": 0,
                        "reservation_utilization_percentage": 0.0,
                        "cost_with_reservations": 0.0,
                        "cost_without_reservations": 0.0,
                        "total_reservations": 0,
                        "status_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "billing_account_id": billing_account_id,
                    },
                }

            # Calculate summary statistics
            total_compute_cost = sum(item["total_effective_cost"] for item in data)
            total_charges = sum(item["charge_count"] for item in data)

            # Calculate costs by reservation usage
            cost_with_reservations = sum(
                item["total_effective_cost"]
                for item in data
                if "Capacity Reservation" in item["status"]
                and item["status"] != "Compute without Capacity Reservation"
            )
            cost_without_reservations = sum(
                item["total_effective_cost"]
                for item in data
                if item["status"] == "Compute without Capacity Reservation"
            )

            used_reservation_cost = sum(
                item["total_effective_cost"]
                for item in data
                if item["status"] == "Compute using Capacity Reservation"
            )

            # Calculate utilization percentage (used vs total reservation cost)
            reservation_utilization_percentage = (
                (used_reservation_cost / cost_with_reservations * 100)
                if cost_with_reservations > 0
                else 0.0
            )

            total_reservations = sum(item["unique_reservations"] for item in data)

            # Status breakdown
            status_totals = {}
            for item in data:
                status = item["status"]
                if status not in status_totals:
                    status_totals[status] = {
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "unique_reservations": 0,
                    }
                status_totals[status]["total_cost"] += item["total_effective_cost"]
                status_totals[status]["charge_count"] += item["charge_count"]
                status_totals[status]["unique_reservations"] += item[
                    "unique_reservations"
                ]

            status_breakdown = [
                {
                    "status": status,
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "unique_reservations": stats["unique_reservations"],
                    "cost_percentage": round(
                        (stats["total_cost"] / total_compute_cost * 100)
                        if total_compute_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for status, stats in sorted(
                    status_totals.items(),
                    key=lambda x: x[1]["total_cost"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_compute_cost": round(total_compute_cost, 4),
                    "total_charges": total_charges,
                    "reservation_utilization_percentage": round(
                        reservation_utilization_percentage, 2
                    ),
                    "cost_with_reservations": round(cost_with_reservations, 4),
                    "cost_without_reservations": round(cost_without_reservations, 4),
                    "total_reservations": total_reservations,
                    "status_breakdown": status_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "billing_account_id": billing_account_id,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_capacity_reservations: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def identify_unused_capacity(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        billing_account_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Identify unused capacity reservations."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_unused_capacity_data(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                billing_account_id=billing_account_id,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_unused_reservations": 0,
                        "total_unused_cost": 0.0,
                        "total_charges": 0,
                        "unique_providers": 0,
                        "unique_accounts": 0,
                        "cost_impact": 0.0,
                        "provider_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "billing_account_id": billing_account_id,
                    },
                }

            # Calculate summary statistics
            total_unused_reservations = len(data)
            total_unused_cost = sum(item["total_effective_cost"] for item in data)
            total_charges = sum(item["charge_count"] for item in data)
            unique_providers = len({item["provider_name"] for item in data})
            unique_accounts = len({item["billing_account_id"] for item in data})

            # Provider breakdown
            provider_totals = {}
            for item in data:
                provider = item["provider_name"]
                if provider not in provider_totals:
                    provider_totals[provider] = {
                        "total_cost": 0.0,
                        "reservation_count": 0,
                        "charge_count": 0,
                        "unique_accounts": set(),
                    }
                provider_totals[provider]["total_cost"] += item["total_effective_cost"]
                provider_totals[provider]["reservation_count"] += 1
                provider_totals[provider]["charge_count"] += item["charge_count"]
                provider_totals[provider]["unique_accounts"].add(
                    item["billing_account_id"]
                )

            provider_breakdown = [
                {
                    "provider_name": provider,
                    "total_cost": round(stats["total_cost"], 4),
                    "reservation_count": stats["reservation_count"],
                    "charge_count": stats["charge_count"],
                    "unique_accounts": len(stats["unique_accounts"]),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_unused_cost * 100)
                        if total_unused_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for provider, stats in sorted(
                    provider_totals.items(),
                    key=lambda x: x[1]["total_cost"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_unused_reservations": total_unused_reservations,
                    "total_unused_cost": round(total_unused_cost, 4),
                    "total_charges": total_charges,
                    "unique_providers": unique_providers,
                    "unique_accounts": unique_accounts,
                    "cost_impact": round(
                        total_unused_cost, 4
                    ),  # Same as total cost for unused
                    "provider_breakdown": provider_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "billing_account_id": billing_account_id,
                },
            }

        except Exception as e:
            logger.error(f"Error in identify_unused_capacity: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_refunds_by_subaccount(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        billing_account_id: str | None = None,
        service_category: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Report refunds by subaccount within a billing period."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_refunds_data(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                billing_account_id=billing_account_id,
                service_category=service_category,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_refund_amount": 0.0,
                        "total_refund_count": 0,
                        "unique_subaccounts": 0,
                        "unique_service_categories": 0,
                        "unique_providers": 0,
                        "avg_refund_per_subaccount": 0.0,
                        "subaccount_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "billing_account_id": billing_account_id,
                        "service_category": service_category,
                    },
                }

            # Calculate summary statistics
            total_refund_amount = sum(item["total_billed_cost"] for item in data)
            total_refund_count = sum(item["refund_count"] for item in data)
            unique_subaccounts = len({item["sub_account_id"] for item in data})
            unique_service_categories = len({item["service_category"] for item in data})
            unique_providers = len({item["provider_name"] for item in data})
            avg_refund_per_subaccount = (
                total_refund_amount / unique_subaccounts
                if unique_subaccounts > 0
                else 0.0
            )

            # Subaccount breakdown
            subaccount_totals = {}
            for item in data:
                subaccount_key = f"{item['sub_account_id']}|{item['sub_account_name']}"
                if subaccount_key not in subaccount_totals:
                    subaccount_totals[subaccount_key] = {
                        "sub_account_id": item["sub_account_id"],
                        "sub_account_name": item["sub_account_name"],
                        "total_amount": 0.0,
                        "refund_count": 0,
                        "service_categories": set(),
                        "providers": set(),
                    }
                subaccount_totals[subaccount_key]["total_amount"] += item[
                    "total_billed_cost"
                ]
                subaccount_totals[subaccount_key]["refund_count"] += item[
                    "refund_count"
                ]
                subaccount_totals[subaccount_key]["service_categories"].add(
                    item["service_category"]
                )
                subaccount_totals[subaccount_key]["providers"].add(
                    item["provider_name"]
                )

            subaccount_breakdown = [
                {
                    "sub_account_id": stats["sub_account_id"],
                    "sub_account_name": stats["sub_account_name"],
                    "total_refund_amount": round(stats["total_amount"], 4),
                    "refund_count": stats["refund_count"],
                    "unique_service_categories": len(stats["service_categories"]),
                    "unique_providers": len(stats["providers"]),
                    "refund_percentage": round(
                        (stats["total_amount"] / total_refund_amount * 100)
                        if total_refund_amount > 0
                        else 0.0,
                        2,
                    ),
                }
                for stats in sorted(
                    subaccount_totals.values(),
                    key=lambda x: x["total_amount"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_refund_amount": round(total_refund_amount, 4),
                    "total_refund_count": total_refund_count,
                    "unique_subaccounts": unique_subaccounts,
                    "unique_service_categories": unique_service_categories,
                    "unique_providers": unique_providers,
                    "avg_refund_per_subaccount": round(avg_refund_per_subaccount, 4),
                    "subaccount_breakdown": subaccount_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "billing_account_id": billing_account_id,
                    "service_category": service_category,
                },
            }

        except Exception as e:
            logger.error(f"Error in get_refunds_by_subaccount: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_recurring_commitment_charges(
        self,
        start_date: datetime,
        end_date: datetime,
        commitment_discount_type: str | None = None,
        charge_frequency: str = "Recurring",
        **kwargs,
    ) -> dict[str, Any]:
        """Report recurring charges for commitment-based discounts over a period."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_commitment_charges(
                start_date=start_date,
                end_date=end_date,
                commitment_discount_type=commitment_discount_type,
                charge_frequency=charge_frequency,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_recurring_cost": 0.0,
                        "total_charge_count": 0,
                        "unique_commitments": 0,
                        "unique_commitment_types": 0,
                        "billing_periods": 0,
                        "avg_cost_per_period": 0.0,
                        "commitment_type_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "commitment_discount_type": commitment_discount_type,
                        "charge_frequency": charge_frequency,
                    },
                }

            # Calculate summary statistics
            total_recurring_cost = sum(item["total_billed_cost"] for item in data)
            total_charge_count = sum(item["charge_count"] for item in data)
            unique_commitments = len({item["commitment_discount_id"] for item in data})
            unique_commitment_types = len(
                {item["commitment_discount_type"] for item in data}
            )
            billing_periods = len({item["billing_period_start"] for item in data})
            avg_cost_per_period = (
                total_recurring_cost / billing_periods if billing_periods > 0 else 0.0
            )

            # Commitment type breakdown
            type_totals = {}
            for item in data:
                commitment_type = item["commitment_discount_type"]
                if commitment_type not in type_totals:
                    type_totals[commitment_type] = {
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "unique_commitments": set(),
                        "billing_periods": set(),
                    }
                type_totals[commitment_type]["total_cost"] += item["total_billed_cost"]
                type_totals[commitment_type]["charge_count"] += item["charge_count"]
                type_totals[commitment_type]["unique_commitments"].add(
                    item["commitment_discount_id"]
                )
                type_totals[commitment_type]["billing_periods"].add(
                    item["billing_period_start"]
                )

            commitment_type_breakdown = [
                {
                    "commitment_discount_type": commitment_type,
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "unique_commitments": len(stats["unique_commitments"]),
                    "billing_periods": len(stats["billing_periods"]),
                    "avg_cost_per_period": round(
                        stats["total_cost"] / len(stats["billing_periods"])
                        if len(stats["billing_periods"]) > 0
                        else 0.0,
                        4,
                    ),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_recurring_cost * 100)
                        if total_recurring_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for commitment_type, stats in sorted(
                    type_totals.items(), key=lambda x: x[1]["total_cost"], reverse=True
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_recurring_cost": round(total_recurring_cost, 4),
                    "total_charge_count": total_charge_count,
                    "unique_commitments": unique_commitments,
                    "unique_commitment_types": unique_commitment_types,
                    "billing_periods": billing_periods,
                    "avg_cost_per_period": round(avg_cost_per_period, 4),
                    "commitment_type_breakdown": commitment_type_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "commitment_discount_type": commitment_discount_type,
                    "charge_frequency": charge_frequency,
                },
            }

        except Exception as e:
            logger.error(f"Error in get_recurring_commitment_charges: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_service_costs(
        self,
        start_date: datetime,
        end_date: datetime,
        service_name: str,
        provider_name: str | None = None,
        sub_account_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze costs by service name."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_service_costs(
                start_date=start_date,
                end_date=end_date,
                service_name=service_name,
                provider_name=provider_name,
                sub_account_id=sub_account_id,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_service_cost": 0.0,
                        "total_charge_count": 0,
                        "unique_billing_periods": 0,
                        "unique_subaccounts": 0,
                        "unique_providers": 0,
                        "avg_cost_per_period": 0.0,
                        "cost_variance": 0.0,
                        "period_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "service_name": service_name,
                        "provider_name": provider_name,
                        "sub_account_id": sub_account_id,
                    },
                }

            # Calculate summary statistics
            total_service_cost = sum(item["total_effective_cost"] for item in data)
            total_charge_count = sum(item["charge_count"] for item in data)
            unique_billing_periods = len(
                {item["billing_period_start"] for item in data}
            )
            unique_subaccounts = len({item["sub_account_id"] for item in data})
            unique_providers = len({item["provider_name"] for item in data})
            avg_cost_per_period = (
                total_service_cost / unique_billing_periods
                if unique_billing_periods > 0
                else 0.0
            )

            # Calculate cost variance across periods
            period_costs = {}
            for item in data:
                period = item["billing_period_start"]
                if period not in period_costs:
                    period_costs[period] = 0.0
                period_costs[period] += item["total_effective_cost"]

            if len(period_costs) > 1:
                costs_list = list(period_costs.values())
                mean_cost = sum(costs_list) / len(costs_list)
                variance = sum((cost - mean_cost) ** 2 for cost in costs_list) / len(
                    costs_list
                )
                cost_variance = variance**0.5  # Standard deviation
            else:
                cost_variance = 0.0

            # Period breakdown
            period_breakdown = [
                {
                    "billing_period": period,
                    "total_cost": round(cost, 4),
                    "cost_percentage": round(
                        (cost / total_service_cost * 100)
                        if total_service_cost > 0
                        else 0.0,
                        2,
                    ),
                    "deviation_from_avg": round(cost - avg_cost_per_period, 4),
                }
                for period, cost in sorted(period_costs.items())
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_service_cost": round(total_service_cost, 4),
                    "total_charge_count": total_charge_count,
                    "unique_billing_periods": unique_billing_periods,
                    "unique_subaccounts": unique_subaccounts,
                    "unique_providers": unique_providers,
                    "avg_cost_per_period": round(avg_cost_per_period, 4),
                    "cost_variance": round(cost_variance, 4),
                    "period_breakdown": period_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "service_name": service_name,
                    "provider_name": provider_name,
                    "sub_account_id": sub_account_id,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_service_costs: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_spending_by_billing_period(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str,
        service_category: str | None = None,
        billing_account_id: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Report spending across billing periods for a provider by service category."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_spending_by_period(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                service_category=service_category,
                billing_account_id=billing_account_id,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_spending": 0.0,
                        "total_charge_count": 0,
                        "unique_billing_periods": 0,
                        "unique_service_categories": 0,
                        "unique_billing_accounts": 0,
                        "avg_spending_per_period": 0.0,
                        "period_breakdown": [],
                        "service_category_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "service_category": service_category,
                        "billing_account_id": billing_account_id,
                    },
                }

            # Calculate summary statistics
            total_spending = sum(item["total_billed_cost"] for item in data)
            total_charge_count = sum(item["charge_count"] for item in data)
            unique_billing_periods = len(
                {item["billing_period_start"] for item in data}
            )
            unique_service_categories = len({item["service_category"] for item in data})
            unique_billing_accounts = len({item["billing_account_id"] for item in data})
            avg_spending_per_period = (
                total_spending / unique_billing_periods
                if unique_billing_periods > 0
                else 0.0
            )

            # Period breakdown
            period_totals = {}
            for item in data:
                period = item["billing_period_start"]
                if period not in period_totals:
                    period_totals[period] = {
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "service_categories": set(),
                        "billing_accounts": set(),
                    }
                period_totals[period]["total_cost"] += item["total_billed_cost"]
                period_totals[period]["charge_count"] += item["charge_count"]
                period_totals[period]["service_categories"].add(
                    item["service_category"]
                )
                period_totals[period]["billing_accounts"].add(
                    item["billing_account_id"]
                )

            period_breakdown = [
                {
                    "billing_period": period,
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "unique_service_categories": len(stats["service_categories"]),
                    "unique_billing_accounts": len(stats["billing_accounts"]),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_spending * 100)
                        if total_spending > 0
                        else 0.0,
                        2,
                    ),
                }
                for period, stats in sorted(period_totals.items())
            ]

            # Service category breakdown
            category_totals = {}
            for item in data:
                category = item["service_category"]
                if category not in category_totals:
                    category_totals[category] = {
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "billing_periods": set(),
                        "services": set(),
                    }
                category_totals[category]["total_cost"] += item["total_billed_cost"]
                category_totals[category]["charge_count"] += item["charge_count"]
                category_totals[category]["billing_periods"].add(
                    item["billing_period_start"]
                )
                category_totals[category]["services"].add(item["service_name"])

            service_category_breakdown = [
                {
                    "service_category": category,
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "billing_periods": len(stats["billing_periods"]),
                    "unique_services": len(stats["services"]),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_spending * 100)
                        if total_spending > 0
                        else 0.0,
                        2,
                    ),
                }
                for category, stats in sorted(
                    category_totals.items(),
                    key=lambda x: x[1]["total_cost"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_spending": round(total_spending, 4),
                    "total_charge_count": total_charge_count,
                    "unique_billing_periods": unique_billing_periods,
                    "unique_service_categories": unique_service_categories,
                    "unique_billing_accounts": unique_billing_accounts,
                    "avg_spending_per_period": round(avg_spending_per_period, 4),
                    "period_breakdown": period_breakdown,
                    "service_category_breakdown": service_category_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "service_category": service_category,
                    "billing_account_id": billing_account_id,
                },
            }

        except Exception as e:
            logger.error(f"Error in get_spending_by_billing_period: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_service_costs_by_region(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        region_id: str | None = None,
        service_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze service costs by region."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_costs_by_region(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                region_id=region_id,
                service_name=service_name,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_cost": 0.0,
                        "total_charge_count": 0,
                        "unique_regions": 0,
                        "unique_services": 0,
                        "unique_providers": 0,
                        "charge_periods": 0,
                        "region_breakdown": [],
                        "service_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "region_id": region_id,
                        "service_name": service_name,
                    },
                }

            # Calculate summary statistics
            total_cost = sum(item["total_effective_cost"] for item in data)
            total_charge_count = sum(item["charge_count"] for item in data)
            unique_regions = len({item["region_id"] for item in data})
            unique_services = len({item["service_name"] for item in data})
            unique_providers = len({item["provider_name"] for item in data})
            charge_periods = len({item["charge_period_start"] for item in data})

            # Region breakdown
            region_totals = {}
            for item in data:
                region_key = f"{item['region_id']}|{item['region_name']}"
                if region_key not in region_totals:
                    region_totals[region_key] = {
                        "region_id": item["region_id"],
                        "region_name": item["region_name"],
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "services": set(),
                        "providers": set(),
                        "periods": set(),
                    }
                region_totals[region_key]["total_cost"] += item["total_effective_cost"]
                region_totals[region_key]["charge_count"] += item["charge_count"]
                region_totals[region_key]["services"].add(item["service_name"])
                region_totals[region_key]["providers"].add(item["provider_name"])
                region_totals[region_key]["periods"].add(item["charge_period_start"])

            region_breakdown = [
                {
                    "region_id": stats["region_id"],
                    "region_name": stats["region_name"],
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "unique_services": len(stats["services"]),
                    "unique_providers": len(stats["providers"]),
                    "charge_periods": len(stats["periods"]),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_cost * 100)
                        if total_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for stats in sorted(
                    region_totals.values(), key=lambda x: x["total_cost"], reverse=True
                )
            ]

            # Service breakdown
            service_totals = {}
            for item in data:
                service = item["service_name"]
                if service not in service_totals:
                    service_totals[service] = {
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "regions": set(),
                        "providers": set(),
                        "periods": set(),
                    }
                service_totals[service]["total_cost"] += item["total_effective_cost"]
                service_totals[service]["charge_count"] += item["charge_count"]
                service_totals[service]["regions"].add(item["region_id"])
                service_totals[service]["providers"].add(item["provider_name"])
                service_totals[service]["periods"].add(item["charge_period_start"])

            service_breakdown = [
                {
                    "service_name": service,
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "unique_regions": len(stats["regions"]),
                    "unique_providers": len(stats["providers"]),
                    "charge_periods": len(stats["periods"]),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_cost * 100)
                        if total_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for service, stats in sorted(
                    service_totals.items(),
                    key=lambda x: x[1]["total_cost"],
                    reverse=True,
                )
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_cost": round(total_cost, 4),
                    "total_charge_count": total_charge_count,
                    "unique_regions": unique_regions,
                    "unique_services": unique_services,
                    "unique_providers": unique_providers,
                    "charge_periods": charge_periods,
                    "region_breakdown": region_breakdown,
                    "service_breakdown": service_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "region_id": region_id,
                    "service_name": service_name,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_service_costs_by_region: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_service_costs_by_subaccount(
        self,
        start_date: datetime,
        end_date: datetime,
        sub_account_id: str,
        provider_name: str,
        service_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Report service costs by providers subaccount."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_costs_by_subaccount(
                start_date=start_date,
                end_date=end_date,
                sub_account_id=sub_account_id,
                provider_name=provider_name,
                service_name=service_name,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_subaccount_cost": 0.0,
                        "total_charge_count": 0,
                        "unique_services": 0,
                        "charge_periods": 0,
                        "avg_cost_per_period": 0.0,
                        "cost_variance": 0.0,
                        "service_breakdown": [],
                        "period_breakdown": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "sub_account_id": sub_account_id,
                        "provider_name": provider_name,
                        "service_name": service_name,
                    },
                }

            # Calculate summary statistics
            total_subaccount_cost = sum(item["total_effective_cost"] for item in data)
            total_charge_count = sum(item["charge_count"] for item in data)
            unique_services = len({item["service_name"] for item in data})
            charge_periods = len({item["charge_period_start"] for item in data})
            avg_cost_per_period = (
                total_subaccount_cost / charge_periods if charge_periods > 0 else 0.0
            )

            # Calculate cost variance across periods
            period_costs = {}
            for item in data:
                period = item["charge_period_start"]
                if period not in period_costs:
                    period_costs[period] = 0.0
                period_costs[period] += item["total_effective_cost"]

            if len(period_costs) > 1:
                costs_list = list(period_costs.values())
                mean_cost = sum(costs_list) / len(costs_list)
                variance = sum((cost - mean_cost) ** 2 for cost in costs_list) / len(
                    costs_list
                )
                cost_variance = variance**0.5  # Standard deviation
            else:
                cost_variance = 0.0

            # Service breakdown
            service_totals = {}
            for item in data:
                service = item["service_name"]
                if service not in service_totals:
                    service_totals[service] = {
                        "total_cost": 0.0,
                        "charge_count": 0,
                        "periods": set(),
                    }
                service_totals[service]["total_cost"] += item["total_effective_cost"]
                service_totals[service]["charge_count"] += item["charge_count"]
                service_totals[service]["periods"].add(item["charge_period_start"])

            service_breakdown = [
                {
                    "service_name": service,
                    "total_cost": round(stats["total_cost"], 4),
                    "charge_count": stats["charge_count"],
                    "charge_periods": len(stats["periods"]),
                    "avg_cost_per_period": round(
                        stats["total_cost"] / len(stats["periods"])
                        if len(stats["periods"]) > 0
                        else 0.0,
                        4,
                    ),
                    "cost_percentage": round(
                        (stats["total_cost"] / total_subaccount_cost * 100)
                        if total_subaccount_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for service, stats in sorted(
                    service_totals.items(),
                    key=lambda x: x[1]["total_cost"],
                    reverse=True,
                )
            ]

            # Period breakdown
            period_breakdown = [
                {
                    "charge_period": period,
                    "total_cost": round(cost, 4),
                    "cost_percentage": round(
                        (cost / total_subaccount_cost * 100)
                        if total_subaccount_cost > 0
                        else 0.0,
                        2,
                    ),
                    "deviation_from_avg": round(cost - avg_cost_per_period, 4),
                }
                for period, cost in sorted(period_costs.items(), reverse=True)
            ]

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_subaccount_cost": round(total_subaccount_cost, 4),
                    "total_charge_count": total_charge_count,
                    "unique_services": unique_services,
                    "charge_periods": charge_periods,
                    "avg_cost_per_period": round(avg_cost_per_period, 4),
                    "cost_variance": round(cost_variance, 4),
                    "service_breakdown": service_breakdown,
                    "period_breakdown": period_breakdown,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "sub_account_id": sub_account_id,
                    "provider_name": provider_name,
                    "service_name": service_name,
                },
            }

        except Exception as e:
            logger.error(f"Error in get_service_costs_by_subaccount: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def analyze_service_cost_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        provider_name: str | None = None,
        service_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Analyze service costs month over month."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_service_cost_trend_data(
                start_date=start_date,
                end_date=end_date,
                provider_name=provider_name,
                service_name=service_name,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_cost": 0.0,
                        "total_charge_count": 0,
                        "unique_months": 0,
                        "unique_services": 0,
                        "unique_providers": 0,
                        "avg_monthly_cost": 0.0,
                        "cost_growth_rate": 0.0,
                        "monthly_breakdown": [],
                        "service_trends": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "provider_name": provider_name,
                        "service_name": service_name,
                    },
                }

            # Calculate summary statistics
            total_cost = sum(item["total_effective_cost"] for item in data)
            total_charge_count = sum(item["charge_count"] for item in data)
            unique_months = len({item["month_name"] for item in data})
            unique_services = len({item["service_name"] for item in data})
            unique_providers = len({item["provider_name"] for item in data})
            avg_monthly_cost = total_cost / unique_months if unique_months > 0 else 0.0

            # Calculate month-over-month growth rate
            monthly_totals = {}
            for item in data:
                month = item["month_name"]
                if month not in monthly_totals:
                    monthly_totals[month] = 0.0
                monthly_totals[month] += item["total_effective_cost"]

            sorted_months = sorted(monthly_totals.items())
            cost_growth_rate = 0.0
            if len(sorted_months) > 1:
                first_month_cost = sorted_months[0][1]
                last_month_cost = sorted_months[-1][1]
                if first_month_cost > 0:
                    cost_growth_rate = (
                        (last_month_cost - first_month_cost) / first_month_cost
                    ) * 100

            # Monthly breakdown
            monthly_breakdown = [
                {
                    "month": month,
                    "total_cost": round(cost, 4),
                    "cost_percentage": round(
                        (cost / total_cost * 100) if total_cost > 0 else 0.0, 2
                    ),
                }
                for month, cost in sorted_months
            ]

            # Service trends
            service_monthly_data = {}
            for item in data:
                service = item["service_name"]
                month = item["month_name"]
                if service not in service_monthly_data:
                    service_monthly_data[service] = {}
                service_monthly_data[service][month] = item["total_effective_cost"]

            service_trends = []
            for service, monthly_data in service_monthly_data.items():
                sorted_service_months = sorted(monthly_data.items())
                service_total = sum(monthly_data.values())

                # Calculate growth rate for this service
                service_growth_rate = 0.0
                if len(sorted_service_months) > 1:
                    first_cost = sorted_service_months[0][1]
                    last_cost = sorted_service_months[-1][1]
                    if first_cost > 0:
                        service_growth_rate = (
                            (last_cost - first_cost) / first_cost
                        ) * 100

                service_trends.append(
                    {
                        "service_name": service,
                        "total_cost": round(service_total, 4),
                        "months_active": len(monthly_data),
                        "avg_monthly_cost": round(
                            service_total / len(monthly_data)
                            if len(monthly_data) > 0
                            else 0.0,
                            4,
                        ),
                        "growth_rate_percentage": round(service_growth_rate, 2),
                        "cost_percentage": round(
                            (service_total / total_cost * 100)
                            if total_cost > 0
                            else 0.0,
                            2,
                        ),
                    }
                )

            # Sort by total cost
            service_trends.sort(key=lambda x: x["total_cost"], reverse=True)

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_cost": round(total_cost, 4),
                    "total_charge_count": total_charge_count,
                    "unique_months": unique_months,
                    "unique_services": unique_services,
                    "unique_providers": unique_providers,
                    "avg_monthly_cost": round(avg_monthly_cost, 4),
                    "cost_growth_rate": round(cost_growth_rate, 2),
                    "monthly_breakdown": monthly_breakdown,
                    "service_trends": service_trends,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "provider_name": provider_name,
                    "service_name": service_name,
                },
            }

        except Exception as e:
            logger.error(f"Error in analyze_service_cost_trends: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_application_cost_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        application_tag: str,
        service_name: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Report application cost month over month."""
        try:
            # Get raw data from repository
            data = self.analytics_repo.get_application_cost_trend_data(
                start_date=start_date,
                end_date=end_date,
                application_tag=application_tag,
                service_name=service_name,
                **kwargs,
            )

            if not data:
                return {
                    "status": "success",
                    "data": [],
                    "summary": {
                        "total_application_cost": 0.0,
                        "total_charge_count": 0,
                        "unique_months": 0,
                        "unique_services": 0,
                        "avg_monthly_cost": 0.0,
                        "cost_growth_rate": 0.0,
                        "monthly_breakdown": [],
                        "service_trends": [],
                    },
                    "filters": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "application_tag": application_tag,
                        "service_name": service_name,
                    },
                }

            # Calculate summary statistics
            total_application_cost = sum(item["total_effective_cost"] for item in data)
            total_charge_count = sum(item["charge_count"] for item in data)
            unique_months = len({item["month_name"] for item in data})
            unique_services = len({item["service_name"] for item in data})
            avg_monthly_cost = (
                total_application_cost / unique_months if unique_months > 0 else 0.0
            )

            # Calculate month-over-month growth rate
            monthly_totals = {}
            for item in data:
                month = item["month_name"]
                if month not in monthly_totals:
                    monthly_totals[month] = 0.0
                monthly_totals[month] += item["total_effective_cost"]

            sorted_months = sorted(monthly_totals.items())
            cost_growth_rate = 0.0
            if len(sorted_months) > 1:
                first_month_cost = sorted_months[0][1]
                last_month_cost = sorted_months[-1][1]
                if first_month_cost > 0:
                    cost_growth_rate = (
                        (last_month_cost - first_month_cost) / first_month_cost
                    ) * 100

            # Monthly breakdown
            monthly_breakdown = [
                {
                    "month": month,
                    "total_cost": round(cost, 4),
                    "cost_percentage": round(
                        (cost / total_application_cost * 100)
                        if total_application_cost > 0
                        else 0.0,
                        2,
                    ),
                }
                for month, cost in sorted_months
            ]

            # Service trends for this application
            service_monthly_data = {}
            for item in data:
                service = item["service_name"]
                month = item["month_name"]
                if service not in service_monthly_data:
                    service_monthly_data[service] = {}
                service_monthly_data[service][month] = item["total_effective_cost"]

            service_trends = []
            for service, monthly_data in service_monthly_data.items():
                sorted_service_months = sorted(monthly_data.items())
                service_total = sum(monthly_data.values())

                # Calculate growth rate for this service
                service_growth_rate = 0.0
                if len(sorted_service_months) > 1:
                    first_cost = sorted_service_months[0][1]
                    last_cost = sorted_service_months[-1][1]
                    if first_cost > 0:
                        service_growth_rate = (
                            (last_cost - first_cost) / first_cost
                        ) * 100

                service_trends.append(
                    {
                        "service_name": service,
                        "total_cost": round(service_total, 4),
                        "months_active": len(monthly_data),
                        "avg_monthly_cost": round(
                            service_total / len(monthly_data)
                            if len(monthly_data) > 0
                            else 0.0,
                            4,
                        ),
                        "growth_rate_percentage": round(service_growth_rate, 2),
                        "cost_percentage": round(
                            (service_total / total_application_cost * 100)
                            if total_application_cost > 0
                            else 0.0,
                            2,
                        ),
                    }
                )

            # Sort by total cost
            service_trends.sort(key=lambda x: x["total_cost"], reverse=True)

            return {
                "status": "success",
                "data": data,
                "summary": {
                    "total_application_cost": round(total_application_cost, 4),
                    "total_charge_count": total_charge_count,
                    "unique_months": unique_months,
                    "unique_services": unique_services,
                    "avg_monthly_cost": round(avg_monthly_cost, 4),
                    "cost_growth_rate": round(cost_growth_rate, 2),
                    "monthly_breakdown": monthly_breakdown,
                    "service_trends": service_trends,
                },
                "filters": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "application_tag": application_tag,
                    "service_name": service_name,
                },
            }

        except Exception as e:
            logger.error(f"Error in get_application_cost_trends: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_connected_provider_names(self) -> dict[str, Any]:
        """Get distinct provider names from billing data for connected providers only."""
        try:
            # Get provider names from repository
            provider_names = self.analytics_repo.get_distinct_provider_names()

            return {
                "status": "success",
                "data": provider_names,
                "summary": {
                    "total_connected_providers": len(provider_names),
                    "provider_list": sorted(provider_names),
                },
            }

        except Exception as e:
            logger.error(f"Error in get_connected_provider_names: {e}")
            return {"status": "error", "message": str(e), "data": []}

    def get_available_service_names(self) -> dict[str, Any]:
        """Get distinct service names with provider and category info from billing data."""
        try:
            # Get service names from repository
            services_data = self.analytics_repo.get_distinct_service_names()

            return {
                "status": "success",
                "data": services_data,
                "summary": {
                    "total_available_services": len(services_data),
                },
            }

        except Exception as e:
            logger.error(f"Error in get_available_service_names: {e}")
            return {"status": "error", "message": str(e), "data": []}
