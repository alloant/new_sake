import os
import json
import tempfile
import httpx
import asyncio
from pathlib import PurePosixPath
from urllib.parse import urlparse

from synology_api import filestation
from .synology_drivestation import DriveStation

# Configuration
USER = os.getenv("SYNOLOGY_SERVICE_USER")
PASS = os.getenv("SYNOLOGY_SERVICE_PASSWD")
IP = os.getenv("SYNOLOGY_SERVER")
PORT = os.getenv("SYNOLOGY_PORT")

# Change these to None initially
_fs_instance = None
_ds_instance = None

def get_fs():
    """Returns a valid FileStation instance, reconnecting if necessary."""
    global _fs_instance
    if _fs_instance is None:
        print("Initializing FileStation connection...")
        _fs_instance = filestation.FileStation(IP, PORT, USER, PASS, secure=True, cert_verify=False, dsm_version=7, debug=False)
    return _fs_instance

def get_ds():
    """Returns a valid DriveStation instance."""
    global _ds_instance
    if _ds_instance is None:
        print("Initializing DriveStation connection...")
        _ds_instance = DriveStation(IP, PORT, USER, PASS, secure=True, cert_verify=False, dsm_version=7, debug=False)
    return _ds_instance

async def upload_bytes_synology(byte_content, target_filename, dest_folder):
    """Uploads file using a thread to prevent blocking the async loop."""
    try:
        def sync_upload():
            with tempfile.TemporaryDirectory() as tmp_dir:
                local_path = os.path.join(tmp_dir, target_filename)
                with open(local_path, 'wb') as f:
                    f.write(byte_content)
                # Use the sync library inside this thread
                fs = get_fs()
                return fs.upload_file(dest_path=dest_folder, file_path=local_path, create_parents=True)

        # Run the blocking sync_upload in a separate thread
        result = await asyncio.to_thread(sync_upload)
        return True, result
    except Exception as e:
        print(f"Upload failed: {e}")
        return False, str(e)

async def upload_bytes_and_convert_synology(byte_content, target_filename, dest_folder):
    """The full workflow orchestrated without crashing the app."""
    # 1. Upload
    success, upload_res = await upload_bytes_synology(byte_content, target_filename, dest_folder)
    if not success:
        print("Stopping workflow: Upload failed.")
        return False

    ds = get_ds()
    # 2. Get Link (Retry logic)
    link = None
    for _ in range(10):
        await asyncio.sleep(1) # Give Synology a second to index the file
        link = await ds.get_link(f"{dest_folder}/{target_filename}")
        if link: break
    
    if not link:
        print("Stopping workflow: Could not generate sharing link.")
        return False

    # 3. Convert
    rst = await ds.convert_to_synology_office(f"link:{link}")

    return rst.get('success', False)

async def list_folder_synology(payload, folder_path: str):
    """dict_keys: 'access_time', 'adv_shared', 'app_properties', 'capabilities', 'change_id', 'change_time', 'content_snippet', 'content_type', 'created_time', 'disable_download', 'display_path', 'dsm_path', 'enable_watermark', 'encrypted', 'file_id', 'force_watermark_download', 'hash', 'image_metadata', 'in_disconnected_cold_tier', 'labels', 'max_id', 'modified_time', 'name', 'owner', 'parent_id', 'path', 'permanent_link', 'properties', 'removed', 'revisions', 'shared', 'shared_with', 'size', 'starred', 'support_remote', 'sync_id', 'sync_to_device', 'transient', 'type', 'version_id', 'watermark_version'"""
    ds = get_ds()
    try:
        rst = ds.list_folder(folder_path)
        return [{'permanent_link': file['permanent_link'], 'name': file['name'], 'path': file['display_path']} for file in rst['data']['items']]
    except Exception as e:
        print(f'Error in list_folder_synology: {e}')
    
    return None
