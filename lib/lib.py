import yaml
import qbittorrentapi
import sys
import datetime
import os


def load_config(return_specific=None):
    def format_conn_info():
        if config['self_signed_ssl']:
            config['connection_info']['VERIFY_WEBUI_CERTIFICATE'] = False
        del config['self_signed_ssl']

        if config['server']:
            config['connection_info']['host'] = f"localhost:{config['connection_info']['port']}"
        else:
            config['connection_info']['host'] = f"{config['connection_info']['ip']}:{config['connection_info']['port']}"

        del config['server']
        del config['connection_info']['ip']
        del config['connection_info']['port']
    current_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    config_path = os.path.join(current_dir, "../config.yaml")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        log_error(0, "Unable to find config file, exiting...")

    if not return_specific or return_specific == "connection_info":
        format_conn_info()

    if return_specific:
        try:
            return config[return_specific]
        except KeyError:
            log_error(0, f"Unable to find {return_specific} in config...")
    else:
        return config


def connect_to_qbittorrent(**kwargs):
    depth = log_text(1, "Connecting to qBittorrent...")
    try:
        login = qbittorrentapi.Client(**kwargs)
        depth = log_text(depth, "Connected.")
        return login
    except qbittorrentapi.exceptions.HTTP404Error:
        log_error(depth, "Unable to connect to qBittorrent, exiting...")


def format_current_time():
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time


def log_text(depth, text, indent=True, reset=False):
    if depth == 0:
        prepend = "\n"
    else:
        prepend = "\t" * depth
    print(f"{prepend}{text}")
    if indent:
        return depth + 1
    elif reset:
        return 0


def log_error(depth, error):
    if depth == 0:
        prepend = "\n"
    else:
        prepend = "\t" * depth
    print(f"{prepend}{format_current_time()}")
    print(f"{prepend}ERROR: {error}")
    sys.exit()



