from synology_api.base_api import BaseApi

class drivestation(BaseApi):
    def __init__(self, ip_address, port, username, password, secure=False, cert_verify=False, dsm_version=7, debug=True, otp_code=None):
        # 1. This call logs in and populates the API list automatically
        super().__init__(ip_address, port, username, password, secure, cert_verify, dsm_version, debug, otp_code)
        
        self.app_api_list = self.gen_list 
        # --- DEBUG LINE ---
        #print("AVAILABLE DRIVE APIS:", [k for k in self.app_api_list.keys() if 'Drive' in k])
        # ------------------

    def get_team_folder_info(self):
        """List all Team Folders in Drive"""
        api_name = 'SYNO.SynologyDrive.TeamFolder'
        
        if api_name not in self.app_api_list:
             return f"API {api_name} not found. Check if Synology Drive is installed."
             
        info = self.app_api_list[api_name]
        api_path = info['path']
        
        # Use .get() for version to avoid errors if it's missing
        req_param = {'version': info.get('maxVersion', 1), 'method': 'list'}
        return self.request_data(api_name, api_path, req_param)

    def list_folder(self, folder_path='/mydrive'):
        """List contents of a specific Drive folder"""
        api_name = 'SYNO.SynologyDrive.Files'
        
        if api_name not in self.app_api_list:
             return f"API {api_name} not found."

        info = self.app_api_list[api_name]
        api_path = info['path']
        
        req_param = {
            'version': info.get('maxVersion', 1), 
            'method': 'list', 
            'path': folder_path
        }
        
        return self.request_data(api_name, api_path, req_param)

    def get_link(self, folder_path: str):
        """Get permanent link Synology drive"""
        api_name = 'SYNO.SynologyDrive.Sharing'
        
        if api_name not in self.app_api_list:
             return f"API {api_name} not found."

        info = self.app_api_list[api_name]
        api_path = info['path']
        
        req_param = {
            'version': info.get('maxVersion', 1), 
            'method': 'create_link', 
            'path': folder_path
        }
        
        return self.request_data(api_name, api_path, req_param)

    def convert_to_synology_office(file_path: str):
        """Get permanent link Synology drive"""
        api_name = 'SYNO.SynologyDrive.Files'
        
        if api_name not in self.app_api_list:
             return f"API {api_name} not found."

        info = self.app_api_list[api_name]
        api_path = info['path']
        
        full_syno_path = file_path if file_path.startswith("link") else f"/team-folders{file_path}"
        req_param = {
            'version': info.get('maxVersion', 1), 
            'method': 'convert_office',
            'conflict_action': 'autorename',
            'files': json.dumps([{'path': full_syno_path}])
        }
        
        return self.request_data(api_name, api_path, req_param)



