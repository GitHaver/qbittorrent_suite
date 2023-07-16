from lib.lib import load_config, connect_to_qbittorrent, log_text, format_current_time
from lib.torrent import Torrent
import sys


depth = log_text(0, f"{format_current_time()}: Starting seeding checker...")

config = load_config()
conn_info = config['connection_info']
qbit_client = connect_to_qbittorrent(**conn_info)

completed_torrents = []

depth = log_text(depth, "Reading torrents...")
for torrent in qbit_client.torrents_info():
    if "Seeded" not in torrent['tags'] and torrent['completion_on']:
        completed_torrents.append(torrent)
    else:
        continue

if not completed_torrents:
    depth = log_text(depth, "No completed torrents.")
    sys.exit()
else:
    depth = log_text(depth, f"{len(completed_torrents)} completed torrents found.\n")

initial_depth = depth
torrents_seeded = 0
torrents_deleted = 0
total_size = 0
seeder_ratio = config['seeder_ratio']


for torrent in completed_torrents:
    torrent = Torrent(torrent['hash'], qbit_client)
    depth = log_text(initial_depth, f"{torrent.name} loaded...")

    # Check if the torrent has a ratio of 0.01 or greater, if so, skip it.
    if torrent.ratio_check():
        log_text(depth, f"...is marked as Seeder, so was skipped.\n")
        continue

    # Check if the torrent has seeded for sufficient time based on tracker
    if not torrent.seeded:
        log_text(depth, f"...has not seeded for sufficient time, so was skipped.\n")
        continue

    # delete torrent if moved
    if torrent.moved:
        log_text(depth, f"...has been moved so was deleted.\n")
        torrent.delete()
        torrents_deleted += 1
        total_size += torrent.size
    else:
        log_text(depth, f"... has not been moved yet so was marked as Seeded.\n")
        torrent.add_tag("Seeded")
        torrents_seeded += 1


if not torrents_deleted:
    log_text(0, "No torrents deleted.")
else:
    log_text(0, f"{torrents_deleted} torrents deleted. {total_size/1024/1024/1024} GB freed.")

if not torrents_seeded:
    log_text(0, "No torrents marked as seeded.")
else:
    log_text(0, f"{torrents_seeded} torrents marked as seeded.")
