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

depth = log_text(depth, "Reading torrents...")
torrents = qbit_client.torrents_info()

if len(torrents) == 0:
    depth = log_text(depth, "No torrents found.")
    sys.exit()
else:
    depth = log_text(depth, f"{len(torrents)} torrents found.\n")

initial_depth = depth

seeder_ratio = config['seeder_ratio']  # Ratio at which we mark a private torrent as a seeder, to be kept for ratios.

private_trackers = load_config('private_trackers')  # Dict of private trackers info such as ratio, bonus scheme
private_torrents = {}  # Dict of private tracker torrents.
non_private_torrents = []  # List of non-private tracker torrents that can be deleted.

for torrent in torrents:
    torrent = Torrent(torrent['hash'], qbit_client)
    depth = log_text(initial_depth, f"{torrent.name}")

    if not torrent.complete:
        log_text(depth, f"-SKIPPED: not complete.\n")
        continue
    # Handle private_tracker torrents
    if torrent.private_tracker:
        depth = log_text(depth, f"-is a {torrent.private_tracker} torrent...")
        # Add torrents to the relevant private_tracker key in private tracker dict.
        if torrent.private_tracker not in private_torrents:
            private_torrents[torrent.private_tracker] = [torrent]
        else:
            private_torrents[torrent.private_tracker].append(torrent)
        # Check if the torrent is a seeder and could help maintain a positive ratio
        if torrent.ratio_check():
            log_text(depth-1, f"-SEEDER: skipped.\n")
            continue
        else:
            log_text(depth, f"-is not a seeder...")

        # Check if the torrent has seeded for sufficient time based on tracker
        if not torrent.seeded:
            log_text(depth-1, f"-SKIPPED: seed for {(torrent.seed_for - torrent.seeding_time)/60/60} more hours. \n")
            continue
        else:
            log_text(depth, f"-has seeded for sufficient time...")
    else:
        log_text(depth, f"-NOT A PRIVATE TRACKER TORRENT")
        non_private_torrents.append(torrent)

    depth -= 1
    # Check if the media files have been moved and so can be deleted. Otherwise, mark for relocation.
    if torrent.moved:
        torrent.deletable = True
        log_text(depth, f"-CAN BE DELETED.\n")
    else:
        torrent.add_tag("Relocate")
        log_text(depth, f"-NOT YET MOVED.\n")


depth = 0
deleted_torrents = 0

torrents_to_delete = []

# Delete any deletable non-private tracker torrents
if non_private_torrents:
    for torrent in non_private_torrents:
        if torrent.deletable:
            torrents_to_delete.append(torrent)

# Work through private tracker torrents
depth = 0
depth = log_text(depth, f"Checking private tracker torrents...")
for tracker in private_torrents.keys():
    depth = log_text(depth, f"Checking {tracker}...")

    torrents_to_seed = private_trackers[tracker]['max_torrents']
    log_text(depth, f"Min torrents for tracker: {torrents_to_seed}")

    log_text(depth, f"Current torrents for tracker: {len(private_torrents[tracker])}")

    tracker_deletable = [torrent for torrent in private_torrents[tracker] if torrent.deletable]
    log_text(depth, f"Deletable torrents for tracker: {len(tracker_deletable)}")

    torrent_difference = len(private_torrents[tracker]) - torrents_to_seed
    log_text(depth, f"Deletable torrents within limit: {torrent_difference}")

    if torrent_difference <= 0:
        log_text(depth-1, f"Torrent count is within the limit for {tracker}.")
        continue

    if torrent_difference > len(tracker_deletable):
        num_deletable_torrents = len(tracker_deletable)
        log_text(depth-1, f"There are {num_deletable_torrents} deletable torrents within {torrents_to_seed}.")
    else:
        log_text(depth-1, f"There are {torrent_difference} torrents to delete within the limit of {torrents_to_seed}.")
        num_deletable_torrents = torrent_difference

    if num_deletable_torrents > 0:
        depth = log_text(depth, f"Too many torrents for {tracker}, deleting least seeded torrents...")
        private_torrents[tracker].sort(key=lambda x: x.ratio)
        for torrent in private_torrents[tracker]:
            if torrent.deletable:
                if deleted_torrents < num_deletable_torrents:
                    torrents_to_delete.append(torrent)
                else:
                    break
            else:
                continue

# Delete the torrents
total_size = 0
if torrents_to_delete:
    depth = log_text(0, f"Deleting {len(torrents_to_delete)} torrents...")
    for torrent in torrents_to_delete:
        torrent.delete()
        log_text(depth, f"DELETED: {torrent.name}")
        deleted_torrents += 1
        total_size += torrent.size


# Wrap things up with a summary
if not deleted_torrents:
    log_text(0, "No torrents deleted.")
else:
    log_text(0, f"{deleted_torrents} torrents deleted. {total_size/1024/1024/1024} GB freed.")
