import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)
from lib.lib import load_config, connect_to_qbittorrent, log_text, format_current_time
from lib.torrent import Torrent


depth = log_text(0, f"\n{format_current_time()}: Starting seeding checker...")

config = load_config()
conn_info = config['connection_info']
qbit_client = connect_to_qbittorrent(**conn_info)

completed_torrents = []

depth = log_text(depth, "Reading torrents...")
for torrent in qbit_client.torrents_info():
    if torrent['completion_on']:
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
total_size = 0
seeder_ratio = config['seeder_ratio']

deletable_torrents = []
all_torrents = []

for torrent in completed_torrents:
    torrent = Torrent(torrent['hash'], qbit_client)
    all_torrents.append(torrent)
    depth = log_text(initial_depth, f"{torrent.name} loaded...")

    # Check if the torrent belongs to a private tracker
    if torrent.private_tracker:
        depth = log_text(depth, f"-is a {torrent.private_tracker} torrent, checking seeding...")
        # Check if the torrent is a seeder and could help maintain a positive ratio
        if torrent.ratio_check():
            log_text(depth, f"-SEEDER: skipped.\n")
            continue
        else:
            log_text(depth, f"-is not a seeder...")

        # Check if the torrent has seeded for sufficient time based on tracker
        if not torrent.seeded:
            log_text(depth-1, f"-SKIPPED: has not seeded for sufficient time.\n")
            continue
        else:
            log_text(depth, f"-has seeded for sufficient time...")
    else:
        log_text(depth, f"-NOT A PRIVATE TRACKER TORRENT")

    depth -= 1
    # Check if the media files have been moved so we can see if we can delete them.
    if torrent.moved:
        deletable_torrents.append(torrent)
        log_text(depth, f"-CAN BE DELETED.\n")
        total_size += torrent.size
    else:
        log_text(depth, f"-NOT MOVED: marked as Seeded.\n")
        torrent.add_tag("Seeded")
        torrents_seeded += 1


private_trackers = load_config('private_trackers')

private_torrents = {}
depth = 0
deleted_torrents = 0
for torrent in deletable_torrents:
    torrent.deletable = True
    if torrent.private_tracker:
        if torrent.private_tracker in private_torrents:
            private_torrents[torrent.private_tracker].append(torrent)
        else:
            private_torrents[torrent.private_tracker] = [torrent]

for torrent in all_torrents:
    if torrent.private_tracker in private_torrents:
        if torrent not in private_torrents[torrent.private_tracker]:
            private_torrents[torrent.private_tracker].append(torrent)
    else:
        private_torrents[torrent.private_tracker] = [torrent]

depth = log_text(depth, f"Checking deletable torrents per tracker...")
for tracker in private_torrents.keys():
    depth = log_text(depth, f"Checking {tracker}...")
    log_text(depth, f"Min torrents for tracker: {private_trackers[tracker]['max_torrents']}")
    log_text(depth, f"Current torrents for tracker: {len(private_torrents[tracker])}")
    tracker_deletable = [torrent for torrent in private_torrents[tracker] if torrent.deletable]
    log_text(depth, f"Deletable torrents for tracker: {len(tracker_deletable)}")
    torrent_difference = len(private_torrents[tracker]) - private_trackers[tracker]['max_torrents']
    log_text(depth, f"Deletable torrents within limit: {torrent_difference}")
    if torrent_difference <= 0:
        log_text(depth, f"Torrent count is within the limit for {tracker}.")
        continue
    if torrent_difference > len(deletable_torrents):
        num_deletable_torrents = len(deletable_torrents)
        log_text(depth, f"There are only {num_deletable_torrents} deletable torrents to keep the count within {private_trackers[tracker]['max_torrents']}.")
    else:
        log_text(depth, f"There are {torrent_difference} torrents to delete within the limit of {private_trackers[tracker]['max_torrents']}.")
        num_deletable_torrents = torrent_difference
    if num_deletable_torrents > 0:
        depth = log_text(depth, f"Too many torrents for {tracker}, deleting least seeded torrents...")
        private_torrents[tracker].sort(key=lambda x: x.ratio)
        for torrent in private_torrents[tracker]:
            if torrent.deletable:
                if deleted_torrents < num_deletable_torrents:
                    torrent.delete()
                    deleted_torrents += 1
                    log_text(depth, f"Deleted {torrent.name}...")
                else:
                    break
            else:
                continue


# Wrap things up with a summary
if not deleted_torrents:
    log_text(0, "No torrents deleted.")
else:
    log_text(0, f"{deleted_torrents} torrents deleted. {total_size/1024/1024/1024} GB freed.")

if not torrents_seeded:
    log_text(0, "No torrents marked as seeded.")
else:
    log_text(0, f"{torrents_seeded} torrents marked as seeded.")
