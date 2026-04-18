import os
import json
import tempfile
import httpx
import asyncio
from pathlib import PurePosixPath
from urllib.parse import urlparse
from synology_api import filestation

# Configuration
USER = os.getenv("SYNOLOGY_SERVICE_USER")
PASS = os.getenv("SYNOLOGY_SERVICE_PASSWD")
IP = os.getenv("SYNOLOGY_SERVER")
PORT = os.getenv("SYNOLOGY_PORT")

# Global Session Cache
_SESSION_SID = None

# Initialize FileStation (Synchronous)
try:
    fs = filestation.FileStation(IP, PORT, USER, PASS, secure=True, cert_verify=False, dsm_version=7, debug=False)
except:
    print('ERROR in FileStation')
    fs = None

async def get_sid():
    """Retrieves and caches the SID to avoid repeated logins."""
    global _SESSION_SID
    if _SESSION_SID:
        return _SESSION_SID
    
    async with httpx.AsyncClient(verify=False) as client:
        auth_url = f"https://{IP}:{PORT}/webapi/auth.cgi"
        params = {
            "api": "SYNO.API.Auth", "method": "login", "version": "3",
            "account": USER, "passwd": PASS, "session": "Drive", "format": "sid"
        }
        res = await client.get(auth_url, params=params)
        data = res.json()
        if data.get("success"):
            _SESSION_SID = data["data"]["sid"]
            return _SESSION_SID
        raise Exception(f"Login failed: {data.get('error')}")

async def upload_bytes(byte_content, target_filename, dest_folder):
    """Uploads file using a thread to prevent blocking the async loop."""
    try:
        def sync_upload():
            with tempfile.TemporaryDirectory() as tmp_dir:
                local_path = os.path.join(tmp_dir, target_filename)
                with open(local_path, 'wb') as f:
                    f.write(byte_content)
                # Use the sync library inside this thread
                return fs.upload_file(dest_path=dest_folder, file_path=local_path, create_parents=True)

        # Run the blocking sync_upload in a separate thread
        result = await asyncio.to_thread(sync_upload)
        return True, result
    except Exception as e:
        print(f"Upload failed: {e}")
        return False, str(e)

async def connect(payload: dict):
    """General Drive API connector using cached SID."""
    try:
        sid = await get_sid()
        payload['_sid'] = sid
        
        async with httpx.AsyncClient(verify=False) as client:
            entry_url = f"https://{IP}:{PORT}/webapi/entry.cgi"
            response = await client.post(entry_url, data=payload)
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

async def upload_bytes_and_convert(byte_content, target_filename, dest_folder):
    """The full workflow orchestrated without crashing the app."""
    # 1. Upload
    success, upload_res = await upload_bytes(byte_content, target_filename, dest_folder)
    if not success:
        print("Stopping workflow: Upload failed.")
        return False

    # 2. Get Link (Retry logic)
    link = None
    for _ in range(10):
        await asyncio.sleep(1) # Give Synology a second to index the file
        link = await get_link(f"{dest_folder}/{target_filename}")
        if link: break
    
    if not link:
        print("Stopping workflow: Could not generate sharing link.")
        return False

    # 3. Convert
    rst = await convert_to_synology_office(f"link:{link}")
    return rst.get('success', False)

async def get_link(file_path: str):
    full_syno_path = f"/team-folders{file_path}" if not file_path.startswith("/team-folders") else file_path
    payload = {
        "api": "SYNO.SynologyDrive.Sharing",
        "method": "create_link",
        "version": "1",
        "path": full_syno_path
    }
    res = await connect(payload)
    if res.get('success'):
        path = urlparse(res['data']['url']).path
        return PurePosixPath(path).name
    return None

async def convert_to_synology_office(file_path: str):
    full_syno_path = file_path if file_path.startswith("link") else f"/team-folders{file_path}"
    payload = {
        "api": "SYNO.SynologyDrive.Files",
        "method": "convert_office",
        "version": "6",
        "conflict_action": "autorename",
        "files": json.dumps([{"path": full_syno_path}])
    }
    return await connect(payload)
