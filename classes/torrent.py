import os
import shutil
import rarfile
import datetime
import pytz
from classes.series import Series

class Torrent:
    def __init__(self, t_hash, qbit_client, config):
        self.hash = t_hash
        self.name = None
        self.qbit_client = qbit_client

        self.config = config
        self.seeder_ratio = self.config.seeder_ratio

        self.torrent_data = None
        # basic attributes set in set_torrent_data
        self.seeding_time = None
        self.size = None
        self.ratio = None
        self.containing_dir = None
        self.tags = None
        self.moved = False
        self.complete = False
        self.last_active = None

        # attributes used for moving torrents
        self.media_type = None  # Movie, TV, Anime, Music or Other
        self.media_location = None  # location to move media files to
        self.type = None  # files or archives

        self.files = None
        self.media_files = None
        self.archives = None

        # attributes used for checking seeding
        self.seeded = False
        self.seeder = False
        self.private_tracker = None
        self.seed_for = 0

        self.deletable = False

        # set the basic attributes
        self.set_torrent_data()

    # Only refreshes the torrent data that is needed as a baseline.
    def set_torrent_data(self):
        self.torrent_data = self.qbit_client.torrents_info(torrent_hashes=self.hash)[0]

        if self.name is None:
            self.name = self.torrent_data['name']

        self.containing_dir = self.torrent_data['content_path']
        self.seeding_time = self.torrent_data['seeding_time']
        self.size = self.torrent_data['total_size']
        self.last_active = self.torrent_data['last_activity']
        self.get_torrent_tags()
        self.ratio = self.torrent_data['ratio']
        if self.torrent_data['amount_left'] == 0:
            self.complete = True
            if 'Moved' in self.tags:
                self.moved = True
                if 'Relocate' in self.tags:
                    self.remove_tag("Relocate")
            else:
                if 'Relocate' not in self.tags:
                    self.add_tag("Relocate")
        self.check_private_tracker()
        if 'Seeded' in self.tags:
            self.seeded = True
        else:
            if self.seeding_time >= self.seed_for:
                self.seeded = True

    # Check seeding data against private trackers
    def seeding_check(self):
        if not self.private_tracker: # Raise an error as this function is only relevant to private tracker torrents
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

    # Lookup the torrent files in the torrent, and get the media files
    def get_torrent_files(self):
        self.files = [os.path.join(root, file) for root, dirs, files in os.walk(self.containing_dir) for file in files]

        self.media_files = [file for file in self.files
                            if file.endswith(('.mkv', '.mp4', '.avi', '.mp3', '.flac'))
                            and "sample" not in file.lower()]
        self.archives = [file for file in self.files
                         if file.endswith(('.rar', '.zip'))
                         and "sample" not in file.lower()]

    # Get the media type and save location from config
    def get_media_type(self):
        media_types = self.config.media_types
        t_type = None
        s_location = None
        for media_type in media_types:
            if media_type['tag'] in self.tags:
                t_type = media_type['tag']
                s_location = media_type['folder']
                break
        if s_location == "N/A":
            self.add_tag("Manual")
        if t_type is None:
            self.mark_error()

        self.media_type = t_type
        self.media_location = s_location

    # Mark the torrent with error, used for moving files
    def mark_error(self):
        self.qbit_client.torrents_add_tags(torrent_hashes=self.hash, tags="Error")

    # Add a tag to the torrent
    def add_tag(self, tag):
        self.qbit_client.torrents_add_tags(torrent_hashes=self.hash, tags=tag)
        self.get_torrent_tags()

    def remove_tag(self, tag):
        self.qbit_client.torrents_remove_tags(torrent_hashes=self.hash, tags=tag)
        self.get_torrent_tags()

    # Get the torrent tags
    def get_torrent_tags(self):
        torrent_info = self.qbit_client.torrents_info(torrent_hashes=self.hash)[0]
        tags = torrent_info['tags']
        tags = tags.split(', ')
        self.tags = tags

    # Check if the torrent is from a private tracker and load the seeding time from config
    def check_private_tracker(self):
        private_trackers = self.config.private_trackers
        for tracker in private_trackers:
            if private_trackers[tracker]['torrent_tag'] in self.tags:
                self.seed_for = private_trackers[tracker]['seeding_time']
                self.private_tracker = tracker

    def delete(self):
        self.qbit_client.torrents_delete(torrent_hashes=self.hash, delete_files=True)

    def move(self):
        def move_series():
            delete = False
            files = None
            if self.type == "files":
                files = self.media_files
            elif self.type == "archives":
                files = self.archives
            if self.private_tracker is not None and self.seeded:
                pass
            else:
                delete = True

            series = Series(files)
            for season in series.seasons:
                season_path = os.path.join(self.media_location, series.series_name, season)
                for file in season:
                    if self.type == "files":
                        if delete:
                            shutil.move(file, season_path)
                        else:
                            shutil.copy(file, season_path)
                    elif self.type == "archives":
                        rar = rarfile.RarFile(file)
                        rar.extractall(season_path)

            self.add_tag("Moved")
            if delete:
                self.delete()

        def move_movie():
            delete = False
            if self.private_tracker is not None and self.seeded:
                pass
            else:
                delete = True
            if self.type == "files":
                if delete:
                    for file in self.media_files:
                        shutil.move(file, self.media_location)
                else:
                    for file in self.media_files:
                        shutil.copy(file, self.media_location)
            elif self.type == "archives":
                for archive in self.archives:
                    rar = rarfile.RarFile(archive)
                    rar.extractall(self.media_location)

            self.add_tag("Moved")
            if delete:
                self.delete()

        def move_music():
            pass

        if self.media_type == "TV" or self.media_type == "Anime":
            move_series()
        elif self.media_type == "Movie":
            move_movie()
        elif self.media_type == "Music":
            move_music()
        else:
            pass