import os
import io
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

class GoogleDriveService:
    def __init__(self, access_token: str, refresh_token: str = None):
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
        )
        self.service = build('drive', 'v3', credentials=creds)
    
    async def get_or_create_folder(self, folder_name: str, parent_id: str = 'root'):
        """Finds a folder by name or creates it if it doesn't exist."""
        query = (f"name = '{folder_name}' and "
                 f"'{parent_id}' in parents and "
                 f"mimeType = 'application/vnd.google-apps.folder' and "
                 f"trashed = false")
        
        results = self.service.files().list(q=query, fields="files(id)").execute()
        folders = results.get('files', [])

        if folders:
            return folders[0]['id']
        
        # Create it if not found
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        folder = self.service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')
    
    async def upload_file(self, file_name: str, file_content: bytes, folder_name: str, convert: bool = True):
        """
        Uploads a file and optionally converts it to Google Office formats.
        """
        target_folder_id = await self.get_or_create_folder(folder_name)
        
        # Map common extensions to Google MimeTypes
        ext = file_name.split('.')[-1].lower()
        
        # Default metadata
        file_metadata = {
            'name': file_name,
            'parents': [target_folder_id]  # This targets your specific folder
            }
        
        if convert:
            if ext in ['csv', 'xlsx', 'xls']:
                file_metadata['mimeType'] = 'application/vnd.google-apps.spreadsheet'
            elif ext in ['doc', 'docx', 'txt', 'sql']:
                file_metadata['mimeType'] = 'application/vnd.google-apps.document'
            # Note: SQL files converted this way become Google Docs (text)

        # Prepare the media content
        media = MediaIoBaseUpload(
            io.BytesIO(file_content), 
            mimetype='application/octet-stream', 
            resumable=True
        )

        # Execute upload
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()

        return file

    async def list_my_files(self):
        # 'q' parameter can filter files. If empty, it returns all files allowed by scope.
        results = self.service.files().list(
            pageSize=10, 
            fields="nextPageToken, files(id, name, mimeType)",
            # Optional: uncomment to see files in the trash too
            # includeItemsFromTrashed=True 
        ).execute()
        
        files = results.get('files', [])
        print(f"DEBUG: Found {len(files)} files") # Check your console
        return files
