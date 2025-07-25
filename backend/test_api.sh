#!/bin/bash

# NarevAI API Test Script
# Simple bash script to test all main endpoints with curl

set -e  # Exit on any error

# Configuration
BASE_URL="${1:-http://localhost:8000}"
VERBOSE="${VERBOSE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Helper functions
print_header() {
    echo -e "${BLUE}🧪 NarevAI API Test Suite${NC}"
    echo -e "${BLUE}🌐 Testing API at: $BASE_URL${NC}"
    echo -e "${BLUE}📅 Started at: $(date)${NC}"
    echo ""
}

print_test() {
    echo -e "${YELLOW}Testing $1...${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1: OK${NC}"
    PASSED=$((PASSED + 1))
}

print_failure() {
    echo -e "${RED}❌ $1: $2${NC}"
    FAILED=$((FAILED + 1))
}

format_response_summary() {
    local response="$1"
    
    # Try to extract meaningful summary using jq
    local summary=$(echo "$response" | jq -r '
        if type == "object" then
            if has("status") then "Status: \(.status)"
            elif has("total") then "Total items: \(.total)"
            elif has("id") then "ID: \(.id)"
            elif has("runs") then "Runs count: \(.runs | length)"
            elif has("data") then "Data records: \(.data | length)"
            elif has("services") then "Services count: \(.services | length)"
            elif has("total_cost") then "Total cost: \(.total_cost)"
            else "Response size: \(. | tostring | length) chars"
            end
        elif type == "array" then "Array with \(length) items"
        else "Response: \(. | tostring | .[0:100])..."
        end
    ' 2>/dev/null || echo "Response size: $(echo "$response" | wc -c) chars")
    
    echo "$summary"
}

test_endpoint() {
    local name="$1"
    local endpoint="$2"
    local method="${3:-GET}"
    local data="$4"
    local expect_error="${5:-false}"
    
    print_test "$name"
    
    # Build curl command
    local curl_cmd="curl -s -w '%{http_code}' -X $method '$BASE_URL$endpoint' -H 'accept: application/json'"
    
    if [ ! -z "$data" ] && [ "$method" != "GET" ]; then
        curl_cmd="$curl_cmd -H 'Content-Type: application/json' -d '$data'"
    fi
    
    # Execute curl and capture response + status code
    local response
    response=$(eval $curl_cmd 2>/dev/null || echo "000CURL_ERROR")
    
    # Extract HTTP status code (last 3 characters)
    local status_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$response" = "000CURL_ERROR" ]; then
        print_failure "$name" "Curl command failed"
        return 1
    fi
    
    # Check HTTP status code
    if [[ "$status_code" =~ ^[45][0-9][0-9]$ ]]; then
        if [ "$expect_error" = "true" ]; then
            print_success "$name"
            [ "$VERBOSE" = "true" ] && echo "  → Expected error: HTTP $status_code"
            return 0
        else
            print_failure "$name" "HTTP $status_code - $body"
            return 1
        fi
    fi
    
    # Validate JSON response
    if ! echo "$body" | jq . >/dev/null 2>&1; then
        print_failure "$name" "Invalid JSON response"
        [ "$VERBOSE" = "true" ] && echo "Response: $body"
        return 1
    fi
    
    print_success "$name"
    
    # Show response summary if verbose
    if [ "$VERBOSE" = "true" ]; then
        local summary=$(format_response_summary "$body")
        echo "  → $summary"
    fi
    
    return 0
}

# Check prerequisites
check_dependencies() {
    if ! command -v curl >/dev/null 2>&1; then
        echo -e "${RED}❌ curl is required but not installed${NC}"
        exit 1
    fi
    
    if ! command -v jq >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ jq not found - JSON validation will be limited${NC}"
    fi
}

# Main test function
run_tests() {
    print_header
    
    echo "🚀 Starting API Tests..."
    echo ""
    
    # Basic health check
    test_endpoint "Health Check" "/health"
    
    # Providers
    test_endpoint "Get All Providers" "/api/v1/providers"
    test_endpoint "Get Providers with Inactive" "/api/v1/providers?include_inactive=true"
    test_endpoint "Provider Types Info" "/api/v1/providers/types/info"
    test_endpoint "Provider Auth Fields (OpenAI)" "/api/v1/providers/types/openai/auth-fields"
    test_endpoint "Provider Health Check" "/api/v1/providers/health"
    
    # Get first provider ID for detailed tests
    local providers_response
    providers_response=$(curl -s "$BASE_URL/api/v1/providers" -H "accept: application/json" 2>/dev/null || echo "[]")
    local provider_id
    provider_id=$(echo "$providers_response" | jq -r '.[0].id // empty' 2>/dev/null || echo "")
    
    if [ ! -z "$provider_id" ] && [ "$provider_id" != "null" ]; then
        test_endpoint "Get Specific Provider" "/api/v1/providers/$provider_id"
    fi
    
    # Sync endpoints
    test_endpoint "Sync Status" "/api/v1/syncs/status"
    test_endpoint "Sync Runs" "/api/v1/syncs/runs"
    test_endpoint "Sync Runs with Pagination" "/api/v1/syncs/runs?skip=0&limit=5"
    
    # Get first run ID for detailed tests
    local runs_response
    runs_response=$(curl -s "$BASE_URL/api/v1/syncs/runs?limit=1" -H "accept: application/json" 2>/dev/null || echo "{}")
    local run_id
    run_id=$(echo "$runs_response" | jq -r '.runs[0].id // empty' 2>/dev/null || echo "")
    
    if [ ! -z "$run_id" ] && [ "$run_id" != "null" ]; then
        test_endpoint "Get Specific Sync Run" "/api/v1/syncs/runs/$run_id"
    fi
    
    test_endpoint "Sync Health Check" "/api/v1/syncs/health"
    test_endpoint "Sync Statistics" "/api/v1/syncs/stats"
    
    if [ ! -z "$provider_id" ] && [ "$provider_id" != "null" ]; then
        test_endpoint "Sync Statistics by Provider" "/api/v1/syncs/stats?provider_id=$provider_id"
    fi
    
    # Skip pipeline graph test - it returns binary PNG data
    # test_endpoint "Pipeline Graph" "/api/v1/syncs/pipeline/graph?format=png"
    
    # Analytics endpoints
    test_endpoint "Analytics Use Cases" "/api/v1/analytics/"
    
    # URL encode the persona parameter
    local persona_encoded=$(printf %s "FinOps Practitioner" | jq -sRr @uri)
    test_endpoint "Analytics Use Cases with Persona Filter" "/api/v1/analytics/?persona=$persona_encoded"
    test_endpoint "Analytics Health Check" "/api/v1/analytics/health"
    
    # Analytics with date parameters
    local start_date end_date
    start_date=$(date -u -d '30 days ago' +%Y-%m-%dT%H:%M:%S 2>/dev/null || date -u -v-30d +%Y-%m-%dT%H:%M:%S 2>/dev/null || echo "2025-06-22T00:00:00")
    end_date=$(date -u +%Y-%m-%dT%H:%M:%S)
    
    # All analytics endpoints - don't check specific keys as they vary
    declare -a analytics_endpoints=(
        "Resource Rate Analytics:/api/v1/analytics/resource-rate"
        "Resource Usage Analytics:/api/v1/analytics/resource-usage"
        "Unit Economics Analytics:/api/v1/analytics/unit-economics"
        "Virtual Currency Target:/api/v1/analytics/virtual-currency-target"
        "Effective Cost by Currency:/api/v1/analytics/effective-cost-by-currency"
        "Virtual Currency Purchases:/api/v1/analytics/virtual-currency-purchases"
        "Contracted Savings:/api/v1/analytics/contracted-savings"
        "Tag Coverage:/api/v1/analytics/tag-coverage"
        "SKU Metered Costs:/api/v1/analytics/sku-metered-costs"
        "Service Category Breakdown:/api/v1/analytics/service-category-breakdown"
        "Capacity Reservation Analysis:/api/v1/analytics/capacity-reservation-analysis"
        "Unused Capacity:/api/v1/analytics/unused-capacity"
        "Refunds by Subaccount:/api/v1/analytics/refunds-by-subaccount"
        "Recurring Commitment Charges:/api/v1/analytics/recurring-commitment-charges"
        "Service Cost Analysis:/api/v1/analytics/service-cost-analysis&service_name=GPT-4"
        "Spending by Billing Period:/api/v1/analytics/spending-by-billing-period&provider_name=OpenAI"
        "Service Costs by Region:/api/v1/analytics/service-costs-by-region"
        "Service Costs by Subaccount:/api/v1/analytics/service-costs-by-subaccount&provider_name=OpenAI&sub_account_id=test-account-123"
        "Service Cost Trends:/api/v1/analytics/service-cost-trends"
        "Application Cost Trends:/api/v1/analytics/application-cost-trends&application_tag=web-app"
    )
    
    for endpoint_info in "${analytics_endpoints[@]}"; do
        local name="${endpoint_info%%:*}"
        local endpoint="${endpoint_info#*:}"
        # Handle special cases for endpoints with required parameters
        if [[ "$endpoint" == *"&"* ]]; then
            # Extract the base endpoint and parameters
            local clean_endpoint="${endpoint%%&*}"
            local params="${endpoint#*&}"
            local url="${clean_endpoint}?start_date=${start_date}&end_date=${end_date}&${params}"
            test_endpoint "$name" "$url"
        else
            test_endpoint "$name" "${endpoint}?start_date=${start_date}&end_date=${end_date}"
        fi
    done
    
    # Billing endpoints
    test_endpoint "Billing Summary" "/api/v1/billing/summary"
    test_endpoint "Billing Data" "/api/v1/billing/data?limit=10"
    
    # URL encode service category
    local service_category_encoded=$(printf %s "AI and Machine Learning" | jq -sRr @uri)
    test_endpoint "Billing Data with Filters" "/api/v1/billing/data?limit=5&service_category=$service_category_encoded"
    test_endpoint "Cost by Service" "/api/v1/billing/services"
    test_endpoint "Cost Trends" "/api/v1/billing/trends"
    test_endpoint "Billing Statistics" "/api/v1/billing/statistics"
    test_endpoint "Billing Health Check" "/api/v1/billing/health"
    
    # Export endpoints - skip CSV test as it returns CSV data, not JSON
    # test_endpoint "Export Billing Data CSV" "/api/v1/export/billing?format=csv&limit=100"
    test_endpoint "Export Health Check" "/api/v1/export/health"
    
    # Error handling tests (these should return expected errors)
    echo ""
    echo "🔍 Testing error handling..."
    
    test_endpoint "Non-existent Endpoint" "/api/v1/nonexistent" "GET" "" "true"
    
    if [ ! -z "$provider_id" ] && [ "$provider_id" != "null" ]; then
        test_endpoint "Non-existent Provider" "/api/v1/providers/00000000-0000-0000-0000-000000000000" "GET" "" "true"
    fi
    
    if [ ! -z "$run_id" ] && [ "$run_id" != "null" ]; then
        test_endpoint "Non-existent Sync Run" "/api/v1/syncs/runs/00000000-0000-0000-0000-000000000000" "GET" "" "true"
    fi
}

print_summary() {
    local total=$((PASSED + FAILED))
    local success_rate=0
    
    if [ $total -gt 0 ]; then
        success_rate=$(( PASSED * 100 / total ))
    fi
    
    echo ""
    echo "=================================================="
    echo "📊 TEST RESULTS SUMMARY"
    echo "=================================================="
    echo -e "${GREEN}✅ Passed: $PASSED${NC}"
    echo -e "${RED}❌ Failed: $FAILED${NC}"
    echo -e "${BLUE}📈 Success Rate: $success_rate%${NC}"
    echo ""
    
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}💥 Some tests failed!${NC}"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${YELLOW}⚠️ Tests interrupted by user${NC}"; print_summary' INT

# Main execution
main() {
    check_dependencies
    run_tests
    print_summary
}

# Show usage if help requested
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    echo "Usage: $0 [BASE_URL]"
    echo ""
    echo "Test NarevAI API endpoints"
    echo ""
    echo "Arguments:"
    echo "  BASE_URL    Base API URL (default: http://localhost:8000)"
    echo ""
    echo "Environment variables:"
    echo "  VERBOSE     Set to 'true' for verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                              # Test localhost"
    echo "  $0 http://api.example.com       # Test remote API"
    echo "  VERBOSE=true $0                 # Verbose mode"
    exit 0
fi

main "$@"