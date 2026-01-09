class UserSettings(object):
    def get_setting(self,setting):
        if setting in self.settings:
            return self.settings[setting]

        match setting:
            case 'limit_records':
                return 20
            case 'theme':
                return 'light'

