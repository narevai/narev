"""
Generate mock Azure FOCUS export data for testing
"""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


# ===== CONFIGURATION =====
# Define the date range for mock data generation
START_DATE = datetime(2025, 7, 10, 0, 0, 0)  # November 1, 2024
END_DATE = datetime(2024, 7, 13, 23, 59, 59)  # November 30, 2024

# Number of records to generate
NUM_RECORDS = 50

# Output directory
OUTPUT_DIR = Path("mock_data/azure")

# If True, generates hourly data points between START_DATE and END_DATE
# If False, generates NUM_RECORDS random data points in the date range
GENERATE_HOURLY_DATA = False


class AzureFOCUSMockGenerator:
    """Generate mock data in Azure FOCUS format"""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
        
        # Azure services and regions
        self.services = [
            "Virtual Machines", "Storage", "SQL Database", "App Service",
            "Functions", "Cosmos DB", "Key Vault", "Load Balancer",
            "Application Gateway", "VPN Gateway", "Container Instances",
            "Kubernetes Service", "Cognitive Services", "Monitor"
        ]
        
        self.regions = [
            "West Europe", "North Europe", "East US", "West US",
            "Central US", "UK South", "Germany West Central"
        ]
        
        self.resource_groups = [
            "rg-production", "rg-development", "rg-staging", 
            "rg-shared-services", "rg-networking"
        ]
        
        self.vm_sizes = [
            "Standard_B2s", "Standard_D2s_v3", "Standard_D4s_v3",
            "Standard_E2s_v3", "Standard_F2s_v2", "Standard_D8s_v3"
        ]
        
        self.storage_types = [
            "Standard_LRS", "Standard_GRS", "Premium_LRS"
        ]
        
        # Demo subscription and billing info
        self.subscription_id = "12345678-1234-1234-1234-123456789012"
        self.subscription_name = "Demo Azure Subscription"
        self.billing_account_id = "12345678"
        self.billing_account_name = "Demo Billing Account"
        self.tenant_id = "87654321-4321-4321-4321-210987654321"
        
    def generate_records(self, num_records: int = 1000, hourly: bool = False) -> List[Dict[str, Any]]:
        """Generate mock FOCUS records
        
        Args:
            num_records: Number of records to generate (ignored if hourly=True)
            hourly: If True, generates one record per hour in the date range
        """
        records = []
        
        if hourly:
            # Generate one record per hour
            current_date = self.start_date
            index = 0
            while current_date <= self.end_date:
                record = self._generate_single_record(current_date, index)
                records.append(record)
                current_date += timedelta(hours=1)
                index += 1
            print(f"Generated {len(records)} hourly records")
        else:
            # Generate specified number of records distributed across date range
            if num_records <= 0:
                raise ValueError("num_records must be positive")
                
            # Calculate time delta between records
            total_duration = self.end_date - self.start_date
            if num_records > 1:
                delta = total_duration / (num_records - 1)
            else:
                delta = timedelta(0)
            
            current_date = self.start_date
            for i in range(num_records):
                # Add some randomness to avoid perfectly uniform distribution
                jitter = timedelta(seconds=random.randint(-1800, 1800))  # +/- 30 minutes
                record_date = current_date + jitter
                
                # Ensure we don't go outside the bounds
                record_date = max(self.start_date, min(record_date, self.end_date))
                
                record = self._generate_single_record(record_date, i)
                records.append(record)
                
                if i < num_records - 1:
                    current_date += delta
            
        return records
    
    def _generate_single_record(self, date: datetime, index: int) -> Dict[str, Any]:
        """Generate a single FOCUS record"""
        
        service = random.choice(self.services)
        region = random.choice(self.regions)
        resource_group = random.choice(self.resource_groups)
        
        # Generate resource ID
        resource_id = self._generate_resource_id(service, resource_group)
        
        # Calculate costs
        list_cost = Decimal(str(round(random.uniform(0.01, 100), 4)))
        discount = Decimal(str(round(random.uniform(0, 0.3), 2)))
        effective_cost = list_cost * (1 - discount)
        
        # Usage quantity
        usage_quantity = round(random.uniform(1, 1000), 2)
        
        # Determine billing period (month containing the date)
        billing_period_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Get first day of next month
        if billing_period_start.month == 12:
            billing_period_end = billing_period_start.replace(year=billing_period_start.year + 1, month=1)
        else:
            billing_period_end = billing_period_start.replace(month=billing_period_start.month + 1)
        
        record = {
            # Temporal fields
            "ChargePeriodStart": date.isoformat(),
            "ChargePeriodEnd": (date + timedelta(hours=1)).isoformat(),
            "BillingPeriodStart": billing_period_start.isoformat(),
            "BillingPeriodEnd": billing_period_end.isoformat(),
            
            # Provider fields
            "ProviderName": "Microsoft",
            "PublisherName": "Microsoft",
            "InvoiceIssuerName": "Microsoft",
            
            # Account fields
            "BillingAccountId": self.billing_account_id,
            "BillingAccountName": self.billing_account_name,
            "SubAccountId": self.subscription_id,
            "SubAccountName": self.subscription_name,
            
            # Service fields
            "ServiceName": service,
            "ServiceCategory": self._get_service_category(service),
            "ResourceId": resource_id,
            "ResourceName": f"{service.lower().replace(' ', '-')}-{index}",
            "ResourceType": self._get_resource_type(service),
            "Region": region,
            
            # Cost fields
            "BillingCurrency": "USD",
            "ListCost": float(list_cost),
            "ListUnitPrice": float(list_cost / Decimal(str(usage_quantity)) if usage_quantity > 0 else list_cost),
            "ContractedCost": float(effective_cost),
            "ContractedUnitPrice": float(effective_cost / Decimal(str(usage_quantity)) if usage_quantity > 0 else effective_cost),
            "EffectiveCost": float(effective_cost),
            "BilledCost": float(effective_cost),
            
            # Usage fields
            "ConsumedQuantity": usage_quantity,
            "ConsumedUnit": self._get_unit_for_service(service),
            "PricingQuantity": usage_quantity,
            "PricingUnit": self._get_unit_for_service(service),
            
            # Charge fields
            "ChargeCategory": "Usage",
            "ChargeClass": random.choice(["Compute", "Storage", "Network", "Database"]),
            "ChargeDescription": f"{service} usage",
            "ChargeFrequency": "Usage-Based",
            "ChargeSubcategory": "On-Demand",
            
            # SKU fields
            "SkuId": f"DZH318Z0{random.randint(1000, 9999)}",
            "SkuPriceId": f"Price_{random.randint(1000, 9999)}",
            
            # Commitment fields (some records have discounts)
            "CommitmentDiscountCategory": "Spend" if discount > 0 else "",
            "CommitmentDiscountId": f"discount-{random.randint(1000, 9999)}" if discount > 0 else "",
            "CommitmentDiscountName": "Azure Savings Plan" if discount > 0 else "",
            "CommitmentDiscountStatus": "Active" if discount > 0 else "",
            "CommitmentDiscountType": "Savings Plan" if discount > 0 else "",
            
            # Pricing fields
            "PricingCategory": "On-Demand",
            
            # Azure-specific extensions
            "x_AzureResourceGroupName": resource_group,
            "x_AzureSubscriptionId": self.subscription_id,
            "x_AzureSubscriptionName": self.subscription_name,
            "x_AzureTenantId": self.tenant_id,
            "x_AzureTenantName": "Default Directory",
            "x_AzureManagementGroupName": "Root Management Group",
            "x_AzureDepartmentName": "IT Department",
            "x_AzureEnrollmentAccountName": "Enterprise Enrollment",
            
            # Tags
            "Tags/Environment": random.choice(["Production", "Development", "Staging"]),
            "Tags/CostCenter": f"CC{random.randint(100, 999)}",
            "Tags/Project": f"Project-{random.choice(['Alpha', 'Beta', 'Gamma', 'Delta'])}",
            "Tags/Owner": random.choice(["TeamA", "TeamB", "TeamC"]),
        }
        
        return record
    
    def _generate_resource_id(self, service: str, resource_group: str) -> str:
        """Generate Azure resource ID"""
        resource_type = self._get_resource_type(service)
        resource_name = f"{service.lower().replace(' ', '-')}-{random.randint(1000, 9999)}"
        
        return (
            f"/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{resource_group}"
            f"/providers/Microsoft.{resource_type}"
            f"/{resource_name}"
        )
    
    def _get_service_category(self, service: str) -> str:
        """Map service to category"""
        mapping = {
            "Virtual Machines": "Compute",
            "Storage": "Storage",
            "SQL Database": "Database",
            "Cosmos DB": "Database",
            "App Service": "Compute",
            "Functions": "Compute",
            "Key Vault": "Security",
            "Load Balancer": "Networking",
            "Application Gateway": "Networking",
            "VPN Gateway": "Networking",
            "Container Instances": "Compute",
            "Kubernetes Service": "Compute",
            "Cognitive Services": "AI + Machine Learning",
            "Monitor": "Management and Governance"
        }
        return mapping.get(service, "Other")
    
    def _get_resource_type(self, service: str) -> str:
        """Get resource type for service"""
        mapping = {
            "Virtual Machines": "Compute/virtualMachines",
            "Storage": "Storage/storageAccounts",
            "SQL Database": "Sql/servers/databases",
            "Cosmos DB": "DocumentDB/databaseAccounts",
            "App Service": "Web/sites",
            "Functions": "Web/sites",
            "Key Vault": "KeyVault/vaults",
            "Load Balancer": "Network/loadBalancers",
            "Application Gateway": "Network/applicationGateways",
            "VPN Gateway": "Network/virtualNetworkGateways",
            "Container Instances": "ContainerInstance/containerGroups",
            "Kubernetes Service": "ContainerService/managedClusters",
            "Cognitive Services": "CognitiveServices/accounts",
            "Monitor": "Insights/components"
        }
        return mapping.get(service, "Resources/generic")
    
    def _get_unit_for_service(self, service: str) -> str:
        """Get unit of measure for service"""
        mapping = {
            "Virtual Machines": "Hours",
            "Storage": "GB",
            "SQL Database": "Hours",
            "Cosmos DB": "RU",
            "App Service": "Hours",
            "Functions": "Executions",
            "Key Vault": "Operations",
            "Load Balancer": "Hours",
            "Application Gateway": "Hours",
            "VPN Gateway": "Hours",
            "Container Instances": "Hours",
            "Kubernetes Service": "Hours",
            "Cognitive Services": "Transactions",
            "Monitor": "GB"
        }
        return mapping.get(service, "Units")
    
    def save_as_parquet(self, records: List[Dict[str, Any]], output_dir: Path):
        """Save records as partitioned parquet files like Azure does"""
        
        # Convert to DataFrame
        df = pd.DataFrame(records)
        
        # Azure creates partitioned files
        # Structure: exportname/YYYYMMDD-YYYYMMDD/RunID/part-00000.parquet
        
        # Create date range folder
        date_range = f"{self.start_date.strftime('%Y%m%d')}-{self.end_date.strftime('%Y%m%d')}"
        run_id = f"run-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create directory structure
        export_dir = output_dir / "azure-focus-export" / date_range / run_id
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Split into multiple part files (Azure typically creates multiple parts)
        chunk_size = 250  # Records per file
        num_parts = (len(records) + chunk_size - 1) // chunk_size
        
        for i in range(num_parts):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(records))
            chunk_df = df.iloc[start_idx:end_idx]
            
            # Write part file
            part_file = export_dir / f"part-{i:05d}.parquet"
            chunk_df.to_parquet(part_file, compression='snappy', index=False)
            print(f"Created: {part_file}")
        
        # Create manifest.json
        manifest = self._create_manifest(date_range, run_id, num_parts, len(records))
        manifest_file = export_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Created: {manifest_file}")
        
        return export_dir
    
    def _create_manifest(self, date_range: str, run_id: str, num_parts: int, total_records: int) -> dict:
        """Create Azure manifest.json"""
        blobs = []
        for i in range(num_parts):
            blobs.append({
                "blobName": f"azure-focus-export/{date_range}/{run_id}/part-{i:05d}.parquet",
                "byteCount": random.randint(50000, 150000),  # Mock file size
                "dataRowCount": min(250, total_records - i * 250)
            })
        
        manifest = {
            "manifestVersion": "2024-04-01",
            "byteCount": sum(b["byteCount"] for b in blobs),
            "blobCount": num_parts,
            "dataRowCount": total_records,
            "exportConfig": {
                "exportName": "azure-focus-export",
                "resourceId": f"/subscriptions/{self.subscription_id}/providers/Microsoft.CostManagement/exports/azure-focus-export",
                "dataVersion": "1.0",
                "apiVersion": "2023-07-01-preview",
                "type": "FocusExport",
                "timeFrame": "Custom",
                "granularity": "Hourly"
            },
            "deliveryConfig": {
                "partitionData": True,
                "dataOverwriteBehavior": "OverwritePreviousReport",
                "fileFormat": "Parquet",
                "compressionMode": "Snappy",
                "containerUri": f"/subscriptions/{self.subscription_id}/resourceGroups/rg-finops-prod/providers/Microsoft.Storage/storageAccounts/finopscostexports",
                "rootFolderPath": "focus-exports/daily"
            },
            "runInfo": {
                "executionType": "Scheduled",
                "submittedTime": datetime.utcnow().isoformat() + "Z",
                "runId": run_id,
                "startDate": self.start_date.isoformat(),
                "endDate": self.end_date.isoformat() + "Z"
            },
            "blobs": blobs
        }
        
        return manifest


def main():
    """Generate mock Azure FOCUS data"""
    
    print(f"Generating Azure FOCUS mock data...")
    print(f"Date range: {START_DATE} to {END_DATE}")
    print(f"Number of records: {NUM_RECORDS} (ignored if GENERATE_HOURLY_DATA=True)")
    print(f"Hourly data generation: {GENERATE_HOURLY_DATA}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    generator = AzureFOCUSMockGenerator(START_DATE, END_DATE)
    records = generator.generate_records(
        num_records=NUM_RECORDS, 
        hourly=GENERATE_HOURLY_DATA
    )
    
    print(f"\nGenerated {len(records)} records")
    
    # Save as parquet
    export_dir = generator.save_as_parquet(records, OUTPUT_DIR)
    
    print(f"\nMock data created in: {export_dir}")
    print("\nTo use this data:")
    print("1. Upload the entire folder structure to your Azure Storage container")
    print("2. Configure your Azure provider with the storage account details")
    print("3. The filesystem extractor will find and process these files")


if __name__ == "__main__":
    main()
