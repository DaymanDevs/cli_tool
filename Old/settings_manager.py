import json
import os

class SettingsManager:
    def __init__(self, filename='bot_settings.json', options_filename='settings_options.json'):
        self.filename = filename
        self.options_filename = options_filename
        self.data = self.load_settings()
        self.options = self.load_options()

    def load_settings(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                return json.load(file)
        return {}

    def save_settings(self):
        with open(self.filename, 'w') as file:
            json.dump(self.data, file, indent=4)

    def load_options(self):
        if os.path.exists(self.options_filename):
            with open(self.options_filename, 'r') as file:
                return json.load(file)
        return []

    def save_options(self):
        with open(self.options_filename, 'w') as file:
            json.dump(self.options, file, indent=4)

    def get_settings(self, profile_name):
        return self.data.get(profile_name, {})

    def update_settings(self, profile_name, new_settings):
        """Update settings for a specific profile."""
        if profile_name in self.data:
            self.data[profile_name].update(new_settings)
            self.save_settings()

    def delete_profile(self, profile_name):
        if profile_name in self.data:
            del self.data[profile_name]
            self.save_settings()

    def rename_profile(self, old_name, new_name):
        """Renames a wallet profile."""
        if old_name in self.data:
            self.data[new_name] = self.data.pop(old_name)
            self.save_settings()

    def list_profiles(self):
        return list(self.data.keys())

    def get_options(self):
        return self.options

    def add_setting_option(self, option_name, default_value=None):
        if option_name not in self.options:
            self.options.append(option_name)
            self.save_options()
            for profile in self.data.values():
                profile[option_name] = default_value
            self.save_settings()

    def remove_setting_option(self, option_name):
        if option_name in self.options:
            self.options.remove(option_name)
            self.save_options()
            for profile in self.data.values():
                if option_name in profile:
                    del profile[option_name]
            self.save_settings()

settings_manager = SettingsManager()
