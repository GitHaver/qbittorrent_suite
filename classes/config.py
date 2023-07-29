import os
import yaml
import sys


class Config:
    connection_info = {}

    def __init__(self):
        current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        config_path = os.path.join(current_dir, "../config.yaml")
        with open(config_path) as f:
            self.raw_config = yaml.safe_load(f)
        self.format_connection_info()

        self.private_trackers = {}
        self.seeder_ratio = None
        for d_key, d_value in self.raw_config.items():
            setattr(self, d_key, d_value)

    def format_connection_info(self):
        if self.raw_config['self_signed_ssl']:
            self.raw_config['connection_info']['VERIFY_WEBUI_CERTIFICATE'] = False
        del self.raw_config['self_signed_ssl']

        host = self.raw_config['connection_info']['ip']
        port = self.raw_config['connection_info']['port']
        self.raw_config['connection_info']['host'] = f"{host}:{port}"

        del self.raw_config['connection_info']['ip']
        del self.raw_config['connection_info']['port']


if __name__ == '__main__':
    config = Config()
    for key, value in config.raw_config.items():
        print(key, value)
