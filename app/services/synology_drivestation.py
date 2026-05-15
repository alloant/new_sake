import json
from synology_api.base_api import BaseApi

class DriveStation(BaseApi):
    def __init__(self, ip_address, port, username, password, secure=False, cert_verify=False, dsm_version=7, debug=True, otp_code=None):
        super().__init__(ip_address, port, username, password, secure, cert_verify, dsm_version, debug, otp_code)
        self.app_api_list = self.gen_list 

    def _drive_request(self, api_name, method, **params):
        """Internal helper to execute API requests with common validation logic."""
        if api_name not in self.app_api_list:
            return {"success": False, "error": f"API {api_name} not found."}

        info = self.app_api_list[api_name]
        
        # Build the base parameters
        req_param = {
            'version': info.get('maxVersion', 1),
            'method': method
        }
        # Add the method-specific parameters (path, files, etc.)
        req_param.update(params)

        return self.request_data(api_name, info['path'], req_param)

    def list_folder(self, folder_path='/mydrive'):
        """List contents of a specific Drive folder"""
        return self._drive_request('SYNO.SynologyDrive.Files', 'list', path=folder_path)

    def get_link(self, folder_path: str):
        """Get permanent link Synology drive"""
        return self._drive_request('SYNO.SynologyDrive.Sharing', 'create_link', path=folder_path)

    def convert_to_synology_office(self, file_path: str):
        """Convert a file to Synology Office format"""
        # Specific logic for this method: handle path prefixing
        full_syno_path = file_path if file_path.startswith("link") else f"/team-folders{file_path}"
        
        return self._drive_request(
            'SYNO.SynologyDrive.Files', 
            'convert_office',
            conflict_action='autorename',
            files=json.dumps([{'path': full_syno_path}])
        )


