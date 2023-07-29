import qbittorrentapi
import sys
import datetime

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



