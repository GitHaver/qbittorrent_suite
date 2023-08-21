import os
import sys
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(parent_dir)
from lib.lib import connect_to_qbittorrent, log_text, format_current_time
from classes.Torrents import Torrents
from classes.Config import Config

def check_complete(f_torrent, f_depth):
    if not f_torrent.complete:
        log_text(f_depth-1, f"-SKIPPED: not complete.\n")
        return False
    else:
        return True

def check_moved(f_torrent, f_depth):
    if 'Moved' not in f_torrent.tags:
        log_text(f_depth-1, f"-SKIPPED: not moved.\n")
        return False
    else:
        return True

def set_deletable(f_torrent, f_depth):
    f_torrent.deletable = True
    log_text(f_depth-1, f"-CONTINUE: can be deleted.\n")

def check_seeded(f_torrent, f_depth):
    if not f_torrent.seeded:
        remaining_time = round(((torrent.seed_for - torrent.seeding_time) / 60 / 60), 2)
        log_text(f_depth - 1, f"-SKIPPED: seed for {remaining_time} more hours. \n")
        return False
    else:
        return True

def check_seeder(f_torrent, f_depth):
    torrent.seeding_check()
    if f_torrent.seeder:
        log_text(f_depth - 1, f"-SKIPPED: is a seeder and contributing to ratio. \n")
        return False
    else:
        return True


depth = log_text(0, f"\n{format_current_time()}: Starting seeding checker...")

config = Config()
qbit_client = connect_to_qbittorrent(**config.connection_info)

depth = log_text(depth, "Reading torrents...")
torrents = Torrents(qbit_client, config)

if not torrents.torrents_by_tracker:
    depth = log_text(depth, "No torrents found.")
    sys.exit()
else:
    torrents_in_dict = sum(len(value) for value in torrents.torrents_by_tracker.values())
    depth = log_text(depth, f"{torrents_in_dict} torrents found.\n")

initial_depth = depth - 2

seeder_ratio = config.seeder_ratio # Ratio at which we mark a private torrent as a seeder, to be kept for ratios.

private_trackers = config.private_trackers  # Dict of private trackers info such as ratio, bonus scheme


for tracker in torrents.torrents_by_tracker.keys():
    inner_depth = log_text(initial_depth, f"Checking {tracker} torrents...")
    for torrent in torrents.torrents_by_tracker[tracker]:
        depth = log_text(inner_depth, f"{torrent.name}")

        if not check_complete(torrent, depth):
            continue

        if not check_seeded(torrent, depth):
            continue

        if not check_moved(torrent, depth):
            continue

        if not check_seeder(torrent, depth):
            continue

        set_deletable(torrent, depth)


depth = 0
deletable_torrents = 0

torrents_to_delete = []

initial_depth = 1

depth = log_text(depth, f"Checking torrents by tracker...")
for tracker in torrents.torrents_by_tracker.keys():
    depth = log_text(initial_depth, f"Checking {tracker}...")
    tracker_torrents = torrents.torrents_by_tracker[tracker]
    torrents_to_seed = private_trackers[tracker]['max_torrents']

    log_text(depth, f"Min torrents for tracker: {torrents_to_seed}")

    log_text(depth, f"Current torrents for tracker: {len(tracker_torrents)}")

    tracker_deletable = [torrent for torrent in tracker_torrents if torrent.deletable]
    log_text(depth, f"Deletable torrents for tracker: {len(tracker_deletable)}")

    torrent_difference = len(tracker_torrents) - torrents_to_seed

    if torrent_difference <= 0:
        log_text(depth-1, f"Torrent count is within the limit for {tracker}.\n")
        continue

    if torrent_difference > len(tracker_deletable):
        num_deletable_torrents = len(tracker_deletable)
        log_text(depth-1, f"There are {num_deletable_torrents} deletable torrents for {tracker}.\n")
    else:
        log_text(depth-1, f"There are {torrent_difference} torrents to delete for {tracker}\n")
        num_deletable_torrents = torrent_difference

    if num_deletable_torrents > 0:
        tracker_torrents.sort(key=lambda x: x.size, reverse=True)
        for torrent in tracker_torrents:
            if torrent.deletable:
                if deletable_torrents < num_deletable_torrents:
                    torrents_to_delete.append(torrent)
                    deletable_torrents += 1
                else:
                    break
            else:
                continue

deleted_torrents = 0
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
if not deletable_torrents:
    log_text(0, "\nNo torrents deleted.")
else:
    total_size = round((total_size / 1024 / 1024 / 1024), 2)
    log_text(0, f"\n{deletable_torrents} torrents deleted. {total_size} GB freed.")
