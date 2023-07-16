from lib.lib import load_config, connect_to_qbittorrent, log_text, format_current_time, log_error
from lib.torrent import Torrent
import sys

torrent_hash = sys.argv[1]
torrent_name = sys.argv[2]

depth = log_text(0, f"{format_current_time()}: Starting file manager...")
depth = log_text(depth, f"Torrent hash: {torrent_hash}", indent=False)
depth = log_text(depth, f"Torrent name: {torrent_name}", reset=True)

config = load_config()
conn_info = config['connection_info']
qbit_client = connect_to_qbittorrent(**conn_info)

depth = log_text(depth, "Reading torrent data...")

torrent = Torrent(torrent_hash, qbit_client)

torrent.get_media_type()

if torrent.media_type == "Other" or torrent.media_type is None:
    depth = log_text(depth, "Media type not found, marking as error.")
    torrent.mark_error()
    sys.exit()


torrent.get_torrent_files()

if torrent.media_files == 0 and torrent.archives == 0:
    depth = log_text(depth, "No media files found, marking as error.")
    torrent.mark_error()
    sys.exit()


if torrent.media_files and torrent.archives:
    depth = log_text(depth, "Both media files and archives found, marking as error.")
    torrent.mark_error()
    sys.exit()

if torrent.media_files:
    torrent.type = "files"
elif torrent.archives:
    torrent.type = "archives"

torrent.move()
