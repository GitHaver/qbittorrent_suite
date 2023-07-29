import os
import re
from lib.lib import log_text


class Series:
    class Episode:
        def __init__(self, file):
            self.full_path = file
            self.directory = os.path.dirname(file)
            self.filename = os.path.basename(file)

            self.series_name = None
            self.season_number = None
            self.episode_number = None
            self.episode_name = None
            self.parse_episode_name()

        def parse_episode_name(self):
            pattern = r"(.+?)[\.\s_-]+s?(\d+)[ex](\d+)[\.\s_-]+(.+)"
            match = re.search(pattern, self.filename, re.IGNORECASE)
            if match:
                self.series_name = match.group(1)
                self.season_number = match.group(2)
                self.episode_number = match.group(3)
                self.episode_name = match.group(4)
            pass

    def __init__(self, series_files, torrent):
        self.torrent = torrent
        self.series_name = None
        self.episodes = None
        self.seasons = None

        self.parse_episodes(series_files)

    def parse_episodes(self, files):
        for file in files:
            episode = self.Episode(file)
            self.episodes.append(episode)
        checked_name = None
        for episode in self.episodes:
            if checked_name is None:
                checked_name = episode.series_name
            else:
                if checked_name != episode.series_name:
                    log_text(0, f"Series name mismatch in {episode.filename}")
                    self.torrent.mark_error()
        self.series_name = checked_name
        for episode in self.episodes:
            cleaned_season_number = episode.season_number
            if cleaned_season_number.startswith("0"):
                cleaned_season_number = cleaned_season_number[1:]
            season_text = f"Season {cleaned_season_number}"
            if season_text in self.seasons:
                self.seasons[season_text].append(episode)
            else:
                self.seasons[season_text] = [episode]