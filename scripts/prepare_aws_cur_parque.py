# scripts/prepare_aws_cur.py
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import random
from datetime import datetime, timedelta
import json
import os
import shutil
import numpy as np

def create_sample_cur_with_aws_structure():
    # Demo data configuration
    BUCKET_NAME = "demo-cost-reports-bucket"
    REGION = "eu-west-1"
    ACCOUNT_ID = "123456789012"  # Demo account ID
    
    # Report parameters
    report_name = "my-cost-report"
    billing_period = "20250701-20250731"
    assembly_id = "20250712T040000Z"
    
    # Set base path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    report_base = os.path.join(base_dir, report_name)
    
    # Remove old files if they exist
    if os.path.exists(report_base):
        print(f"Removing existing directory: {report_base}")
        shutil.rmtree(report_base)
    
    # Create directory structure
    report_path = os.path.join(report_base, billing_period, assembly_id)
    os.makedirs(report_path, exist_ok=True)
    parent_path = os.path.join(report_base, billing_period)
    
    print(f"Creating directory structure: {report_path}")
    
    # CUR 2.0 headers (simplified)
    headers = [
        'identity/LineItemId',
        'identity/TimeInterval',
        'bill/InvoiceId',
        'bill/BillingEntity',
        'bill/BillType',
        'bill/PayerAccountId',
        'bill/BillingPeriodStartDate',
        'bill/BillingPeriodEndDate',
        'lineItem/UsageAccountId',
        'lineItem/LineItemType',
        'lineItem/UsageStartDate',
        'lineItem/UsageEndDate',
        'lineItem/ProductCode',
        'lineItem/UsageType',
        'lineItem/Operation',
        'lineItem/AvailabilityZone',
        'lineItem/ResourceId',
        'lineItem/UsageAmount',
        'lineItem/NormalizationFactor',
        'lineItem/NormalizedUsageAmount',
        'lineItem/CurrencyCode',
        'lineItem/UnblendedRate',
        'lineItem/UnblendedCost',
        'lineItem/BlendedRate',
        'lineItem/BlendedCost',
        'lineItem/LineItemDescription',
        'lineItem/TaxType',
        'lineItem/LegalEntity',
        'product/ProductName',
        'product/location',
        'product/locationType',
        'product/instanceType',
        'product/vcpu',
        'product/memory',
        'product/region',
        'product/regionCode',
        'product/operatingSystem',
        'product/servicecode',
        'product/servicename',
        'product/usagetype',
        'pricing/RateCode',
        'pricing/RateId',
        'pricing/currency',
        'pricing/publicOnDemandCost',
        'pricing/publicOnDemandRate',
        'pricing/term',
        'pricing/unit'
    ]
    
    # Prepare data
    all_data = []
    
    # Generate data for days 2025-07-15 to 2025-07-20
    start_date = datetime(2025, 7, 15)
    end_date = datetime(2025, 7, 20, 23, 59, 59)
    
    line_item_id = 1
    
    # Sample service data
    services_data = [
        {
            'ProductCode': 'AmazonEC2',
            'UsageType': 'EUW1-BoxUsage:t3.micro',
            'Operation': 'RunInstances',
            'ResourceId': 'i-0a1b2c3d4e5f67890',
            'ProductName': 'Amazon Elastic Compute Cloud',
            'InstanceType': 't3.micro',
            'vcpu': '2',
            'memory': '1 GiB',
            'os': 'Linux/UNIX',
            'unit': 'Hrs'
        },
        {
            'ProductCode': 'AmazonS3',
            'UsageType': 'EUW1-TimedStorage-ByteHrs',
            'Operation': 'StandardStorage',
            'ResourceId': 'demo-cost-reports-bucket',
            'ProductName': 'Amazon Simple Storage Service',
            'unit': 'GB-Mo'
        },
        {
            'ProductCode': 'AmazonRDS',
            'UsageType': 'EUW1-InstanceUsage:db.t3.micro',
            'Operation': 'CreateDBInstance:0002',
            'ResourceId': f'arn:aws:rds:{REGION}:{ACCOUNT_ID}:db:mydb-instance',
            'ProductName': 'Amazon Relational Database Service',
            'InstanceType': 'db.t3.micro',
            'unit': 'Hrs'
        },
        {
            'ProductCode': 'AWSLambda',
            'UsageType': 'EUW1-Lambda-GB-Second',
            'Operation': 'Invoke',
            'ResourceId': f'arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:myfunction',
            'ProductName': 'AWS Lambda',
            'unit': 'GB-Second'
        }
    ]
    
    availability_zones = ['eu-west-1a', 'eu-west-1b', 'eu-west-1c']
    
    current_date = start_date
    while current_date <= end_date:
        for service in services_data:
            # Generuj dane godzinowe
            for hour in range(24):
                hour_start = current_date.replace(hour=hour, minute=0, second=0, microsecond=0)
                hour_end = hour_start + timedelta(hours=1)
                
                # Different usage amounts for different services
                if service['ProductCode'] == 'AmazonEC2':
                    usage_amount = 1.0  # 1 godzina instancji
                    rate = 0.0116  # ~$0.0116/hour for t3.micro
                elif service['ProductCode'] == 'AmazonS3':
                    usage_amount = round(random.uniform(10.0, 100.0), 6)  # GB
                    rate = 0.023  # $0.023 per GB
                elif service['ProductCode'] == 'AmazonRDS':
                    usage_amount = 1.0
                    rate = 0.017  # ~$0.017/hour for db.t3.micro
                else:  # Lambda
                    usage_amount = round(random.uniform(100, 1000), 2)  # GB-seconds
                    rate = 0.0000166667  # $0.0000166667 per GB-second
                
                unblended_cost = round(usage_amount * rate, 6)
                
                row_dict = {
                    'identity/LineItemId': f'{assembly_id}-{line_item_id:010d}',
                    'identity/TimeInterval': f'{hour_start.isoformat()}Z/{hour_end.isoformat()}Z',
                    'bill/InvoiceId': '',
                    'bill/BillingEntity': 'AWS',
                    'bill/BillType': 'Anniversary',
                    'bill/PayerAccountId': ACCOUNT_ID,
                    'bill/BillingPeriodStartDate': '2025-07-01T00:00:00Z',
                    'bill/BillingPeriodEndDate': '2025-07-31T23:59:59Z',
                    'lineItem/UsageAccountId': ACCOUNT_ID,
                    'lineItem/LineItemType': 'Usage',
                    'lineItem/UsageStartDate': hour_start.isoformat() + 'Z',
                    'lineItem/UsageEndDate': hour_end.isoformat() + 'Z',
                    'lineItem/ProductCode': service['ProductCode'],
                    'lineItem/UsageType': service['UsageType'],
                    'lineItem/Operation': service['Operation'],
                    'lineItem/AvailabilityZone': random.choice(availability_zones) if 'EC2' in service['ProductCode'] or 'RDS' in service['ProductCode'] else '',
                    'lineItem/ResourceId': service['ResourceId'],
                    'lineItem/UsageAmount': usage_amount,
                    'lineItem/NormalizationFactor': 1.0,
                    'lineItem/NormalizedUsageAmount': usage_amount,
                    'lineItem/CurrencyCode': 'USD',
                    'lineItem/UnblendedRate': rate,
                    'lineItem/UnblendedCost': unblended_cost,
                    'lineItem/BlendedRate': rate,
                    'lineItem/BlendedCost': unblended_cost,
                    'lineItem/LineItemDescription': f"{service['ProductName']} {service['UsageType']}",
                    'lineItem/TaxType': '',
                    'lineItem/LegalEntity': 'Amazon Web Services EMEA SARL',
                    'product/ProductName': service['ProductName'],
                    'product/location': 'EU (Ireland)',
                    'product/locationType': 'AWS Region',
                    'product/instanceType': service.get('InstanceType', ''),
                    'product/vcpu': service.get('vcpu', ''),
                    'product/memory': service.get('memory', ''),
                    'product/region': 'EU (Ireland)',
                    'product/regionCode': REGION,
                    'product/operatingSystem': service.get('os', ''),
                    'product/servicecode': service['ProductCode'],
                    'product/servicename': service['ProductName'],
                    'product/usagetype': service['UsageType'],
                    'pricing/RateCode': f"R{random.randint(1000000, 9999999)}",
                    'pricing/RateId': f"{service['ProductCode']}-{service['UsageType']}-{hour_start.strftime('%Y%m%d')}",
                    'pricing/currency': 'USD',
                    'pricing/publicOnDemandCost': unblended_cost,
                    'pricing/publicOnDemandRate': rate,
                    'pricing/term': 'OnDemand',
                    'pricing/unit': service.get('unit', 'Hrs')
                }
                
                all_data.append(row_dict)
                line_item_id += 1
        
        current_date += timedelta(days=1)
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    
    # Set proper data types
    # Numeric columns
    float_columns = [
        'lineItem/UsageAmount',
        'lineItem/NormalizationFactor',
        'lineItem/NormalizedUsageAmount',
        'lineItem/UnblendedRate',
        'lineItem/UnblendedCost',
        'lineItem/BlendedRate',
        'lineItem/BlendedCost',
        'pricing/publicOnDemandCost',
        'pricing/publicOnDemandRate'
    ]
    
    for col in float_columns:
        df[col] = df[col].astype('float64')
    
    # Date columns - keep as string (AWS CUR uses string for dates)
    
    # Save as Parquet (may be split into parts)
    chunk_size = 100000  # Liczba wierszy na plik
    report_keys = []
    
    if len(df) > chunk_size:
        # Split into parts
        num_chunks = (len(df) + chunk_size - 1) // chunk_size
        for i in range(num_chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, len(df))
            chunk_df = df.iloc[start_idx:end_idx]
            
            # File name compliant with AWS convention
            parquet_filename = os.path.join(report_path, f"{report_name}-{i+1:05d}.snappy.parquet")
            
            # Save as Parquet with Snappy compression (AWS standard)
            chunk_df.to_parquet(
                parquet_filename,
                engine='pyarrow',
                compression='snappy',
                index=False
            )
            
            report_keys.append(f"{report_name}-{i+1:05d}.snappy.parquet")
            print(f"  📄 Utworzono: {os.path.basename(parquet_filename)}")
    else:
        # Single file
        parquet_filename = os.path.join(report_path, f"{report_name}-00001.snappy.parquet")
        df.to_parquet(
            parquet_filename,
            engine='pyarrow',
            compression='snappy',
            index=False
        )
        report_keys.append(f"{report_name}-00001.snappy.parquet")
        print(f"  📄 Utworzono: {os.path.basename(parquet_filename)}")
    
    # Create manifest file
    manifest = {
        "assemblyId": assembly_id,
        "account": ACCOUNT_ID,
        "columns": headers,
        "charset": "UTF-8",
        "reportName": report_name,
        "reportKeys": report_keys,
        "bucket": BUCKET_NAME,
        "billingPeriod": {
            "start": "2025-07-01T00:00:00.000Z",
            "end": "2025-07-31T23:59:59.999Z"
        },
        "region": REGION,
        "version": "1.0",
        "reportCount": len(report_keys),
        "compression": "Parquet",
        "contentType": "application/x-parquet"
    }
    
    # Save manifest in two places
    # 1. In assemblyId directory
    manifest_filename = os.path.join(report_path, f"{report_name}-Manifest.json")
    with open(manifest_filename, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    # 2. In billing period directory
    parent_manifest_filename = os.path.join(parent_path, f"{report_name}-Manifest.json")
    with open(parent_manifest_filename, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    # Additionally create status file (used by Athena)
    status_filename = os.path.join(parent_path, "cost_and_usage_data_status")
    with open(status_filename, 'w') as f:
        f.write("READY")
    
    print(f"\n✅ CUR structure in Parquet format created successfully!")
    print(f"📁 Location: {report_base}")
    print(f"📊 Generated {len(df)} data lines")
    print(f"📦 Created {len(report_keys)} .parquet files")
    print(f"\n🚀 You can now upload files to S3 using:")
    print(f"   aws s3 sync {report_name}\\{billing_period}\\{assembly_id}\\ s3://{BUCKET_NAME}/{report_name}/{billing_period}/{assembly_id}/ --region {REGION}")
    print(f"   aws s3 cp {report_name}\\{billing_period}\\{report_name}-Manifest.json s3://{BUCKET_NAME}/{report_name}/{billing_period}/ --region {REGION}")
    print(f"   aws s3 cp {report_name}\\{billing_period}\\cost_and_usage_data_status s3://{BUCKET_NAME}/{report_name}/{billing_period}/ --region {REGION}")
    
    return report_name, billing_period, assembly_id

if __name__ == "__main__":
    # Check if we have required libraries
    try:
        import pandas
        import pyarrow
    except ImportError:
        print("❌ Missing required libraries! Install them:")
        print("   pip install pandas pyarrow")
        exit(1)
    
    create_sample_cur_with_aws_structure()
