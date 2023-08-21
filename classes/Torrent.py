import os
import shutil
import rarfile
import datetime
import pytz
from classes.Series import Series

class Torrent:
    def __init__(self, torrent_data, client, config):
        self.hash = torrent_data['hash']
        self.name = torrent_data['name']
        self.client = client

        self.config = config
        self.seeder_ratio = self.config.seeder_ratio

        self.torrent_data = torrent_data

        # basic attributes that can be set with raw torrent data
        self.seeding_time = self.torrent_data['seeding_time']
        self.size = self.torrent_data['size']
        self.ratio = self.torrent_data['ratio']
        self.containing_dir = self.torrent_data['content_path']
        self.save_path = self.torrent_data['save_path']
        self.last_active = self.torrent_data['last_activity']

        # Get torrent tag data
        self.tags = None
        self.get_torrent_tags()

        # Check if torrent is complete and has been moved
        self.complete = False
        self.moved = False
        self.check_complete()

        # Attributes relating to private_tracker
        self.seeded = False
        self.tracker = None
        self.seed_for = 0
        self.check_private_tracker()

        self.seeder = False
        if self.complete:
            self.seeding_check()

        self.deletable = False

    def get_torrent_tags(self):
        if self.tags is None:
            self.tags = self.torrent_data['tags'].split(', ')
        else:
            self.get_torrent_data()
            self.tags = self.torrent_data['tags'].split(', ')

    def get_torrent_data(self):
        self.torrent_data = self.client.torrents_info(torrent_hashes=self.hash)[0]

    def check_complete(self):
        if self.torrent_data['amount_left'] == 0:
            self.complete = True
            if 'Moved' in self.tags:
                self.moved = True
                if 'Relocate' in self.tags:
                    self.remove_tag("Relocate")
            else:
                if 'Relocate' not in self.tags:
                    self.add_tag("Relocate")

    def check_private_tracker(self):
        private_trackers = self.config.private_trackers
        for tracker in private_trackers:
            if private_trackers[tracker]['torrent_tag'] in self.tags:
                self.tracker = tracker
                self.seed_for = private_trackers[tracker]['seeding_time']
                break
            elif private_trackers[tracker]['source_tag'] in self.name:
                self.tracker = tracker
                self.seed_for = private_trackers[tracker]['seeding_time']
                break
        if not self.tracker:
            self.seed_for = 0
            if 'PUBLIC' not in self.tags:
                self.add_tag("PUBLIC")

        if 'Seeded' in self.tags:
            self.seeded = True
        else:
            if self.seeding_time >= self.seed_for:
                self.seeded = True

    # Check seeding data against private trackers
    def seeding_check(self):
        if not self.tracker: # Raise an error as this function is only relevant to private tracker torrents
            raise Exception("Torrent is not from a private tracker")
        if not self.complete: # Raise an error as this function is only relevant to completed torrents
            raise Exception("Torrent is not complete")

        last_active_date = datetime.datetime.fromtimestamp(self.last_active, tz=pytz.timezone('Australia/Sydney'))
        current_time = datetime.datetime.now(tz=pytz.timezone('Australia/Sydney'))
        time_diff = (current_time - last_active_date).days
        if "Seeder" in self.tags: # If torrent is already marked as a seeder, check if it's still active
            if time_diff >= 7:
                self.remove_tag("Seeder")
                self.add_tag("Inactive")
            else:
                self.seeder = True
        else: # If torrent is not already marked as a seeder, check if should be.
            if self.ratio >= self.seeder_ratio and time_diff <= 7:
                if "Inactive" in self.tags:
                    self.remove_tag("Inactive")
                self.add_tag("Seeder")
                self.seeder = True
            else:
                self.add_tag("Inactive")

    # Mark the torrent with error, used for moving files
    def mark_error(self):
        self.client.torrents_add_tags(torrent_hashes=self.hash, tags="Error")

    # Add a tag to the torrent
    def add_tag(self, tag):
        self.client.torrents_add_tags(torrent_hashes=self.hash, tags=tag)
        self.get_torrent_tags()

    def remove_tag(self, tag):
        self.client.torrents_remove_tags(torrent_hashes=self.hash, tags=tag)
        self.get_torrent_tags()

    def delete(self):
        self.client.torrents_delete(torrent_hashes=self.hash, delete_files=True)