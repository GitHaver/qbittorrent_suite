import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)
from lib.lib import connect_to_qbittorrent, log_text, format_current_time
from classes.Torrents import Torrent
from classes.Config import Config

torrent_hash = sys.argv[1]
torrent_name = sys.argv[2]

depth = log_text(0, f"{format_current_time()}: Starting file manager...")
depth = log_text(depth, f"Torrent hash: {torrent_hash}", indent=False)
depth = log_text(depth, f"Torrent name: {torrent_name}", reset=True)

config = Config()
client = connect_to_qbittorrent(**config.connection_info)

depth = log_text(depth, "Reading torrent data...")

raw_torrent = client.torrents_info(hashes=torrent_hash)[0]
torrent = Torrent(raw_torrent, client, config)

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
