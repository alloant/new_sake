import os
import json
import tempfile
import httpx
import asyncio

from pathlib import PurePosixPath
from urllib.parse import urlparse

from synology_api import filestation

USER = os.getenv("SYNOLOGY_SERVICE_USER")
PASS = os.getenv("SYNOLOGY_SERVICE_PASSWD")
IP = os.getenv("SYNOLOGY_SERVER")
PORT = os.getenv("SYNOLOGY_PORT")

fs = filestation.FileStation(IP, PORT, USER, PASS, secure=True, cert_verify=False, dsm_version=7, debug=True, otp_code=None)

async def get_info(file_path: str):
    return fs.get_file_info(file_path)

# Custom exception for clarity (Optional but recommended)
class UploadError(Exception):
    pass

async def upload_bytes(byte_content, target_filename, dest_folder):
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_path = os.path.join(tmp_dir, target_filename)

            with open(local_path, 'wb') as f:
                f.write(byte_content)

            # Await the upload if it's an async function
            return fs.upload_file(dest_path=dest_folder, file_path=local_path, progress_bar=False, create_parents=True)
    except OSError as e:
        # We catch it here to add context, then raise it again
        print(f"File system error during upload setup: {e}")
        raise UploadError(f"Failed to prepare file for upload: {e}")
    except Exception as e:
        print(f"Unexpected error in upload_bytes: {e}")
        raise


#############################################################
### Mix methods #################################
#########################################################

async def upload_bytes_and_convert(byte_content, target_filename, dest_folder):
    try:
        # This will now catch errors from upload_bytes OR the logic below
        await upload_bytes(byte_content, target_filename, dest_folder)
        
        link = None
        attempts = 0
        while not link and attempts < 10: # Added a safety timeout
            await asyncio.sleep(0.5) # Use asyncio.sleep, NOT time.sleep
            link = await get_link(f"{dest_folder}/{target_filename}")
            attempts += 1
            
        if not link:
            raise TimeoutError("Link generation timed out.")

        rst = await convert_to_synology_office(f"link:{link}")
        return True if rst.get('success') else False

    except UploadError as e:
        print(f"Workflow stopped because upload failed: {e}")
    except Exception as e:
        print(f"Workflow failed at a later stage: {e}")

################################################################
## HERE DOWN THE DRIVE PART #################################################
######################################################

async def get_link(file_path: str):
    full_syno_path = f"/team-folders{file_path}" if not file_path.startswith("/team-folders") else file_path
    payload = {
        "api": "SYNO.SynologyDrive.Sharing",
        "method": "create_link",
        "version": "1",
        "path": full_syno_path
    }

    full_link = await connect(payload)
    if 'data' in full_link:
        path = urlparse(full_link['data']['url']).path
        return PurePosixPath(path).name
    return None

async def convert_to_synology_office(file_path: str):
    if file_path.startswith("link"):
        full_syno_path = file_path
    else:
        full_syno_path = f"/team-folders{file_path}" if not file_path.startswith("/team-folders") else file_path
    payload = {
        "api": "SYNO.SynologyDrive.Files",
        "method": "convert_office",
        "version": "6",
        "conflict_action": "autorename",
        "files": json.dumps([{"path": full_syno_path}])
    }

    return await connect(payload)

async def connect(payload: dict):
    async with httpx.AsyncClient(verify=False) as client:
        auth_url = f"https://{IP}:{PORT}/webapi/auth.cgi"
        auth_params = {
            "api": "SYNO.API.Auth", "method": "login", "version": "3",
            "account": USER, "passwd": PASS, "session": "Drive", "format": "sid"
        }
        
        auth_res = await client.get(auth_url, params=auth_params)
        sid = auth_res.json()["data"]["sid"]
        payload['_sid'] = sid

        entry_url = f"https://{IP}:{PORT}/webapi/entry.cgi"
        response = await client.post(entry_url, data=payload)
        data = response.json()
        return data
        if data.get("success"):
            targets = data.get("data", {}).get("targets", [{}])
            if targets[0].get("success"):
                return True, data
            else:
                return False, targets[0].get("error_code")
        return False, data.get("error")


