#!/usr/bin/env python3
"""
Script to anonymize sensitive data in billing_data.csv
"""

import csv
import hashlib
import re
import uuid
from pathlib import Path

def hash_id(value: str, prefix: str = "") -> str:
    """Create consistent hash of sensitive ID"""
    if not value or value in ["", "null", "None"]:
        return ""
    
    # Create consistent hash
    hash_obj = hashlib.md5(f"billing_anonymize_{value}".encode())
    hash_hex = hash_obj.hexdigest()[:12]  # Use first 12 chars
    
    return f"{prefix}{hash_hex}"

def anonymize_arn(arn: str) -> str:
    """Anonymize AWS ARN while keeping structure"""
    if not arn or not arn.startswith("arn:"):
        return arn
    
    # Pattern: arn:aws:service:region:account-id:resource
    parts = arn.split(":")
    if len(parts) >= 6:
        # Replace account ID (index 4)
        if parts[4]:
            parts[4] = hash_id(parts[4], "123456")
        
        # Replace resource names but keep types
        resource_part = ":".join(parts[5:])
        
        # Common patterns to anonymize
        # Lambda function names
        resource_part = re.sub(r'function:([^/\s:]+)', lambda m: f'function:demo-{hash_id(m.group(1))[:8]}', resource_part)
        # RDS instance names  
        resource_part = re.sub(r'db:([^/\s:]+)', lambda m: f'db:demo-{hash_id(m.group(1))[:8]}', resource_part)
        # EC2 instance IDs
        resource_part = re.sub(r'(i-[a-f0-9]+)', lambda m: f'i-{hash_id(m.group(1))[:17]}', resource_part)
        # S3 bucket names
        resource_part = re.sub(r'/([^/\s]+)$', lambda m: f'/demo-bucket-{hash_id(m.group(1))[:8]}', resource_part)
        
        parts[5:] = [resource_part]
        return ":".join(parts)
    
    return arn

def anonymize_resource_name(name: str) -> str:
    """Anonymize resource names"""
    if not name:
        return name
        
    # S3 bucket names
    if name.startswith("s3://") or "-bucket" in name or "bucket" in name.lower():
        return f"demo-bucket-{hash_id(name)[:8]}"
    
    # Lambda function names
    if "function" in name.lower():
        return f"demo-function-{hash_id(name)[:8]}"
    
    # RDS instances
    if "db:" in name or "-instance" in name:
        return f"demo-db-{hash_id(name)[:8]}"
        
    # EC2 instances
    if name.startswith("i-"):
        return f"i-{hash_id(name)[:17]}"
    
    # Generic resources
    if len(name) > 10:  # Only anonymize longer names
        return f"demo-resource-{hash_id(name)[:8]}"
    
    return name

def anonymize_json_data(json_str: str) -> str:
    """Anonymize JSON data in x_provider_data field"""
    if not json_str:
        return json_str
    
    # Replace account IDs in JSON
    json_str = re.sub(r'"(\d{12})"', lambda m: f'"{hash_id(m.group(1), "123456")}"', json_str)
    
    # Replace resource identifiers
    json_str = re.sub(r'"(i-[a-f0-9]{8,17})"', lambda m: f'"i-{hash_id(m.group(1))[:17]}"', json_str)
    
    return json_str

def anonymize_billing_data(input_file: str, output_file: str):
    """Main anonymization function"""
    
    print(f"Reading from: {input_file}")
    print(f"Writing to: {output_file}")
    
    # Fields to anonymize
    account_id_fields = ["billing_account_id", "sub_account_id"]
    resource_fields = ["resource_id", "resource_name"]
    uuid_fields = ["x_provider_id", "x_raw_billing_data_id"]
    json_fields = ["x_provider_data"]
    
    rows_processed = 0
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in reader:
                # Anonymize account IDs
                for field in account_id_fields:
                    if field in row and row[field]:
                        row[field] = hash_id(row[field], "123456")
                
                # Anonymize resource identifiers
                for field in resource_fields:
                    if field in row and row[field]:
                        if field == "resource_id":
                            row[field] = anonymize_arn(row[field])
                        else:
                            row[field] = anonymize_resource_name(row[field])
                
                # Replace UUIDs
                for field in uuid_fields:
                    if field in row and row[field]:
                        # Generate consistent UUID from hash
                        hash_hex = hash_id(row[field])
                        # Convert to UUID format
                        uuid_str = f"{hash_hex[:8]}-{hash_hex[8:12]}-4{hash_hex[12:15]}-8{hash_hex[15:18]}-{hash_hex[18:30]}"
                        row[field] = uuid_str
                
                # Anonymize JSON data
                for field in json_fields:
                    if field in row and row[field]:
                        row[field] = anonymize_json_data(row[field])
                
                writer.writerow(row)
                rows_processed += 1
    
    print(f"✅ Anonymized {rows_processed} rows")
    print(f"✅ Output saved to: {output_file}")

if __name__ == "__main__":
    script_dir = Path(__file__).parent
    input_file = script_dir / "billing_data.csv"
    output_file = script_dir / "billing_data_anonymized.csv"
    
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        exit(1)
    
    # Create backup
    backup_file = script_dir / f"billing_data_backup.csv"
    print(f"Creating backup: {backup_file}")
    import shutil
    shutil.copy2(input_file, backup_file)
    
    # Anonymize data
    anonymize_billing_data(str(input_file), str(output_file))
    
    print("\n🔒 Anonymization complete!")
    print(f"📁 Original (backup): {backup_file}")
    print(f"📁 Anonymized: {output_file}")