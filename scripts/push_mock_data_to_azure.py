"""
Upload mock data to Azure Storage
"""

import os
import sys
from pathlib import Path
from getpass import getpass

from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError


def get_account_key(storage_account: str) -> str:
    """Prompt user for storage account key"""
    print(f"\nAzure Storage Account: {storage_account}")
    print("To get your storage account key:")
    print("1. Go to Azure Portal (https://portal.azure.com)")
    print("2. Navigate to your storage account")
    print("3. Go to 'Access keys' under 'Security + networking'")
    print("4. Copy key1 or key2")
    print()
    
    # Use getpass to hide the key input
    account_key = getpass("Enter your storage account key: ")
    
    if not account_key or account_key == "your-storage-account-key":
        print("\nError: Invalid storage account key")
        sys.exit(1)
    
    return account_key


def upload_directory_to_azure(
    local_path: Path,
    storage_account: str,
    container_name: str,
    account_key: str,
    remote_path: str = "",
    preserve_structure: bool = True
):
    """Upload directory to Azure Storage
    
    Args:
        local_path: Local directory to upload
        storage_account: Azure storage account name
        container_name: Container name
        account_key: Storage account key
        remote_path: Base path in container
        preserve_structure: If True, preserves the local directory structure
    """
    
    # Validate local path
    if not local_path.exists():
        print(f"Error: Local path does not exist: {local_path}")
        sys.exit(1)
    
    # Create blob service client
    connection_string = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={storage_account};"
        f"AccountKey={account_key};"
        f"EndpointSuffix=core.windows.net"
    )
    
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
    except Exception as e:
        print(f"Error connecting to Azure Storage: {e}")
        print("Please check your storage account name and key")
        sys.exit(1)
    
    # Create container if not exists
    try:
        container_client.create_container()
        print(f"Created container: {container_name}")
    except ResourceExistsError:
        print(f"Container '{container_name}' already exists")
    except Exception as e:
        print(f"Error creating container: {e}")
        sys.exit(1)
    
    # Count files to upload
    total_files = sum([len(files) for _, _, files in os.walk(local_path)])
    if total_files == 0:
        print(f"No files found in {local_path}")
        return
    
    print(f"\nFound {total_files} files to upload")
    
    # Upload files
    uploaded_count = 0
    failed_count = 0
    
    for root, dirs, files in os.walk(local_path):
        for file in files:
            local_file_path = Path(root) / file
            
            # Calculate blob name
            if preserve_structure:
                # For Azure FOCUS exports, we want the structure to be:
                # daily/billing_data-focus-cost/YYYYMMDD-YYYYMMDD/file.parquet
                # So we need to get just the date range and run ID parts
                relative_path = local_file_path.relative_to(local_path.parent.parent)
                # This gives us: azure-focus-export/YYYYMMDD-YYYYMMDD/RunID/file.parquet
                # We want just: YYYYMMDD-YYYYMMDD/RunID/file.parquet
                path_parts = relative_path.parts
                if len(path_parts) > 1 and path_parts[0] == "azure-focus-export":
                    relative_path = Path(*path_parts[1:])
            else:
                # Only keep structure relative to the upload directory
                relative_path = local_file_path.relative_to(local_path)
            
            # Combine with remote path
            if remote_path:
                blob_name = f"{remote_path}/{relative_path}".replace("\\", "/")
            else:
                blob_name = str(relative_path).replace("\\", "/")
            
            # Clean up the path (remove double slashes, leading slash)
            blob_name = blob_name.replace("//", "/").lstrip("/")
            
            # Upload file
            try:
                print(f"Uploading: {blob_name} ... ", end="", flush=True)
                
                with open(local_file_path, "rb") as data:
                    blob_client = container_client.get_blob_client(blob_name)
                    blob_client.upload_blob(data, overwrite=True)
                
                print("✓")
                uploaded_count += 1
                
            except Exception as e:
                print(f"✗ Failed: {e}")
                failed_count += 1
    
    # Summary
    print(f"\n{'='*50}")
    print(f"Upload complete!")
    print(f"Successfully uploaded: {uploaded_count} files")
    if failed_count > 0:
        print(f"Failed: {failed_count} files")
    print(f"\nFiles are available at:")
    print(f"https://{storage_account}.blob.core.windows.net/{container_name}/{remote_path}")


def main():
    """Main function"""
    
    # Configuration
    LOCAL_PATH = Path("mock_data/azure/azure-focus-export")
    STORAGE_ACCOUNT = "democostexports"  # Demo storage account name
    CONTAINER_NAME = "focus-exports"
    REMOTE_PATH = "daily/billing_data-focus-cost"
    
    # Check if we have the export directory
    if not LOCAL_PATH.exists():
        print(f"Error: Directory not found: {LOCAL_PATH}")
        print("\nPlease run generate_azure_focus_mock_data.py first to create mock data")
        sys.exit(1)
    
    # Find the most recent export
    exports = list(LOCAL_PATH.glob("*/*/*"))
    if not exports:
        print(f"No exports found in {LOCAL_PATH}")
        print("\nPlease run generate_azure_focus_mock_data.py first to create mock data")
        sys.exit(1)
    
    # Get the parent directory that contains the date range folder
    # Structure: azure-focus-export/YYYYMMDD-YYYYMMDD/RunID/files
    date_dirs = [d for d in LOCAL_PATH.iterdir() if d.is_dir()]
    if not date_dirs:
        print("No date range directories found")
        sys.exit(1)
    
    # Use the most recent date directory
    latest_date_dir = sorted(date_dirs)[-1]
    
    print(f"Azure Storage Upload Tool")
    print(f"{'='*50}")
    print(f"Local directory: {latest_date_dir}")
    print(f"Storage account: {STORAGE_ACCOUNT}")
    print(f"Container: {CONTAINER_NAME}")
    print(f"Remote path: {REMOTE_PATH}")
    
    # Ask for confirmation
    response = input("\nProceed with upload? (y/n): ")
    if response.lower() != 'y':
        print("Upload cancelled")
        sys.exit(0)
    
    # Get storage account key
    account_key = get_account_key(STORAGE_ACCOUNT)
    
    # Upload
    upload_directory_to_azure(
        local_path=latest_date_dir,
        storage_account=STORAGE_ACCOUNT,
        container_name=CONTAINER_NAME,
        account_key=account_key,
        remote_path=REMOTE_PATH,
        preserve_structure=True  # This will keep the azure-focus-export/date/runid structure
    )


if __name__ == "__main__":
    main()
