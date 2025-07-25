# scripts/prepare_aws_cur.py
import csv
import random
from datetime import datetime, timedelta
import gzip
import json
import os
import shutil

def create_sample_cur_with_aws_structure():
    # Demo data configuration
    BUCKET_NAME = "demo-cost-reports-bucket"
    REGION = "eu-west-1"
    ACCOUNT_ID = "123456789012"
    
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
    
    rows = []
    
    # Generate data for days 2025-07-06 to 2025-07-11
    start_date = datetime(2025, 7, 6)
    end_date = datetime(2025, 7, 11, 23, 59, 59)
    
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
                
                row = [
                    f'{assembly_id}-{line_item_id:010d}',  # LineItemId
                    f'{hour_start.isoformat()}Z/{hour_end.isoformat()}Z',  # TimeInterval
                    '',  # InvoiceId (puste do finalizacji)
                    'AWS',  # BillingEntity
                    'Anniversary',  # BillType
                    ACCOUNT_ID,  # PayerAccountId
                    '2025-07-01T00:00:00Z',  # BillingPeriodStartDate
                    '2025-07-31T23:59:59Z',  # BillingPeriodEndDate
                    ACCOUNT_ID,  # UsageAccountId
                    'Usage',  # LineItemType
                    hour_start.isoformat() + 'Z',  # UsageStartDate
                    hour_end.isoformat() + 'Z',  # UsageEndDate
                    service['ProductCode'],  # ProductCode
                    service['UsageType'],  # UsageType
                    service['Operation'],  # Operation
                    random.choice(availability_zones) if 'EC2' in service['ProductCode'] or 'RDS' in service['ProductCode'] else '',  # AvailabilityZone
                    service['ResourceId'],  # ResourceId
                    str(usage_amount),  # UsageAmount
                    '1',  # NormalizationFactor
                    str(usage_amount),  # NormalizedUsageAmount
                    'USD',  # CurrencyCode
                    str(rate),  # UnblendedRate
                    str(unblended_cost),  # UnblendedCost
                    str(rate),  # BlendedRate
                    str(unblended_cost),  # BlendedCost
                    f"{service['ProductName']} {service['UsageType']}",  # LineItemDescription
                    '',  # TaxType
                    'Amazon Web Services EMEA SARL',  # LegalEntity (for EU)
                    service['ProductName'],  # product/ProductName
                    'EU (Ireland)',  # product/location
                    'AWS Region',  # product/locationType
                    service.get('InstanceType', ''),  # product/instanceType
                    service.get('vcpu', ''),  # product/vcpu
                    service.get('memory', ''),  # product/memory
                    'EU (Ireland)',  # product/region
                    REGION,  # product/regionCode
                    service.get('os', ''),  # product/operatingSystem
                    service['ProductCode'],  # product/servicecode
                    service['ProductName'],  # product/servicename
                    service['UsageType'],  # product/usagetype
                    f"R{random.randint(1000000, 9999999)}",  # pricing/RateCode
                    f"{service['ProductCode']}-{service['UsageType']}-{hour_start.strftime('%Y%m%d')}",  # pricing/RateId
                    'USD',  # pricing/currency
                    str(unblended_cost),  # pricing/publicOnDemandCost
                    str(rate),  # pricing/publicOnDemandRate
                    'OnDemand',  # pricing/term
                    service.get('unit', 'Hrs')  # pricing/unit
                ]
                
                rows.append(row)
                line_item_id += 1
        
        current_date += timedelta(days=1)
    
    # Save to files (split into chunks if too large)
    chunk_size = 50000  # Smaller chunks for better compression
    file_number = 1
    report_keys = []
    
    for i in range(0, len(rows), chunk_size):
        chunk_rows = rows[i:i + chunk_size]
        
        # File name compliant with AWS convention
        csv_filename = os.path.join(report_path, f"{report_name}-{file_number:05d}.csv")
        gz_filename = os.path.join(report_path, f"{report_name}-{file_number:05d}.csv.gz")
        
        # Save CSV
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            writer.writerows(chunk_rows)
        
        # Compress to gzip
        with open(csv_filename, 'rb') as f_in:
            with gzip.open(gz_filename, 'wb') as f_out:
                f_out.writelines(f_in)
        
        # Remove uncompressed file
        os.remove(csv_filename)
        
        report_keys.append(f"{report_name}-{file_number:05d}.csv.gz")
        file_number += 1
    
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
        "compression": "GZIP"
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
    
    print(f"\n✅ CUR structure created successfully!")
    print(f"📁 Location: {report_base}")
    print(f"📊 Generated {len(rows)} data lines")
    print(f"📦 Created {len(report_keys)} .csv.gz files")
    print(f"\n🚀 You can now upload files to S3 using:")
    print(f"   aws s3 sync {report_name}\\{billing_period}\\{assembly_id}\\ s3://{BUCKET_NAME}/{report_name}/{billing_period}/{assembly_id}/ --region {REGION}")
    print(f"   aws s3 cp {report_name}\\{billing_period}\\{report_name}-Manifest.json s3://{BUCKET_NAME}/{report_name}/{billing_period}/ --region {REGION}")
    
    return report_name, billing_period, assembly_id

if __name__ == "__main__":
    create_sample_cur_with_aws_structure()
