"""
Manual API Testing Script for NarevAI Backend
Runs curl commands to test all main endpoints and validates responses.
"""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any


class APITester:
    """Simple API tester using curl commands."""

    def __init__(self, base_url: str = "http://localhost:8000", verbose: bool = True):
        self.base_url = base_url
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.results: list[dict[str, Any]] = []

    def curl_request(
        self, endpoint: str, method: str = "GET", data: dict | None = None
    ) -> dict[str, Any]:
        """Execute curl request and return parsed response."""
        url = f"{self.base_url}{endpoint}"

        cmd = ["curl", "-s", "-X", method, url, "-H", "accept: application/json"]

        if data and method != "GET":
            cmd.extend(["-H", "Content-Type: application/json", "-d", json.dumps(data)])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                return {"error": f"Curl failed: {result.stderr}"}

            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON response: {result.stdout}"}

        except subprocess.TimeoutExpired:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": f"Request failed: {str(e)}"}

    def _format_response_summary(self, response: Any) -> str:
        """Format a concise summary of the API response."""
        try:
            if isinstance(response, dict):
                if "status" in response:
                    return f"Status: {response['status']}"
                elif "total" in response:
                    return f"Total items: {response['total']}"
                elif "id" in response:
                    return f"ID: {response['id']}"
                elif "runs" in response:
                    runs = response["runs"]
                    if isinstance(runs, list):
                        return f"Runs count: {len(runs)}"
                elif "data" in response:
                    data = response["data"]
                    if isinstance(data, list):
                        return f"Data records: {len(data)}"
                elif "services" in response:
                    services = response["services"]
                    if isinstance(services, list):
                        return f"Services count: {len(services)}"
                else:
                    return f"Response size: {len(str(response))} chars"
            elif isinstance(response, list):
                return f"Array with {len(response)} items"
            else:
                response_str = str(response)
                if len(response_str) > 100:
                    return f"Response: {response_str[:100]}..."
                return f"Response: {response_str}"
        except Exception:
            return f"Response size: {len(str(response))} chars"

    def test_endpoint(
        self,
        name: str,
        endpoint: str,
        method: str = "GET",
        data: dict | None = None,
        expected_keys: list[str] | None = None,
        should_be_list: bool = False,
        expect_error: bool = False,
    ) -> bool:
        """Test single endpoint and validate response."""
        if self.verbose:
            print(f"Testing {name}...")

        response = self.curl_request(endpoint, method, data)

        # Check for curl/network errors
        if "error" in response:
            if self.verbose:
                print(f"❌ {name}: {response['error']}")
            self.failed += 1
            self.results.append(
                {"name": name, "status": "FAILED", "error": response["error"]}
            )
            self.print_progress()
            return False

        # Check for API errors
        if "detail" in response and isinstance(response["detail"], str):
            if expect_error:
                # This is an expected error (like 404 for non-existent resources)
                if self.verbose:
                    print(f"✅ {name}: Expected error - {response['detail']}")
                self.passed += 1
                self.results.append(
                    {
                        "name": name,
                        "status": "PASSED",
                        "response_size": len(str(response)),
                    }
                )
                self.print_progress()
                return True
            else:
                if self.verbose:
                    print(f"❌ {name}: API Error - {response['detail']}")
                self.failed += 1
                self.results.append(
                    {"name": name, "status": "FAILED", "error": response["detail"]}
                )
                self.print_progress()
                return False

        # Validate response structure
        if should_be_list and not isinstance(response, list):
            if self.verbose:
                print(f"❌ {name}: Expected list, got {type(response)}")
            self.failed += 1
            self.results.append(
                {"name": name, "status": "FAILED", "error": "Expected list response"}
            )
            self.print_progress()
            return False

        if expected_keys and not should_be_list:
            missing_keys = [key for key in expected_keys if key not in response]
            if missing_keys:
                if self.verbose:
                    print(f"❌ {name}: Missing keys: {missing_keys}")
                self.failed += 1
                self.results.append(
                    {
                        "name": name,
                        "status": "FAILED",
                        "error": f"Missing keys: {missing_keys}",
                    }
                )
                self.print_progress()
                return False

        if self.verbose:
            print(f"✅ {name}: OK")
            # Show formatted summary of response
            summary = self._format_response_summary(response)
            if summary:
                print(f"  → {summary}")
        self.passed += 1
        self.results.append(
            {"name": name, "status": "PASSED", "response_size": len(str(response))}
        )
        self.print_progress()
        return True

    def run_all_tests(self):
        """Run all API tests."""
        if self.verbose:
            print("🚀 Starting API Tests...\n")

        # Health check
        self.test_endpoint(
            "Health Check",
            "/health",
            expected_keys=["status", "environment", "version"],
        )

        # Providers
        self.test_endpoint(
            "Get All Providers", "/api/v1/providers", should_be_list=True
        )

        self.test_endpoint(
            "Get Providers with Inactive",
            "/api/v1/providers?include_inactive=true",
            should_be_list=True,
        )

        self.test_endpoint(
            "Provider Types Info",
            "/api/v1/providers/types/info",
            expected_keys=["providers", "total_providers"],
        )

        self.test_endpoint(
            "Provider Auth Fields (OpenAI)",
            "/api/v1/providers/types/openai/auth-fields",
            expected_keys=["provider_type", "auth_fields"],
        )

        self.test_endpoint(
            "Provider Health Check",
            "/api/v1/providers/health",
            expected_keys=["status", "service", "timestamp"],
        )

        # We'll get first provider ID from the list for detailed tests
        providers_response = self.curl_request("/api/v1/providers")
        provider_id = None
        run_id = None

        if isinstance(providers_response, list) and len(providers_response) > 0:
            provider_id = providers_response[0].get("id")

            if provider_id:
                self.test_endpoint(
                    "Get Specific Provider",
                    f"/api/v1/providers/{provider_id}",
                    expected_keys=["id", "name", "provider_type", "is_active"],
                )

        # Sync endpoints
        self.test_endpoint(
            "Sync Status", "/api/v1/syncs/status", expected_keys=["runs", "summary"]
        )

        self.test_endpoint(
            "Sync Runs", "/api/v1/syncs/runs", expected_keys=["runs", "pagination"]
        )

        self.test_endpoint(
            "Sync Runs with Pagination",
            "/api/v1/syncs/runs?skip=0&limit=5",
            expected_keys=["runs", "pagination"],
        )

        # Get a run ID for detailed tests
        runs_response = self.curl_request("/api/v1/syncs/runs?limit=1")
        if (
            isinstance(runs_response, dict)
            and "runs" in runs_response
            and len(runs_response["runs"]) > 0
        ):
            run_id = runs_response["runs"][0].get("id")
            if run_id:
                self.test_endpoint(
                    "Get Specific Sync Run",
                    f"/api/v1/syncs/runs/{run_id}",
                    expected_keys=["id", "provider_id", "status"],
                )

        self.test_endpoint(
            "Sync Health Check",
            "/api/v1/syncs/health",
            expected_keys=["status", "service", "timestamp"],
        )

        self.test_endpoint(
            "Sync Statistics",
            "/api/v1/syncs/stats",
            expected_keys=["period_days", "total_runs", "success_rate"],
        )

        if provider_id:
            self.test_endpoint(
                "Sync Statistics by Provider",
                f"/api/v1/syncs/stats?provider_id={provider_id}",
                expected_keys=["period_days", "total_runs", "success_rate"],
            )

        # Skip pipeline graph test - it returns binary PNG data
        # self.test_endpoint(
        #     "Pipeline Graph",
        #     "/api/v1/syncs/pipeline/graph?format=png"
        # )

        # Analytics endpoints
        self.test_endpoint(
            "Analytics Use Cases",
            "/api/v1/analytics/",
            expected_keys=["use_cases", "total", "filters"],
        )

        import urllib.parse

        persona_encoded = urllib.parse.quote("FinOps Practitioner")
        self.test_endpoint(
            "Analytics Use Cases with Persona Filter",
            f"/api/v1/analytics/?persona={persona_encoded}",
            expected_keys=["use_cases", "total", "filters"],
        )

        self.test_endpoint(
            "Analytics Health Check",
            "/api/v1/analytics/health",
            expected_keys=["status", "service", "timestamp"],
        )

        # Analytics with date parameters
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()

        analytics_endpoints = [
            ("Resource Rate Analytics", "/api/v1/analytics/resource-rate"),
            ("Resource Usage Analytics", "/api/v1/analytics/resource-usage"),
            ("Unit Economics Analytics", "/api/v1/analytics/unit-economics"),
            ("Virtual Currency Target", "/api/v1/analytics/virtual-currency-target"),
            (
                "Effective Cost by Currency",
                "/api/v1/analytics/effective-cost-by-currency",
            ),
            (
                "Virtual Currency Purchases",
                "/api/v1/analytics/virtual-currency-purchases",
            ),
            ("Contracted Savings", "/api/v1/analytics/contracted-savings"),
            ("Tag Coverage", "/api/v1/analytics/tag-coverage"),
            ("SKU Metered Costs", "/api/v1/analytics/sku-metered-costs"),
            (
                "Service Category Breakdown",
                "/api/v1/analytics/service-category-breakdown",
            ),
            (
                "Capacity Reservation Analysis",
                "/api/v1/analytics/capacity-reservation-analysis",
            ),
            ("Unused Capacity", "/api/v1/analytics/unused-capacity"),
            ("Refunds by Subaccount", "/api/v1/analytics/refunds-by-subaccount"),
            (
                "Recurring Commitment Charges",
                "/api/v1/analytics/recurring-commitment-charges",
            ),
            (
                "Service Cost Analysis",
                "/api/v1/analytics/service-cost-analysis&service_name=GPT-4",
            ),
            (
                "Spending by Billing Period",
                "/api/v1/analytics/spending-by-billing-period&provider_name=OpenAI",
            ),
            ("Service Costs by Region", "/api/v1/analytics/service-costs-by-region"),
            (
                "Service Costs by Subaccount",
                "/api/v1/analytics/service-costs-by-subaccount&provider_name=OpenAI&sub_account_id=test-account-123",
            ),
            ("Service Cost Trends", "/api/v1/analytics/service-cost-trends"),
            (
                "Application Cost Trends",
                "/api/v1/analytics/application-cost-trends&application_tag=web-app",
            ),
        ]

        for name, endpoint in analytics_endpoints:
            # Handle special cases for endpoints with required parameters
            if "&" in endpoint:
                # Extract the base endpoint and parameters
                clean_endpoint = endpoint.split("&")[0]
                params = "&".join(endpoint.split("&")[1:])
                test_url = f"{clean_endpoint}?start_date={start_date}&end_date={end_date}&{params}"
            else:
                test_url = f"{endpoint}?start_date={start_date}&end_date={end_date}"

            # Most analytics endpoints return different response structures
            # Don't enforce specific keys as they vary per endpoint
            self.test_endpoint(name, test_url)

        # Billing endpoints
        self.test_endpoint(
            "Billing Summary",
            "/api/v1/billing/summary",
            expected_keys=[
                "total_cost",
                "total_records",
                "start_date",
                "end_date",
                "currency",
            ],
        )

        self.test_endpoint(
            "Billing Data",
            "/api/v1/billing/data?limit=10",
            expected_keys=["data", "pagination"],
        )

        import urllib.parse

        service_category_encoded = urllib.parse.quote("AI and Machine Learning")
        self.test_endpoint(
            "Billing Data with Filters",
            f"/api/v1/billing/data?limit=5&service_category={service_category_encoded}",
            expected_keys=["data", "pagination"],
        )

        self.test_endpoint(
            "Cost by Service", "/api/v1/billing/services", expected_keys=["services"]
        )

        self.test_endpoint(
            "Cost Trends", "/api/v1/billing/trends", expected_keys=["trends"]
        )

        self.test_endpoint(
            "Billing Statistics",
            "/api/v1/billing/statistics",
            expected_keys=["total_records", "total_cost"],
        )

        self.test_endpoint(
            "Billing Health Check",
            "/api/v1/billing/health",
            expected_keys=["status", "service", "timestamp"],
        )

        # Export endpoints - skip CSV test as it returns CSV data, not JSON
        # self.test_endpoint(
        #     "Export Billing Data CSV",
        #     "/api/v1/export/billing?format=csv&limit=100"
        # )

        self.test_endpoint(
            "Export Health Check",
            "/api/v1/export/health",
            expected_keys=["status", "service", "timestamp"],
        )

        # Test error handling
        if self.verbose:
            print("\n🔍 Testing error handling...")
        self.test_endpoint(
            "Non-existent Endpoint", "/api/v1/nonexistent", expect_error=True
        )

        if provider_id:
            self.test_endpoint(
                "Non-existent Provider",
                "/api/v1/providers/00000000-0000-0000-0000-000000000000",
                expect_error=True,
            )

        if run_id:
            self.test_endpoint(
                "Non-existent Sync Run",
                "/api/v1/syncs/runs/00000000-0000-0000-0000-000000000000",
                expect_error=True,
            )

    def print_progress(self):
        """Print progress bar in quiet mode."""
        if not self.verbose:
            total = self.passed + self.failed
            if total > 0 and total % 5 == 0:  # Update every 5 tests
                print(
                    f"Progress: {total} tests completed ({self.passed} ✅, {self.failed} ❌)"
                )

    def print_summary(self):
        """Print test results summary."""
        print(f"\n{'=' * 50}")
        print("📊 TEST RESULTS SUMMARY")
        print(f"{'=' * 50}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        total = self.passed + self.failed
        if total > 0:
            print(f"📈 Success Rate: {(self.passed / total * 100):.1f}%")

        if self.failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAILED":
                    print(
                        f"  - {result['name']}: {result.get('error', 'Unknown error')}"
                    )

        print("\n🎯 All tests completed!")

        # Exit with error code if any tests failed
        sys.exit(1 if self.failed > 0 else 0)


def main():
    """Main function."""
    import argparse

    parser = argparse.ArgumentParser(description="Test NarevAI API endpoints")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base API URL (default: http://localhost:8000)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode - only show progress and summary",
    )

    args = parser.parse_args()

    # Handle quiet vs verbose flags
    verbose = args.verbose and not args.quiet

    print("🧪 NarevAI API Test Suite")
    print(f"🌐 Testing API at: {args.url}")
    if verbose or not args.quiet:
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    tester = APITester(args.url, verbose=verbose)

    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        sys.exit(1)
    finally:
        tester.print_summary()


if __name__ == "__main__":
    main()
