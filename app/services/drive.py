from .synology import upload_bytes_and_convert as upload_bytes_and_convert_synology
from .google import GoogleDriveService


async def upload_bytes_and_convert(payload, byte_content, target_filename, dest_folder):
    if payload.provider == 'synology':
        await upload_bytes_and_convert_synology(byte_content, target_filename, dest_folder)
    elif payload.provider == 'google':
        drive = GoogleDriveService(
            access_token=payload.google_access_token,
            refresh_token=payload.google_refresh_token
        )

        rst = await drive.upload_file(target_filename, byte_content, 'Sake', convert=True)



